from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth import get_user_model
from django.db.models import Q, Sum, F
from django.db.models.functions import Greatest
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from datetime import timedelta
import hashlib
import random
import uuid

from content.models import Content
from content.serializers import ContentCardSerializer
from content.post_list_helpers import build_post_card_context
from portfolios.models import Portfolio
from portfolios.serializers import PortfolioListSerializer

from .models import (
    User, UserInvestProfile, UserFollow, UserModerationLog,
    UserSocialAccount, UserVerificationCode, UserRealNameVerification,
    UserProfessionalVerification, RiskQuestionnaireTemplate, RiskQuestionnaireSubmission,
    UserPrivacySettings, UserStarFollow, FollowFeedItem, UserBehaviorDaily, UserPointLog
)
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    PasswordLoginSerializer,
    EmailRegisterSerializer,
    PhoneRegisterSerializer,
    VerificationSendSerializer,
    VerificationConfirmSerializer,
    SmsLoginSerializer,
    UserProfileSerializer,
    UserInvestProfileSerializer,
    UserPublicSerializer,
    UserFollowSerializer,
    UserKycStatusSerializer,
    RealNameSubmitSerializer,
    ProfessionalSubmitSerializer,
    RiskQuestionnaireSubmitSerializer,
    UserPrivacySettingsSerializer,
)
from notifications.community_tasks import publish_follow_created_task, safe_task_delay
from .feed_service import write_follow_feed_for_actor
from .user_score_service import apply_points
from .oauth.wechat_client import WeChatOAuthClient
from .oauth.weibo_client import WeiboOAuthClient
from .message_service import send_email_verification_code, send_sms_verification_code
from invest_backend.api_response import ok, fail

User = get_user_model()


def get_tokens_for_user(user):
    """为用户生成JWT token"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def _auth_user_payload(user):
    return {
        'id': user.id,
        'username': user.username,
        'displayName': user.display_name,
        'role': user.role,
        'phoneVerified': user.phone_verified,
        'emailVerified': user.email_verified,
        'identityLevel': user.identity_level,
        'realNameStatus': user.real_name_status,
        'professionalStatus': user.professional_status,
        'riskAssessmentStatus': user.risk_assessment_status,
        'riskLevel': user.risk_level,
        'vBadge': user.v_badge,
    }


def _mask_id_card(id_card_no: str) -> str:
    text = id_card_no.strip()
    if len(text) <= 8:
        return '*' * len(text)
    return f"{text[:4]}{'*' * (len(text) - 8)}{text[-4:]}"


def _hash_id_card(id_card_no: str) -> str:
    return hashlib.sha256(id_card_no.strip().encode('utf-8')).hexdigest()


def _calc_risk_level(score: int) -> str:
    if score <= 20:
        return 'R1'
    if score <= 40:
        return 'R2'
    if score <= 60:
        return 'R3'
    if score <= 80:
        return 'R4'
    return 'R5'


def _ensure_social_provider(provider: str) -> str:
    p = (provider or '').upper()
    if p not in ['WECHAT', 'WEIBO']:
        raise ValueError('不支持的OAuth提供方')
    return p


def _create_or_bind_social_user(provider: str, social_info: dict, token_data: dict):
    provider_uid = str(social_info.get('unionid') or social_info.get('openid') or social_info.get('id') or token_data.get('uid') or '')
    if not provider_uid:
        raise ValueError('无法识别第三方账号ID')

    social = UserSocialAccount.objects.filter(provider=provider, provider_uid=provider_uid).select_related('user').first()
    if social:
        user = social.user
    else:
        base_name = social_info.get('nickname') or social_info.get('screen_name') or f'{provider.lower()}_user'
        username = base_name
        suffix = 1
        while User.objects.filter(username=username).exists():
            suffix += 1
            username = f"{base_name}_{suffix}"

        email = social_info.get('email') or f'{provider.lower()}_{provider_uid[:12]}@oauth.local'
        if User.objects.filter(email=email).exists():
            email = f'{provider.lower()}_{uuid.uuid4().hex[:12]}@oauth.local'

        user = User.objects.create_user(
            username=username,
            email=email,
            password=uuid.uuid4().hex,
            display_name=social_info.get('nickname') or social_info.get('screen_name') or username
        )
        social = UserSocialAccount(user=user, provider=provider, provider_uid=provider_uid)

    social.unionid = social_info.get('unionid') or social.unionid
    social.openid = social_info.get('openid') or social.openid
    social.access_token = token_data.get('access_token', '') or social.access_token
    social.refresh_token = token_data.get('refresh_token', '') or social.refresh_token
    expires_in = token_data.get('expires_in')
    if expires_in:
        try:
            social.expires_at = timezone.now() + timedelta(seconds=int(expires_in))
        except (ValueError, TypeError):
            pass
    social.save()
    return user, social


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """用户注册"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        return Response({
            'code': 0,
            'data': {
                'id': user.id,
                'username': user.username,
                'displayName': user.display_name,
                'role': user.role,
                'phoneVerified': user.phone_verified,
                'emailVerified': user.email_verified,
                'identityLevel': user.identity_level,
                **tokens
            }
        }, status=status.HTTP_201_CREATED)
    return Response({
        'code': 4001,
        'message': '注册失败',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """用户登录"""
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']

        # 封禁用户禁止登录
        if user.status == 'BANNED' or not user.is_active:
            return fail(4030, '账户已被封禁，无法登录', status.HTTP_403_FORBIDDEN)
        tokens = get_tokens_for_user(user)
        return ok({
            'access': tokens['access'],
            'refresh': tokens['refresh'],
            'user': _auth_user_payload(user)
        })
    return fail(4001, '登录失败', status.HTTP_400_BAD_REQUEST, serializer.errors)


@api_view(['POST'])
@permission_classes([AllowAny])
def token_refresh(request):
    serializer = TokenRefreshSerializer(data=request.data)
    if serializer.is_valid():
        return Response({'code': 0, 'data': serializer.validated_data})
    return Response({
        'code': 4001,
        'message': '刷新令牌失败',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_email(request):
    serializer = EmailRegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'code': 4001, 'message': '注册失败', 'errors': serializer.errors}, status=400)

    confirm = VerificationConfirmSerializer(data={
        'channel': 'EMAIL',
        'target': serializer.validated_data['email'],
        'purpose': 'REGISTER',
        'code': serializer.validated_data['email_code'],
    })
    if not confirm.is_valid():
        return Response({'code': 4001, 'message': '邮箱验证码校验失败', 'errors': confirm.errors}, status=400)

    with transaction.atomic():
        data = serializer.validated_data
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            display_name=data['username'],
            email_verified=True,
            phone_verified=False,
            identity_level='BASIC',
        )
        rec = confirm.validated_data['record']
        rec.status = 'VERIFIED'
        rec.verified_at = timezone.now()
        rec.user = user
        rec.save(update_fields=['status', 'verified_at', 'user'])
    tokens = get_tokens_for_user(user)
    return Response({
        'code': 0,
        'data': {'access': tokens['access'], 'refresh': tokens['refresh'], 'user': _auth_user_payload(user)}
    }, status=201)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_phone(request):
    serializer = PhoneRegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'code': 4001, 'message': '注册失败', 'errors': serializer.errors}, status=400)
    confirm = VerificationConfirmSerializer(data={
        'channel': 'PHONE',
        'target': serializer.validated_data['phone'],
        'purpose': 'REGISTER',
        'code': serializer.validated_data['phone_code'],
    })
    if not confirm.is_valid():
        return Response({'code': 4001, 'message': '手机验证码校验失败', 'errors': confirm.errors}, status=400)

    with transaction.atomic():
        data = serializer.validated_data
        email = data.get('email') or f"phone_{data['phone']}@local.investhub"
        user = User.objects.create_user(
            username=data['username'],
            email=email,
            phone=data['phone'],
            password=data['password'],
            display_name=data['username'],
            phone_verified=True,
            email_verified=bool(data.get('email')),
            identity_level='BASIC',
        )
        rec = confirm.validated_data['record']
        rec.status = 'VERIFIED'
        rec.verified_at = timezone.now()
        rec.user = user
        rec.save(update_fields=['status', 'verified_at', 'user'])
    tokens = get_tokens_for_user(user)
    return Response({
        'code': 0,
        'data': {'access': tokens['access'], 'refresh': tokens['refresh'], 'user': _auth_user_payload(user)}
    }, status=201)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_password(request):
    serializer = PasswordLoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'code': 4001, 'message': '登录失败', 'errors': serializer.errors}, status=400)
    user = serializer.validated_data['user']
    tokens = get_tokens_for_user(user)
    return Response({
        'code': 0,
        'data': {'access': tokens['access'], 'refresh': tokens['refresh'], 'user': _auth_user_payload(user)}
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def login_sms(request):
    serializer = SmsLoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'code': 4001, 'message': '登录失败', 'errors': serializer.errors}, status=400)
    user = serializer.validated_data['user']
    rec = serializer.validated_data['record']
    rec.status = 'VERIFIED'
    rec.verified_at = timezone.now()
    rec.user = user
    rec.save(update_fields=['status', 'verified_at', 'user'])
    tokens = get_tokens_for_user(user)
    return Response({
        'code': 0,
        'data': {'access': tokens['access'], 'refresh': tokens['refresh'], 'user': _auth_user_payload(user)}
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def verification_send(request):
    serializer = VerificationSendSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'code': 4001, 'message': '发送失败', 'errors': serializer.errors}, status=400)

    code = str(random.randint(100000, 999999))
    expires_at = timezone.now() + timedelta(minutes=10)
    record = UserVerificationCode.objects.create(
        channel=serializer.validated_data['channel'],
        target=serializer.validated_data['target'],
        purpose=serializer.validated_data['purpose'],
        code=code,
        expires_at=expires_at,
        status='SENT',
    )
    try:
        channel = serializer.validated_data['channel']
        target = serializer.validated_data['target']
        if channel == 'EMAIL':
            send_email_verification_code(target, code, minutes=10)
        elif channel == 'PHONE':
            send_sms_verification_code(target, code, minutes=10)
        else:
            raise ValueError('不支持的验证码渠道')
    except Exception as exc:
        record.status = 'INVALID'
        record.save(update_fields=['status'])
        return Response({'code': 4001, 'message': f'验证码发送失败: {exc}'}, status=400)

    payload = {'expiresAt': expires_at}
    if settings.DEBUG:
        payload['debugCode'] = code
    return Response({'code': 0, 'data': payload, 'message': '验证码已发送'})


@api_view(['POST'])
@permission_classes([AllowAny])
def verification_confirm(request):
    serializer = VerificationConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'code': 4001, 'message': '校验失败', 'errors': serializer.errors}, status=400)
    rec = serializer.validated_data['record']
    rec.status = 'VERIFIED'
    rec.verified_at = timezone.now()
    rec.save(update_fields=['status', 'verified_at'])
    return Response({'code': 0, 'message': '验证码校验通过'})


@api_view(['GET'])
@permission_classes([AllowAny])
def oauth_start(request, provider):
    try:
        provider = _ensure_social_provider(provider)
        state = uuid.uuid4().hex
        cache.set(f"oauth_state:{state}", provider, timeout=600)
        if provider == 'WECHAT':
            client = WeChatOAuthClient(
                getattr(settings, 'WECHAT_APP_ID', ''),
                getattr(settings, 'WECHAT_APP_SECRET', ''),
                getattr(settings, 'WECHAT_REDIRECT_URI', ''),
            )
        else:
            client = WeiboOAuthClient(
                getattr(settings, 'WEIBO_CLIENT_ID', ''),
                getattr(settings, 'WEIBO_CLIENT_SECRET', ''),
                getattr(settings, 'WEIBO_REDIRECT_URI', ''),
            )
        url = client.build_authorize_url(state)
        return Response({'code': 0, 'data': {'authorizeUrl': url, 'state': state}})
    except Exception as exc:
        return Response({'code': 4001, 'message': str(exc)}, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])
def oauth_callback(request, provider):
    code = request.query_params.get('code')
    state = request.query_params.get('state')
    try:
        provider = _ensure_social_provider(provider)
        if not code or not state:
            return Response({'code': 4001, 'message': '缺少code/state参数'}, status=400)
        cached = cache.get(f"oauth_state:{state}")
        if cached != provider:
            return Response({'code': 4001, 'message': 'state校验失败'}, status=400)

        if provider == 'WECHAT':
            client = WeChatOAuthClient(
                getattr(settings, 'WECHAT_APP_ID', ''),
                getattr(settings, 'WECHAT_APP_SECRET', ''),
                getattr(settings, 'WECHAT_REDIRECT_URI', ''),
            )
            token_data = client.exchange_code(code)
            social_info = client.fetch_userinfo(token_data['access_token'], token_data['openid'])
        else:
            client = WeiboOAuthClient(
                getattr(settings, 'WEIBO_CLIENT_ID', ''),
                getattr(settings, 'WEIBO_CLIENT_SECRET', ''),
                getattr(settings, 'WEIBO_REDIRECT_URI', ''),
            )
            token_data = client.exchange_code(code)
            social_info = client.fetch_userinfo(token_data['access_token'], token_data['uid'])

        user, _social = _create_or_bind_social_user(provider, social_info, token_data)
        tokens = get_tokens_for_user(user)
        return Response({
            'code': 0,
            'data': {'access': tokens['access'], 'refresh': tokens['refresh'], 'user': _auth_user_payload(user)}
        })
    except Exception as exc:
        return Response({'code': 4001, 'message': f'OAuth回调失败: {exc}'}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def oauth_bind(request, provider):
    provider = _ensure_social_provider(provider)
    provider_uid = request.data.get('provider_uid')
    if not provider_uid:
        return Response({'code': 4001, 'message': '缺少provider_uid'}, status=400)
    if UserSocialAccount.objects.filter(provider=provider, provider_uid=provider_uid).exclude(user=request.user).exists():
        return Response({'code': 4090, 'message': '该第三方账号已绑定其他用户'}, status=409)
    UserSocialAccount.objects.update_or_create(
        user=request.user,
        provider=provider,
        provider_uid=provider_uid,
        defaults={
            'unionid': request.data.get('unionid') or '',
            'openid': request.data.get('openid') or '',
            'access_token': request.data.get('access_token') or '',
            'refresh_token': request.data.get('refresh_token') or '',
        }
    )
    return Response({'code': 0, 'message': '绑定成功'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_real_name(request):
    serializer = RealNameSubmitSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'code': 4001, 'message': '提交失败', 'errors': serializer.errors}, status=400)
    data = serializer.validated_data
    rec = UserRealNameVerification.objects.create(
        user=request.user,
        real_name=data['real_name'],
        id_card_no_masked=_mask_id_card(data['id_card_no']),
        id_card_hash=_hash_id_card(data['id_card_no']),
        face_score=data.get('face_score'),
        ocr_passed=data.get('ocr_passed', True),
        liveness_passed=data.get('liveness_passed', True),
        status='PENDING',
    )
    request.user.real_name_status = 'PENDING'
    request.user.save(update_fields=['real_name_status'])
    return Response({'code': 0, 'data': {'id': rec.id}, 'message': '实名认证申请已提交'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_professional(request):
    serializer = ProfessionalSubmitSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'code': 4001, 'message': '提交失败', 'errors': serializer.errors}, status=400)
    if request.user.risk_assessment_status != 'APPROVED':
        return Response({'code': 4001, 'message': '请先完成风险评估问卷'}, status=400)
    rec = UserProfessionalVerification.objects.create(
        user=request.user,
        qualification_doc_url=serializer.validated_data.get('qualification_doc_url', ''),
        education_doc_url=serializer.validated_data.get('education_doc_url', ''),
        additional_doc_url=serializer.validated_data.get('additional_doc_url', ''),
        status='PENDING',
    )
    request.user.professional_status = 'PENDING'
    request.user.save(update_fields=['professional_status'])
    return Response({'code': 0, 'data': {'id': rec.id}, 'message': '专业认证申请已提交'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def kyc_status(request):
    serializer = UserKycStatusSerializer(request.user)
    return Response({'code': 0, 'data': serializer.data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def risk_questionnaire(request):
    template = RiskQuestionnaireTemplate.objects.filter(is_active=True).order_by('-created_at').first()
    if not template:
        default_questions = [
            {'id': 1, 'text': '你可接受的最大回撤是？', 'options': [{'label': '5%', 'score': 10}, {'label': '10%', 'score': 20}, {'label': '20%', 'score': 30}, {'label': '30%+', 'score': 40}]},
            {'id': 2, 'text': '你的投资经验年限？', 'options': [{'label': '0-1年', 'score': 10}, {'label': '1-3年', 'score': 20}, {'label': '3-5年', 'score': 30}, {'label': '5年以上', 'score': 40}]},
            {'id': 3, 'text': '你更看重？', 'options': [{'label': '保本', 'score': 10}, {'label': '稳健增值', 'score': 20}, {'label': '成长收益', 'score': 30}, {'label': '高收益', 'score': 40}]},
        ]
        template = RiskQuestionnaireTemplate.objects.create(
            version='v1',
            title='投资者风险评估问卷',
            description='用于评估投资者风险承受能力',
            questions=default_questions,
            is_active=True,
        )
    return Response({'code': 0, 'data': {'id': template.id, 'version': template.version, 'title': template.title, 'questions': template.questions}})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_risk_questionnaire(request):
    serializer = RiskQuestionnaireSubmitSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'code': 4001, 'message': '提交失败', 'errors': serializer.errors}, status=400)
    template_id = serializer.validated_data.get('template_id')
    answers = serializer.validated_data['answers'] or {}
    if template_id:
        template = get_object_or_404(RiskQuestionnaireTemplate, id=template_id)
    else:
        template = RiskQuestionnaireTemplate.objects.filter(is_active=True).order_by('-created_at').first()
        if not template:
            return Response({'code': 4001, 'message': '暂无可用问卷'}, status=400)

    # 允许前端直接上传总分，也支持按题目分值汇总
    score = answers.get('total_score')
    if score is None:
        score = 0
        selected = answers.get('selected', {})
        for _k, v in selected.items():
            try:
                score += int(v)
            except (ValueError, TypeError):
                pass
    score = int(score)
    risk_level = _calc_risk_level(score)

    submission = RiskQuestionnaireSubmission.objects.create(
        user=request.user, template=template, answers=answers, score=score, risk_level=risk_level
    )
    user = request.user
    user.risk_assessment_status = 'APPROVED'
    user.risk_level = risk_level
    if user.identity_level in ['UNVERIFIED', 'BASIC', 'REAL_NAME']:
        user.identity_level = 'BASIC' if user.identity_level == 'UNVERIFIED' else user.identity_level
    user.save(update_fields=['risk_assessment_status', 'risk_level', 'identity_level'])
    return Response({'code': 0, 'data': {'id': submission.id, 'score': score, 'riskLevel': risk_level}})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def risk_result(request):
    latest = RiskQuestionnaireSubmission.objects.filter(user=request.user).order_by('-created_at').first()
    if not latest:
        return Response({'code': 4040, 'message': '尚未完成风险评估'}, status=404)
    return Response({
        'code': 0,
        'data': {
            'score': latest.score,
            'riskLevel': latest.risk_level,
            'templateVersion': latest.template.version,
            'createdAt': latest.created_at,
        }
    })


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def manage_current_user(request):
    """管理当前用户信息 - GET: 获取用户信息, PATCH: 更新用户资料"""
    if request.method == 'GET':
        # 获取当前用户信息
        serializer = UserProfileSerializer(request.user)
        return Response({
            'code': 0,
            'data': serializer.data
        })
    
    elif request.method == 'PATCH':
        # 更新用户资料
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'code': 0,
                'data': serializer.data
            })
        return Response({
            'code': 4001,
            'message': '更新失败',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def user_profile_overview(request, user_id):
    """用户主页首屏聚合：公开资料 + 近期帖子 + 公开组合 + 关注统计。"""
    from django.db.models import Count

    from portfolios.views import get_portfolio_metrics

    target = get_object_or_404(User, id=user_id)
    profile = UserPublicSerializer(target).data

    posts = list(
        Content.objects.filter(author=target, status='PUBLISHED')
        .select_related('author')
        .prefetch_related('assets', 'boards', 'attachments', 'meta', 'poll__options')
        .order_by('-created_at')[:10]
    )
    post_ctx = build_post_card_context(request, [p.id for p in posts])
    recent_posts = ContentCardSerializer(posts, many=True, context=post_ctx).data

    portfolios = list(
        Portfolio.objects.filter(owner=target, is_public=True)
        .select_related('owner')
        .prefetch_related('assets', 'assets__asset')
        .annotate(
            favorites_count=Count('favorites', distinct=True),
            asset_count=Count('assets', distinct=True),
        )
        .order_by('-created_at')[:12]
    )
    pids = [p.id for p in portfolios]
    liked_pf = set()
    fav_pf = set()
    if request.user.is_authenticated and pids:
        from content.models import Like
        from portfolios.models import PortfolioFavorite

        liked_pf = set(
            Like.objects.filter(
                user=request.user, target_type='PORTFOLIO', target_id__in=pids
            ).values_list('target_id', flat=True)
        )
        fav_pf = set(
            PortfolioFavorite.objects.filter(
                user=request.user, portfolio_id__in=pids
            ).values_list('portfolio_id', flat=True)
        )
    metrics = get_portfolio_metrics(portfolios)
    recent_portfolios = PortfolioListSerializer(
        portfolios,
        many=True,
        context={
            'request': request,
            'portfolio_metrics': metrics,
            'liked_portfolio_ids': liked_pf,
            'favorited_portfolio_ids': fav_pf,
        },
    ).data

    star_following = UserStarFollow.objects.filter(user=target).count()
    follow_stats = {
        'followers': target.followers_count,
        'following': target.following_count,
        'starFollowing': star_following,
    }

    return Response({
        'code': 0,
        'data': {
            'profile': profile,
            'recentPosts': recent_posts,
            'recentPortfolios': recent_portfolios,
            'followStats': follow_stats,
        },
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_profile(request, user_id):
    """获取用户公开资料"""
    user = get_object_or_404(User, id=user_id)
    serializer = UserPublicSerializer(user)
    return Response({
        'code': 0,
        'data': serializer.data
    })


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def invest_profile(request):
    """获取或更新投资偏好"""
    profile, created = UserInvestProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'GET':
        serializer = UserInvestProfileSerializer(profile)
        return Response({
            'code': 0,
            'data': serializer.data
        })
    
    elif request.method == 'PUT':
        serializer = UserInvestProfileSerializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'code': 0,
                'data': serializer.data
            })
        return Response({
            'code': 4001,
            'message': '更新失败',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_follow(request, user_id):
    """管理用户关注 - POST: 关注用户, DELETE: 取消关注"""
    target_user = get_object_or_404(User, id=user_id)
    
    if target_user == request.user:
        return Response({
            'code': 4001,
            'message': '不能关注自己'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'POST':
        # 关注用户（计数用 F()/数据库原子更新，避免并发覆盖）
        created = False
        with transaction.atomic():
            _, created = UserFollow.objects.get_or_create(
                follower=request.user,
                followee=target_user
            )
            if created:
                User.objects.filter(pk=request.user.pk).update(
                    following_count=F('following_count') + 1
                )
                User.objects.filter(pk=target_user.pk).update(
                    followers_count=F('followers_count') + 1
                )

        if created:
            fid, tid = request.user.pk, target_user.pk

            def _notify_follow():
                safe_task_delay(publish_follow_created_task, args=(fid, tid))

            transaction.on_commit(_notify_follow)
            return Response({
                'code': 0,
                'message': '关注成功'
            })
        return Response({
            'code': 4090,
            'message': '已经关注过了'
        }, status=status.HTTP_409_CONFLICT)

    elif request.method == 'DELETE':
        # 取消关注用户
        try:
            follow = UserFollow.objects.get(follower=request.user, followee=target_user)
        except UserFollow.DoesNotExist:
            return Response({
                'code': 4040,
                'message': '没有关注过该用户'
            }, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            follow.delete()
            UserStarFollow.objects.filter(user=request.user, follow_user=target_user).delete()
            User.objects.filter(pk=request.user.pk).update(
                following_count=Greatest(F('following_count') - 1, 0)
            )
            User.objects.filter(pk=target_user.pk).update(
                followers_count=Greatest(F('followers_count') - 1, 0)
            )

        return Response({
            'code': 0,
            'message': '取消关注成功'
        })


class UserFollowersView(generics.ListAPIView):
    """用户粉丝列表"""
    serializer_class = UserFollowSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return UserFollow.objects.filter(followee_id=user_id).select_related('follower')
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': 0,
            'data': serializer.data
        })


class UserFollowingView(generics.ListAPIView):
    """用户关注列表"""
    serializer_class = UserFollowSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return UserFollow.objects.filter(follower_id=user_id).select_related('followee')
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': 0,
            'data': serializer.data
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def follow_status(request, user_id):
    """查询关注状态"""
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        return Response({
            'code': 0,
            'data': {'isFollowing': False, 'isMutual': False, 'isStarred': False}
        })
    is_following = UserFollow.objects.filter(follower=request.user, followee=target_user).exists()
    is_mutual = is_following and UserFollow.objects.filter(follower=target_user, followee=request.user).exists()
    is_starred = UserStarFollow.objects.filter(user=request.user, follow_user=target_user).exists()
    return Response({'code': 0, 'data': {'isFollowing': is_following, 'isMutual': is_mutual, 'isStarred': is_starred}})


@api_view(['GET'])
@permission_classes([AllowAny])
def follow_stats(request, user_id):
    user = get_object_or_404(User, id=user_id)
    star_following = UserStarFollow.objects.filter(user=user).count()
    return Response({
        'code': 0,
        'data': {
            'followers': user.followers_count,
            'following': user.following_count,
            'starFollowing': star_following,
        }
    })


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_star_follow(request, user_id):
    """管理特别关注"""
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        return Response({'code': 4001, 'message': '不能特别关注自己'}, status=status.HTTP_400_BAD_REQUEST)
    if not UserFollow.objects.filter(follower=request.user, followee=target_user).exists():
        return Response({'code': 4001, 'message': '请先关注该用户'}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'POST':
        _, created = UserStarFollow.objects.get_or_create(user=request.user, follow_user=target_user)
        if not created:
            return Response({'code': 4090, 'message': '已设置特别关注'}, status=status.HTTP_409_CONFLICT)
        FollowFeedItem.objects.filter(user=request.user, actor_user=target_user).update(is_star_actor=True)
        return Response({'code': 0, 'message': '设置特别关注成功'})

    deleted, _ = UserStarFollow.objects.filter(user=request.user, follow_user=target_user).delete()
    if not deleted:
        return Response({'code': 4040, 'message': '未设置特别关注'}, status=status.HTTP_404_NOT_FOUND)
    FollowFeedItem.objects.filter(user=request.user, actor_user=target_user).update(is_star_actor=False)
    return Response({'code': 0, 'message': '已取消特别关注'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_star_following(request):
    qs = UserStarFollow.objects.filter(user=request.user).select_related('follow_user').order_by('-created_at')
    items = [{
        'id': x.follow_user.id,
        'username': x.follow_user.username,
        'display_name': x.follow_user.display_name,
        'avatar_url': x.follow_user.avatar_url,
        'followers_count': x.follow_user.followers_count,
        'following_count': x.follow_user.following_count,
        'created_at': x.created_at,
    } for x in qs]
    return Response({'code': 0, 'data': items})


@api_view(['POST'])
@permission_classes([IsAuthenticated])  
def logout(request):
    """
    用户登出（兼容模式）：
    - 提供 refresh：加入 black list
    - 不提供 refresh：兼容旧前端，仅返回成功
    """
    refresh = request.data.get('refresh')
    if not refresh:
        return ok(message='登出成功')

    try:
        token = RefreshToken(refresh)
        token.blacklist()
    except TokenError:
        return fail(4001, 'refresh token 无效或已过期', status.HTTP_400_BAD_REQUEST)
    except AttributeError:
        return fail(5001, '黑名单功能未启用', status.HTTP_500_INTERNAL_SERVER_ERROR)

    return ok(message='登出成功')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def following_feed(request):
    """
    关注流 / 社交 Feed：当前用户关注的人发布的公开内容

    - 仅返回已发布的帖子（PUBLISHED）
    - 支持分页：page / pageSize
    - 按发布时间倒序
    """
    user = request.user

    queryset = FollowFeedItem.objects.filter(
        user=user,
        is_deleted=False,
    ).select_related('actor_user').order_by('-is_star_actor', '-created_at')
    if not queryset.exists():
        return Response({
            'code': 0,
            'data': {
                'items': [],
                'page': 1,
                'pageSize': int(request.query_params.get('pageSize', 20)),
                'total': 0,
            }
        })

    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('pageSize', 20))
    total = queryset.count()
    start = (page - 1) * page_size
    end = start + page_size
    feed_items = queryset[start:end]

    post_ids = [x.object_id for x in feed_items if x.object_type == 'POST']
    posts_map = {
        post.id: post for post in Content.objects.select_related('author').prefetch_related('assets').filter(
            id__in=post_ids, status='PUBLISHED'
        )
    }
    items = []
    for row in feed_items:
        if row.object_type != 'POST':
            continue
        post = posts_map.get(row.object_id)
        if not post:
            continue
        pctx = build_post_card_context(request, [post.id])
        data = ContentCardSerializer(post, context=pctx).data
        data['feedMeta'] = {
            'actionType': row.action_type,
            'actorUserId': row.actor_user_id,
            'isStarActor': row.is_star_actor,
            'createdAt': row.created_at,
        }
        items.append(data)

    return Response({
        'code': 0,
        'data': {
            'items': items,
            'page': page,
            'pageSize': page_size,
            'total': total,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def following_portfolios_feed(request):
    """
    关注用户的公开组合更新流：
    - 只包含 is_public=True 的组合
    - 组合拥有者在当前用户的关注列表中
    - 默认按创建时间倒序
    """
    user = request.user

    followee_ids = list(
        UserFollow.objects.filter(follower=user).values_list('followee_id', flat=True)
    )
    if not followee_ids:
        return Response({
            'code': 0,
            'data': {
                'items': [],
                'page': 1,
                'pageSize': int(request.query_params.get('pageSize', 20)),
                'total': 0,
            }
        })

    queryset = Portfolio.objects.filter(
        is_public=True,
        owner_id__in=followee_ids,
    ).select_related('owner').prefetch_related('assets', 'assets__asset').order_by('-created_at')

    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('pageSize', 20))
    total = queryset.count()
    start = (page - 1) * page_size
    end = start + page_size

    portfolios = queryset[start:end]
    serializer = PortfolioListSerializer(portfolios, many=True, context={'request': request})

    return Response({
        'code': 0,
        'data': {
            'items': serializer.data,
            'page': page,
            'pageSize': page_size,
            'total': total,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def following_recommendations(request):
    """
    关注推荐：你可能感兴趣的用户 / 组合

    - 当前用户尚未关注的活跃用户（按 followers_count 排序）
    - 热门公开组合（按 returns_ytd、likes 排序）
    """
    user = request.user

    # 安全解析 limit 参数，范围限制在 1~20 之间
    try:
        limit = int(request.query_params.get('limit', 5))
    except (TypeError, ValueError):
        limit = 5
    limit = max(1, min(limit, 20))

    # 已关注用户 ID，用于排除
    followed_ids = list(
        UserFollow.objects.filter(follower=user).values_list('followee_id', flat=True)
    )

    # 推荐用户：排除自己和已关注用户，按粉丝数倒序
    user_qs = User.objects.exclude(
        id__in=followed_ids + [user.id]
    ).order_by('-followers_count')[:limit]
    user_serializer = UserPublicSerializer(user_qs, many=True)

    # 推荐组合：公开组合，按收益率/点赞数倒序
    portfolio_qs = Portfolio.objects.filter(
        is_public=True,
    ).select_related('owner').prefetch_related('assets', 'assets__asset').order_by(
        '-returns_ytd', '-likes', '-created_at'
    )[:limit]
    portfolio_serializer = PortfolioListSerializer(
        portfolio_qs, many=True, context={'request': request}
    )

    return Response({
        'code': 0,
        'data': {
            'users': user_serializer.data,
            'portfolios': portfolio_serializer.data,
        }
    })


# ===========================
# 用户治理后台相关接口（Admin）
# ===========================


def _ensure_moderator(request):
    if not request.user.is_authenticated:
        return Response({'code': 4010, 'message': '需要登录'}, status=status.HTTP_401_UNAUTHORIZED)
    if request.user.role not in ['MODERATOR', 'ADMIN']:
        return Response({'code': 4030, 'message': '无权限'}, status=status.HTTP_403_FORBIDDEN)
    return None


def _create_moderation_log(user, operator, action, reason='', expire_at=None):
    return UserModerationLog.objects.create(
        user=user,
        operator=operator,
        action=action,
        reason=reason or '',
        expire_at=expire_at,
    )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def admin_update_user_status(request, user_id):
    """
    PATCH /api/admin/users/{id}/status/
    直接修改用户状态字段（NORMAL/MUTED/BANNED），并记录治理日志
    """
    perm_error = _ensure_moderator(request)
    if perm_error:
        return perm_error

    user = get_object_or_404(User, id=user_id)

    new_status = request.data.get('status')
    reason = request.data.get('reason', '')

    if new_status not in ['NORMAL', 'MUTED', 'BANNED']:
        return Response({'code': 4001, 'message': '无效的状态值'}, status=status.HTTP_400_BAD_REQUEST)

    # 更新状态及激活标记
    user.status = new_status
    if new_status == 'BANNED':
        user.is_active = False
    elif new_status == 'NORMAL':
        user.is_active = True
        user.mute_until = None
    user.save(update_fields=['status', 'is_active', 'mute_until'])

    _create_moderation_log(user, request.user, 'STATUS_CHANGE', reason=reason)

    return Response({'code': 0, 'message': '用户状态已更新'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_mute_user(request, user_id):
    """
    POST /api/admin/users/{id}/mute/
    body: { "days": 7, "reason": "刷屏广告" }
    将用户设为 MUTED，并设置 mute_until
    """
    perm_error = _ensure_moderator(request)
    if perm_error:
        return perm_error

    user = get_object_or_404(User, id=user_id)

    days = int(request.data.get('days', 7))
    if days <= 0:
        days = 1
    reason = request.data.get('reason', '')

    expire_at = timezone.now() + timezone.timedelta(days=days)

    user.status = 'MUTED'
    user.mute_until = expire_at
    user.is_active = True  # 禁言不影响登录
    user.save(update_fields=['status', 'mute_until', 'is_active'])

    _create_moderation_log(user, request.user, 'MUTE', reason=reason, expire_at=expire_at)

    return Response({'code': 0, 'message': f'用户已被禁言 {days} 天'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_ban_user(request, user_id):
    """
    POST /api/admin/users/{id}/ban/
    body: { "reason": "严重违规" }
    将用户设为 BANNED，并禁止登录/访问
    """
    perm_error = _ensure_moderator(request)
    if perm_error:
        return perm_error

    user = get_object_or_404(User, id=user_id)
    reason = request.data.get('reason', '')

    user.status = 'BANNED'
    user.is_active = False
    user.save(update_fields=['status', 'is_active'])

    _create_moderation_log(user, request.user, 'BAN', reason=reason)

    return Response({'code': 0, 'message': '用户已被封禁'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_unmute_user(request, user_id):
    """
    POST /api/admin/users/{id}/unmute/
    解除禁言
    """
    perm_error = _ensure_moderator(request)
    if perm_error:
        return perm_error

    user = get_object_or_404(User, id=user_id)
    reason = request.data.get('reason', '')

    user.mute_until = None
    # 若之前是 MUTED，则恢复为 NORMAL；若是 BANNED 则不自动解封
    if user.status == 'MUTED':
        user.status = 'NORMAL'
    user.save(update_fields=['status', 'mute_until'])

    _create_moderation_log(user, request.user, 'UNMUTE', reason=reason)

    return Response({'code': 0, 'message': '已解除禁言'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_unban_user(request, user_id):
    """
    POST /api/admin/users/{id}/unban/
    解除封禁，恢复可登录
    """
    perm_error = _ensure_moderator(request)
    if perm_error:
        return perm_error

    user = get_object_or_404(User, id=user_id)
    reason = request.data.get('reason', '')

    user.status = 'NORMAL'
    user.is_active = True
    user.save(update_fields=['status', 'is_active'])

    _create_moderation_log(user, request.user, 'UNBAN', reason=reason)

    return Response({'code': 0, 'message': '已解除封禁'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_moderated_users(request):
    """
    GET /api/admin/users/moderation/
    返回当前处于 MUTED/BANNED 状态的用户及最近一次治理记录
    """
    perm_error = _ensure_moderator(request)
    if perm_error:
        return perm_error

    users = User.objects.filter(status__in=['MUTED', 'BANNED']).order_by('-created_at')

    items = []
    for u in users:
        last_log = u.moderation_logs.first()
        items.append({
            'id': u.id,
            'username': u.username,
            'displayName': u.display_name,
            'status': u.status,
            'muteUntil': u.mute_until,
            'lastAction': last_log.action if last_log else None,
            'lastReason': last_log.reason if last_log else '',
            'lastOperator': last_log.operator.display_name if last_log and last_log.operator else None,
            'lastCreatedAt': last_log.created_at if last_log else None,
        })

    return Response({
        'code': 0,
        'data': {
            'items': items,
            'total': len(items),
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_users_risk(request):
    """
    GET /api/admin/users/risk/
    用户风险画像与行为指标列表
    """
    perm_error = _ensure_moderator(request)
    if perm_error:
        return perm_error

    risk_level = request.query_params.get('riskLevel')
    sort_by = request.query_params.get('sortBy', 'riskScore')
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('pageSize', 20))
    offset = (page - 1) * page_size

    users = User.objects.all().order_by('-updated_at')
    if risk_level in ['LOW', 'MEDIUM', 'HIGH']:
        if risk_level == 'LOW':
            users = users.filter(quality_score__gte=80)
        elif risk_level == 'MEDIUM':
            users = users.filter(quality_score__gte=50, quality_score__lt=80)
        else:
            users = users.filter(quality_score__lt=50)

    user_ids = list(users.values_list('id', flat=True))
    behavior_rows = (
        UserBehaviorDaily.objects
        .filter(user_id__in=user_ids)
        .values('user_id')
        .annotate(
            post_count=Sum('post_count'),
            comment_count=Sum('comment_count'),
            reported_count=Sum('reported_count'),
            violation_count=Sum('violation_count'),
        )
    )
    behavior_map = {x['user_id']: x for x in behavior_rows}

    items = []
    for u in users[offset: offset + page_size]:
        behavior = behavior_map.get(u.id, {})
        risk_score = int(
            (behavior.get('violation_count') or 0) * 25 +
            (behavior.get('reported_count') or 0) * 10 +
            (100 - float(u.quality_score or 0)) * 0.5
        )
        items.append({
            'id': u.id,
            'username': u.username,
            'displayName': u.display_name,
            'status': u.status,
            'points': u.points,
            'level': u.level,
            'qualityScore': float(u.quality_score),
            'riskScore': risk_score,
            'postCount': behavior.get('post_count') or 0,
            'commentCount': behavior.get('comment_count') or 0,
            'reportedCount': behavior.get('reported_count') or 0,
            'violationCount': behavior.get('violation_count') or 0,
        })

    if sort_by == 'reportedCount':
        items.sort(key=lambda x: x['reportedCount'], reverse=True)
    else:
        items.sort(key=lambda x: x['riskScore'], reverse=True)

    return Response({
        'code': 0,
        'data': {
            'items': items,
            'page': page,
            'pageSize': page_size,
            'total': users.count(),
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_user_behavior_report(request, user_id):
    """
    GET /api/admin/users/{id}/behavior-report/
    """
    perm_error = _ensure_moderator(request)
    if perm_error:
        return perm_error
    target_user = get_object_or_404(User, id=user_id)
    range_param = request.query_params.get('range', '7d')
    days = 30 if range_param == '30d' else 7
    start_date = timezone.now().date() - timezone.timedelta(days=days - 1)
    rows = UserBehaviorDaily.objects.filter(user=target_user, stat_date__gte=start_date).order_by('stat_date')
    daily = [{
        'date': r.stat_date,
        'postCount': r.post_count,
        'commentCount': r.comment_count,
        'reportedCount': r.reported_count,
        'violationCount': r.violation_count,
        'receivedLikes': r.received_likes,
        'qualityScore': float(r.quality_score),
    } for r in rows]
    summary = {
        'postCount': sum(x['postCount'] for x in daily),
        'commentCount': sum(x['commentCount'] for x in daily),
        'reportedCount': sum(x['reportedCount'] for x in daily),
        'violationCount': sum(x['violationCount'] for x in daily),
        'receivedLikes': sum(x['receivedLikes'] for x in daily),
    }
    return Response({'code': 0, 'data': {'userId': target_user.id, 'range': range_param, 'summary': summary, 'daily': daily}})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_warning_user(request, user_id):
    """
    POST /api/admin/users/{id}/warning/
    """
    perm_error = _ensure_moderator(request)
    if perm_error:
        return perm_error
    target_user = get_object_or_404(User, id=user_id)
    reason = request.data.get('reason', '')
    _create_moderation_log(target_user, request.user, 'WARNING', reason=reason)
    apply_points(
        user=target_user,
        event_type='MODERATION_PENALTY',
        delta=-5,
        source_type='USER',
        source_id=target_user.id,
        reason=reason or '管理员警告扣分',
        operator=request.user,
    )
    return Response({'code': 0, 'message': '警告已记录'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_user_points_logs(request, user_id):
    """
    GET /api/admin/users/{id}/points/logs/
    """
    perm_error = _ensure_moderator(request)
    if perm_error:
        return perm_error
    target_user = get_object_or_404(User, id=user_id)
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('pageSize', 20))
    qs = UserPointLog.objects.filter(user=target_user).select_related('operator').order_by('-created_at')
    total = qs.count()
    logs = qs[(page - 1) * page_size: page * page_size]
    items = [{
        'id': log.id,
        'delta': log.delta,
        'eventType': log.event_type,
        'sourceType': log.source_type,
        'sourceId': log.source_id,
        'reason': log.reason,
        'operator': log.operator.display_name if log.operator else None,
        'createdAt': log.created_at,
    } for log in logs]
    return Response({'code': 0, 'data': {'items': items, 'page': page, 'pageSize': page_size, 'total': total}})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def admin_adjust_user_points(request, user_id):
    """
    PATCH /api/admin/users/{id}/points/adjust/
    仅 ADMIN 可调整积分
    """
    if not request.user.is_authenticated:
        return Response({'code': 4010, 'message': '需要登录'}, status=status.HTTP_401_UNAUTHORIZED)
    if request.user.role != 'ADMIN':
        return Response({'code': 4030, 'message': '仅管理员可调整积分'}, status=status.HTTP_403_FORBIDDEN)
    target_user = get_object_or_404(User, id=user_id)
    try:
        delta = int(request.data.get('delta', 0))
    except (TypeError, ValueError):
        return Response({'code': 4001, 'message': 'delta 必须是整数'}, status=status.HTTP_400_BAD_REQUEST)
    reason = request.data.get('reason', '')
    apply_points(
        user=target_user,
        event_type='ADMIN_ADJUST',
        delta=delta,
        source_type='USER',
        source_id=target_user.id,
        reason=reason or '管理员调整积分',
        operator=request.user,
    )
    return Response({'code': 0, 'message': '积分调整成功'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_review_real_name(request, verification_id):
    perm_error = _ensure_moderator(request)
    if perm_error:
        return perm_error
    rec = get_object_or_404(UserRealNameVerification, id=verification_id)
    action = request.data.get('action')
    reason = request.data.get('reason', '')
    if action not in ['APPROVE', 'REJECT']:
        return Response({'code': 4001, 'message': '无效操作'}, status=400)
    if action == 'APPROVE':
        rec.status = 'APPROVED'
        rec.reject_reason = ''
        rec.user.real_name_status = 'APPROVED'
        if rec.user.identity_level in ['UNVERIFIED', 'BASIC']:
            rec.user.identity_level = 'REAL_NAME'
        rec.user.save(update_fields=['real_name_status', 'identity_level'])
    else:
        rec.status = 'REJECTED'
        rec.reject_reason = reason or '资料不通过'
        rec.user.real_name_status = 'REJECTED'
        rec.user.save(update_fields=['real_name_status'])
    rec.reviewed_by = request.user
    rec.reviewed_at = timezone.now()
    rec.save(update_fields=['status', 'reject_reason', 'reviewed_by', 'reviewed_at'])
    return Response({'code': 0, 'message': '审核完成'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_review_professional(request, verification_id):
    perm_error = _ensure_moderator(request)
    if perm_error:
        return perm_error
    rec = get_object_or_404(UserProfessionalVerification, id=verification_id)
    action = request.data.get('action')
    reason = request.data.get('reason', '')
    user = rec.user
    if action not in ['APPROVE', 'REJECT']:
        return Response({'code': 4001, 'message': '无效操作'}, status=400)
    if action == 'APPROVE':
        if user.risk_assessment_status != 'APPROVED':
            return Response({'code': 4001, 'message': '用户未完成风险评估，不能通过专业认证'}, status=400)
        rec.status = 'APPROVED'
        rec.reject_reason = ''
        user.professional_status = 'APPROVED'
        user.identity_level = 'PROFESSIONAL'
        user.v_badge = True
        user.save(update_fields=['professional_status', 'identity_level', 'v_badge'])
    else:
        rec.status = 'REJECTED'
        rec.reject_reason = reason or '资料不通过'
        user.professional_status = 'REJECTED'
        user.v_badge = False
        user.save(update_fields=['professional_status', 'v_badge'])
    rec.reviewed_by = request.user
    rec.reviewed_at = timezone.now()
    rec.save(update_fields=['status', 'reject_reason', 'reviewed_by', 'reviewed_at'])
    return Response({'code': 0, 'message': '审核完成'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_pending_verifications(request):
    perm_error = _ensure_moderator(request)
    if perm_error:
        return perm_error

    real_items = UserRealNameVerification.objects.filter(status='PENDING').select_related('user').order_by('-created_at')[:200]
    pro_items = UserProfessionalVerification.objects.filter(status='PENDING').select_related('user').order_by('-created_at')[:200]
    return Response({
        'code': 0,
        'data': {
            'realName': [{
                'id': x.id,
                'userId': x.user_id,
                'username': x.user.username,
                'realName': x.real_name,
                'createdAt': x.created_at,
            } for x in real_items],
            'professional': [{
                'id': x.id,
                'userId': x.user_id,
                'username': x.user.username,
                'qualificationDocUrl': x.qualification_doc_url,
                'educationDocUrl': x.education_doc_url,
                'createdAt': x.created_at,
            } for x in pro_items]
        }
    })


class UserFavoritesView(generics.ListAPIView):
    """用户收藏列表"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        from content.models import Favorite

        favorites = (
            Favorite.objects.filter(user=request.user)
            .order_by('-created_at')
            .select_related('content', 'content__author')
            .prefetch_related(
                'content__assets',
                'content__boards',
                'content__attachments',
                'content__meta',
                'content__poll__options',
            )
        )
        contents = [fav.content for fav in favorites]
        post_ids = [c.id for c in contents]
        ctx = build_post_card_context(request, post_ids)

        serializer = ContentCardSerializer(contents, many=True, context=ctx)
        return Response({
            'code': 0,
            'data': {
                'items': serializer.data,
                'total': len(contents)
            }
        })


class UserLikesView(generics.ListAPIView):
    """用户点赞记录列表"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        from content.models import Like, Content, Comment
        from portfolios.models import Portfolio
        
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('pageSize', 20))
        offset = (page - 1) * page_size
        
        likes_qs = Like.objects.filter(user=request.user).order_by('-created_at')
        total = likes_qs.count()
        likes = likes_qs[offset:offset + page_size]
        
        items = []
        for like in likes:
            item = {
                'id': like.id,
                'targetType': like.target_type,
                'targetId': like.target_id,
                'createdAt': like.created_at,
                'target': None,
            }
            # 填充目标对象摘要
            try:
                if like.target_type == 'POST':
                    content = Content.objects.get(id=like.target_id)
                    item['target'] = {
                        'id': content.id,
                        'title': content.title,
                        'authorName': content.author.display_name,
                    }
                elif like.target_type == 'COMMENT':
                    comment = Comment.objects.select_related('author', 'content').get(id=like.target_id)
                    item['target'] = {
                        'id': comment.id,
                        'body': comment.body[:100],
                        'authorName': comment.author.display_name,
                        'postId': comment.content_id,
                        'postTitle': comment.content.title,
                    }
                elif like.target_type == 'PORTFOLIO':
                    portfolio = Portfolio.objects.select_related('owner').get(id=like.target_id)
                    item['target'] = {
                        'id': portfolio.id,
                        'title': portfolio.title,
                        'ownerName': portfolio.owner.display_name,
                    }
            except Exception:
                pass  # 目标已被删除时保留 target=None
            
            items.append(item)
        
        return Response({
            'code': 0,
            'data': {
                'items': items,
                'page': page,
                'pageSize': page_size,
                'total': total,
            }
        })


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def manage_privacy_settings(request):
    """管理当前用户隐私设置"""
    settings_obj, _ = UserPrivacySettings.objects.get_or_create(user=request.user)

    if request.method == 'GET':
        serializer = UserPrivacySettingsSerializer(settings_obj)
        return Response({'code': 0, 'data': serializer.data})

    serializer = UserPrivacySettingsSerializer(settings_obj, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({'code': 0, 'data': serializer.data, 'message': '隐私设置已更新'})
    return Response(
        {'code': 4001, 'message': '更新失败', 'errors': serializer.errors},
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_achievements(request):
    """我的成就概览（最小闭环实现）"""
    from content.models import Content, Like, Favorite
    from portfolios.models import Portfolio

    user = request.user

    posts_qs = Content.objects.filter(author=user)
    published_posts_qs = posts_qs.filter(status='PUBLISHED')
    post_count = posts_qs.count()

    # 暂无真实“精华帖”字段，使用高赞阈值近似（后续可替换为真实字段）
    featured_post_count = published_posts_qs.filter(like_count__gte=20).count()
    post_likes = published_posts_qs.aggregate(total=Sum('like_count')).get('total') or 0
    post_comments = published_posts_qs.aggregate(total=Sum('comment_count')).get('total') or 0

    portfolios_qs = Portfolio.objects.filter(owner=user)
    portfolio_count = portfolios_qs.count()
    portfolio_likes = portfolios_qs.aggregate(total=Sum('like_count')).get('total') or 0

    favorites_count = Favorite.objects.filter(user=user).count()
    likes_count = Like.objects.filter(user=user).count()
    followers_count = user.followers_count

    # 统一影响力口径：内容质量 + 社交反馈 + 活跃度
    influence_score = int(
        post_likes * 2 +
        post_comments * 3 +
        portfolio_likes * 2 +
        followers_count * 5 +
        post_count * 2 +
        portfolio_count * 3
    )

    badges = []
    if user.v_badge:
        badges.append({'code': 'VERIFIED_V', 'name': '认证V标识', 'description': '完成专业认证并获得V标识'})
    if post_count >= 10:
        badges.append({'code': 'CONTENT_CREATOR', 'name': '内容创作者', 'description': '累计发布10篇以上内容'})
    if featured_post_count >= 1:
        badges.append({'code': 'FEATURED_AUTHOR', 'name': '优质作者', 'description': '拥有高互动内容'})
    if influence_score >= 300:
        badges.append({'code': 'INFLUENCER', 'name': '社区影响力', 'description': '影响力值达到300+'})

    return Response({
        'code': 0,
        'data': {
            'postCount': post_count,
            'featuredPostCount': featured_post_count,
            'portfolioCount': portfolio_count,
            'favoritesCount': favorites_count,
            'likesCount': likes_count,
            'followersCount': followers_count,
            'influenceScore': influence_score,
            'badges': badges,
        }
    })