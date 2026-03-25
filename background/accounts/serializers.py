from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import (
    User, UserInvestProfile, UserFollow, UserVerificationCode,
    UserRealNameVerification, UserProfessionalVerification,
    RiskQuestionnaireTemplate, RiskQuestionnaireSubmission, UserPrivacySettings,
)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password', 'password_confirm']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("两次输入的密码不一致")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # 设置默认显示名称
        if not validated_data.get('display_name'):
            validated_data['display_name'] = validated_data['username']
        
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """用户登录序列化器"""
    username = serializers.CharField(required=False)
    identifier = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get('username') or attrs.get('identifier')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError('用户账号已被禁用')
                if user.status == 'BANNED':
                    raise serializers.ValidationError('用户账号已被封禁')
                attrs['user'] = user
                return attrs
            else:
                raise serializers.ValidationError('用户名或密码错误')
        else:
            raise serializers.ValidationError('必须提供用户名和密码')


class PasswordLoginSerializer(serializers.Serializer):
    """密码登录（支持用户名/邮箱/手机号）"""
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        identifier = attrs.get('identifier', '').strip()
        password = attrs.get('password')
        if not identifier or not password:
            raise serializers.ValidationError('必须提供登录标识和密码')

        user = None
        if '@' in identifier:
            user = User.objects.filter(email=identifier).first()
        elif identifier.isdigit():
            user = User.objects.filter(phone=identifier).first()
        else:
            user = User.objects.filter(username=identifier).first()

        if not user or not user.check_password(password):
            raise serializers.ValidationError('账号或密码错误')
        if not user.is_active or user.status == 'BANNED':
            raise serializers.ValidationError('账户已被封禁，无法登录')

        attrs['user'] = user
        return attrs


class EmailRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    email_code = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'email_code']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError('两次输入的密码不一致')
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError('邮箱已注册')
        return attrs


class PhoneRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    phone_code = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = ['username', 'phone', 'email', 'password', 'password_confirm', 'phone_code']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError('两次输入的密码不一致')
        if not attrs.get('phone'):
            raise serializers.ValidationError('手机号不能为空')
        if User.objects.filter(phone=attrs['phone']).exists():
            raise serializers.ValidationError('手机号已注册')
        email = attrs.get('email')
        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError('邮箱已注册')
        return attrs


class VerificationSendSerializer(serializers.Serializer):
    channel = serializers.ChoiceField(choices=UserVerificationCode.CHANNEL_CHOICES)
    target = serializers.CharField(max_length=255)
    purpose = serializers.ChoiceField(choices=UserVerificationCode.PURPOSE_CHOICES)

    def validate(self, attrs):
        channel = attrs.get('channel')
        target = (attrs.get('target') or '').strip()
        if channel == 'EMAIL':
            # 使用 DRF 内置邮箱校验，提前拦截空值/非法格式
            attrs['target'] = serializers.EmailField().to_internal_value(target)
        elif channel == 'PHONE':
            if len(target) < 6:
                raise serializers.ValidationError('手机号格式不正确')
            attrs['target'] = target
        return attrs


class VerificationConfirmSerializer(serializers.Serializer):
    channel = serializers.ChoiceField(choices=UserVerificationCode.CHANNEL_CHOICES)
    target = serializers.CharField(max_length=255)
    purpose = serializers.ChoiceField(choices=UserVerificationCode.PURPOSE_CHOICES)
    code = serializers.CharField(max_length=16)

    def validate(self, attrs):
        now = timezone.now()
        rec = UserVerificationCode.objects.filter(
            channel=attrs['channel'],
            target=attrs['target'],
            purpose=attrs['purpose'],
            code=attrs['code'],
            status='SENT',
            expires_at__gt=now
        ).order_by('-created_at').first()
        if not rec:
            raise serializers.ValidationError('验证码错误或已过期')
        attrs['record'] = rec
        return attrs


class SmsLoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=16)

    def validate(self, attrs):
        now = timezone.now()
        rec = UserVerificationCode.objects.filter(
            channel='PHONE',
            target=attrs['phone'],
            purpose='LOGIN',
            code=attrs['code'],
            status='SENT',
            expires_at__gt=now
        ).order_by('-created_at').first()
        if not rec:
            raise serializers.ValidationError('验证码错误或已过期')
        user = User.objects.filter(phone=attrs['phone']).first()
        if not user:
            raise serializers.ValidationError('手机号未注册')
        if not user.is_active or user.status == 'BANNED':
            raise serializers.ValidationError('账户已被封禁，无法登录')
        attrs['user'] = user
        attrs['record'] = rec
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """用户个人资料序列化器"""
    displayName = serializers.CharField(source='display_name')
    avatar = serializers.URLField(source='avatar_url')
    followers = serializers.IntegerField(source='followers_count', read_only=True)
    following = serializers.IntegerField(source='following_count', read_only=True)
    phoneVerified = serializers.BooleanField(source='phone_verified', read_only=True)
    emailVerified = serializers.BooleanField(source='email_verified', read_only=True)
    identityLevel = serializers.CharField(source='identity_level', read_only=True)
    realNameStatus = serializers.CharField(source='real_name_status', read_only=True)
    professionalStatus = serializers.CharField(source='professional_status', read_only=True)
    riskAssessmentStatus = serializers.CharField(source='risk_assessment_status', read_only=True)
    riskLevel = serializers.CharField(source='risk_level', read_only=True)
    vBadge = serializers.BooleanField(source='v_badge', read_only=True)
    investmentExperience = serializers.CharField(source='investment_experience', allow_blank=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'displayName', 
            'avatar', 'bio', 'role', 'status',
            'followers', 'following',
            'phoneVerified', 'emailVerified', 'identityLevel',
            'realNameStatus', 'professionalStatus',
            'riskAssessmentStatus', 'riskLevel', 'vBadge',
            'investmentExperience',
            'created_at'
        ]
        read_only_fields = ['id', 'username', 'role', 'status', 'followers', 'following', 'created_at']


class UserInvestProfileSerializer(serializers.ModelSerializer):
    """用户投资偏好序列化器"""
    class Meta:
        model = UserInvestProfile
        fields = ['risk_level', 'horizon', 'focus_market', 'preferred_assets']


class UserPublicSerializer(serializers.ModelSerializer):
    """用户公开信息序列化器（用于其他用户查看）"""
    class Meta:
        model = User
        fields = [
            'id', 'username', 'display_name', 'avatar_url', 
            'bio', 'role', 'followers_count', 'following_count', 'created_at'
        ]


class UserFollowSerializer(serializers.ModelSerializer):
    """用户关注序列化器"""
    follower = UserPublicSerializer(read_only=True)
    followee = UserPublicSerializer(read_only=True)

    class Meta:
        model = UserFollow
        fields = ['follower', 'followee', 'created_at']


class UserKycStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'phone_verified', 'email_verified', 'identity_level',
            'real_name_status', 'professional_status',
            'risk_assessment_status', 'risk_level', 'v_badge'
        ]


class RealNameSubmitSerializer(serializers.Serializer):
    real_name = serializers.CharField(max_length=100)
    id_card_no = serializers.CharField(max_length=32)
    face_score = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    ocr_passed = serializers.BooleanField(required=False, default=True)
    liveness_passed = serializers.BooleanField(required=False, default=True)


class ProfessionalSubmitSerializer(serializers.Serializer):
    qualification_doc_url = serializers.URLField(required=False, allow_blank=True)
    education_doc_url = serializers.URLField(required=False, allow_blank=True)
    additional_doc_url = serializers.URLField(required=False, allow_blank=True)


class RiskQuestionnaireSubmitSerializer(serializers.Serializer):
    template_id = serializers.IntegerField(required=False)
    answers = serializers.JSONField()


class UserPrivacySettingsSerializer(serializers.ModelSerializer):
    profileVisibility = serializers.CharField(source='profile_visibility', required=False)
    showInvestProfile = serializers.BooleanField(source='show_invest_profile', required=False)
    allowSearch = serializers.BooleanField(source='allow_search', required=False)
    showEmail = serializers.BooleanField(source='show_email', required=False)
    showPhone = serializers.BooleanField(source='show_phone', required=False)
    allowStrangerDm = serializers.BooleanField(source='allow_stranger_dm', required=False)

    class Meta:
        model = UserPrivacySettings
        fields = [
            'profileVisibility',
            'showInvestProfile',
            'allowSearch',
            'showEmail',
            'showPhone',
            'allowStrangerDm',
        ]