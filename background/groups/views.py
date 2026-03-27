import os

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Group, GroupMember, GroupJoinRequest, GroupReviewer, GroupInvite, GroupPost, GroupFile
from .serializers import (
    GroupSerializer,
    GroupCreateUpdateSerializer,
    GroupMemberSerializer,
    GroupJoinRequestSerializer,
    GroupReviewerSerializer,
    GroupInviteSerializer,
    GroupPostSerializer,
    GroupPostCreateSerializer,
    GroupFileSerializer,
)

User = get_user_model()


def _is_group_admin(user, group: Group) -> bool:
    if not user.is_authenticated:
        return False
    return GroupMember.objects.filter(
        group=group, user=user, status='ACTIVE', role__in=['OWNER', 'ADMIN']
    ).exists()


def _is_group_owner(user, group: Group) -> bool:
    if not user.is_authenticated:
        return False
    return GroupMember.objects.filter(group=group, user=user, status='ACTIVE', role='OWNER').exists()


def _is_group_member(user, group: Group) -> bool:
    if not user.is_authenticated:
        return False
    return GroupMember.objects.filter(group=group, user=user, status='ACTIVE').exists()


def _is_group_reviewer(user, group: Group) -> bool:
    if not user.is_authenticated:
        return False
    if _is_group_owner(user, group):
        return True
    return GroupReviewer.objects.filter(
        group=group,
        user=user,
        user__group_memberships__group=group,
        user__group_memberships__status='ACTIVE',
    ).exists()


def _forbidden(message: str, reason: str, action: str = ''):
    payload = {'code': 4030, 'message': message, 'reason': reason}
    if action:
        payload['action'] = action
    return Response(payload, status=403)


def _ensure_group_can_view(user, group: Group):
    if group.status != 'ACTIVE':
        return Response({'code': 4040, 'message': '群组不存在或已解散'}, status=404)
    if group.visibility == 'PRIVATE' and not _is_group_member(user, group):
        return _forbidden('私密群仅成员可查看', 'INVITE_ONLY', 'CONTACT_OWNER')
    return None


def _can_access_group_content(user, group: Group) -> bool:
    """
    群内容访问规则：
    - PUBLIC：允许访问内容（讨论/资料）
    - PRIVATE / APPROVAL：仅成员可访问内容
    """
    if group.visibility == 'PUBLIC':
        return True
    return _is_group_member(user, group)


def _content_access_denied_response(user, group: Group, content_label: str):
    if group.visibility == 'PRIVATE':
        return _forbidden(f'你暂无权限查看群{content_label}，该群仅受邀成员可访问', 'INVITE_ONLY', 'CONTACT_OWNER')
    pending = GroupJoinRequest.objects.filter(group=group, user=user, status='PENDING').exists()
    if pending:
        return _forbidden(f'你暂无权限查看群{content_label}，入群申请审核中', 'WAIT_REVIEW', 'WAIT_REVIEW')
    return _forbidden(f'你暂无权限查看群{content_label}，请先申请加入', 'APPROVAL_REQUIRED', 'APPLY_JOIN')


def _activate_member(group: Group, user):
    member = GroupMember.objects.filter(group=group, user=user).first()
    if member and member.status == 'ACTIVE':
        return False
    with transaction.atomic():
        if member:
            member.status = 'ACTIVE'
            member.role = member.role if member.role in ['OWNER', 'ADMIN'] else 'MEMBER'
            member.left_at = None
            member.joined_at = timezone.now()
            member.save(update_fields=['status', 'role', 'left_at', 'joined_at'])
        else:
            GroupMember.objects.create(group=group, user=user, role='MEMBER', status='ACTIVE')
        Group.objects.filter(pk=group.pk).update(member_count=F('member_count') + 1)
    return True


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def groups_list_create(request):
    if request.method == 'GET':
        qs = Group.objects.filter(status='ACTIVE').select_related('owner')
        q = request.query_params.get('q')
        visibility = request.query_params.get('visibility')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
        if visibility:
            qs = qs.filter(visibility=visibility)

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('pageSize', 20))
        total = qs.count()
        start = (page - 1) * page_size
        items = qs.order_by('-created_at')[start:start + page_size]
        data = GroupSerializer(items, many=True, context={'request': request}).data
        return Response({'code': 0, 'data': {'items': data, 'page': page, 'pageSize': page_size, 'total': total}})

    if not request.user.is_authenticated:
        return Response({'code': 4010, 'message': '需要登录'}, status=401)

    serializer = GroupCreateUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'code': 4001, 'message': '创建群组失败', 'errors': serializer.errors}, status=400)

    with transaction.atomic():
        group = serializer.save(owner=request.user, status='ACTIVE')
        GroupMember.objects.create(group=group, user=request.user, role='OWNER', status='ACTIVE')
    return Response({'code': 0, 'data': GroupSerializer(group, context={'request': request}).data}, status=201)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([AllowAny])
def group_detail(request, group_id: int):
    group = get_object_or_404(Group.objects.select_related('owner'), pk=group_id)
    if request.method == 'GET':
        perm_error = _ensure_group_can_view(request.user, group)
        if perm_error:
            return perm_error
        return Response({'code': 0, 'data': GroupSerializer(group, context={'request': request}).data})

    if not request.user.is_authenticated:
        return Response({'code': 4010, 'message': '需要登录'}, status=401)

    if request.method == 'PATCH':
        if not _is_group_admin(request.user, group):
            return Response({'code': 4030, 'message': '无权限编辑群组'}, status=403)
        serializer = GroupCreateUpdateSerializer(group, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({'code': 4001, 'message': '更新失败', 'errors': serializer.errors}, status=400)
        serializer.save()
        return Response({'code': 0, 'data': GroupSerializer(group, context={'request': request}).data})

    # DELETE 解散（仅群主）
    owner_member = GroupMember.objects.filter(group=group, user=request.user, status='ACTIVE', role='OWNER').first()
    if not owner_member:
        return Response({'code': 4030, 'message': '仅群主可解散群组'}, status=403)
    group.status = 'DISSOLVED'
    group.save(update_fields=['status', 'updated_at'])
    return Response({'code': 0, 'message': '群组已解散'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def group_join(request, group_id: int):
    group = get_object_or_404(Group, pk=group_id, status='ACTIVE')
    if _is_group_member(request.user, group):
        return Response({'code': 4090, 'message': '你已在群内'}, status=409)

    if group.visibility == 'PRIVATE':
        return _forbidden('私密群仅支持群主邀请加入', 'INVITE_ONLY', 'CONTACT_OWNER')

    if group.visibility == 'APPROVAL':
        if GroupJoinRequest.objects.filter(group=group, user=request.user, status='PENDING').exists():
            return Response({'code': 4090, 'message': '已提交申请，请等待审核'}, status=409)
        req = GroupJoinRequest.objects.create(
            group=group, user=request.user, status='PENDING', message=request.data.get('message', '')
        )
        return Response({'code': 0, 'data': GroupJoinRequestSerializer(req).data, 'message': '申请已提交'})

    # PUBLIC 直接加入
    _activate_member(group, request.user)
    return Response({'code': 0, 'message': '加入成功'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def group_leave(request, group_id: int):
    group = get_object_or_404(Group, pk=group_id, status='ACTIVE')
    member = GroupMember.objects.filter(group=group, user=request.user, status='ACTIVE').first()
    if not member:
        return Response({'code': 4040, 'message': '你不在该群'}, status=404)
    if member.role == 'OWNER':
        return Response({'code': 4001, 'message': '群主请先转让群主后再退出'}, status=400)
    member.status = 'LEFT'
    member.left_at = timezone.now()
    member.save(update_fields=['status', 'left_at'])
    Group.objects.filter(pk=group.pk, member_count__gt=0).update(member_count=F('member_count') - 1)
    return Response({'code': 0, 'message': '已退出群组'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def group_members(request, group_id: int):
    group = get_object_or_404(Group, pk=group_id, status='ACTIVE')
    perm_error = _ensure_group_can_view(request.user, group)
    if perm_error:
        return perm_error
    qs = GroupMember.objects.filter(group=group, status='ACTIVE').select_related('user').order_by('-role', '-joined_at')
    return Response({'code': 0, 'data': {'items': GroupMemberSerializer(qs, many=True).data, 'total': qs.count()}})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def group_member_set_role(request, group_id: int, user_id: int):
    group = get_object_or_404(Group, pk=group_id, status='ACTIVE')
    if not _is_group_admin(request.user, group):
        return Response({'code': 4030, 'message': '无权限'}, status=403)
    target = get_object_or_404(GroupMember, group=group, user_id=user_id, status='ACTIVE')
    action = request.data.get('action')
    if action == 'set_admin':
        if target.role == 'OWNER':
            return Response({'code': 4001, 'message': '群主无需设为管理员'}, status=400)
        target.role = 'ADMIN'
        target.save(update_fields=['role'])
        return Response({'code': 0, 'message': '设置管理员成功'})
    if action == 'remove_admin':
        if target.role != 'ADMIN':
            return Response({'code': 4001, 'message': '该成员不是管理员'}, status=400)
        target.role = 'MEMBER'
        target.save(update_fields=['role'])
        return Response({'code': 0, 'message': '已取消管理员'})
    if action == 'remove_member':
        if target.role == 'OWNER':
            return Response({'code': 4001, 'message': '不能移除群主'}, status=400)
        target.status = 'REMOVED'
        target.left_at = timezone.now()
        target.save(update_fields=['status', 'left_at'])
        Group.objects.filter(pk=group.pk, member_count__gt=0).update(member_count=F('member_count') - 1)
        return Response({'code': 0, 'message': '已移除成员'})
    return Response({'code': 4001, 'message': '无效操作'}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def group_transfer_owner(request, group_id: int):
    group = get_object_or_404(Group, pk=group_id, status='ACTIVE')
    owner = GroupMember.objects.filter(group=group, user=request.user, role='OWNER', status='ACTIVE').first()
    if not owner:
        return Response({'code': 4030, 'message': '仅群主可转让'}, status=403)
    target_user_id = request.data.get('targetUserId')
    target = GroupMember.objects.filter(group=group, user_id=target_user_id, status='ACTIVE').first()
    if not target:
        return Response({'code': 4040, 'message': '目标成员不存在'}, status=404)
    with transaction.atomic():
        owner.role = 'ADMIN'
        owner.save(update_fields=['role'])
        target.role = 'OWNER'
        target.save(update_fields=['role'])
        group.owner_id = target.user_id
        group.save(update_fields=['owner_id', 'updated_at'])
        if group.visibility == 'APPROVAL':
            GroupReviewer.objects.get_or_create(group=group, user_id=target.user_id)
    return Response({'code': 0, 'message': '群主转让成功'})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def group_join_requests(request, group_id: int):
    group = get_object_or_404(Group, pk=group_id, status='ACTIVE')
    if request.method == 'GET':
        if group.visibility != 'APPROVAL':
            return Response({'code': 4001, 'message': '当前群组无需审核申请'}, status=400)
        if not _is_group_reviewer(request.user, group):
            return Response({'code': 4030, 'message': '无权限'}, status=403)
        qs = GroupJoinRequest.objects.filter(group=group).select_related('user', 'reviewed_by').order_by('-created_at')
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return Response({'code': 0, 'data': {'items': GroupJoinRequestSerializer(qs, many=True).data, 'total': qs.count()}})

    if group.visibility != 'APPROVAL':
        return Response({'code': 4001, 'message': '当前群组不支持申请加入'}, status=400)
    if _is_group_member(request.user, group):
        return Response({'code': 4090, 'message': '你已在群内'}, status=409)
    if GroupJoinRequest.objects.filter(group=group, user=request.user, status='PENDING').exists():
        return Response({'code': 4090, 'message': '已提交申请'}, status=409)
    req = GroupJoinRequest.objects.create(
        group=group, user=request.user, status='PENDING', message=request.data.get('message', '')
    )
    return Response({'code': 0, 'data': GroupJoinRequestSerializer(req).data, 'message': '申请已提交'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def group_join_request_review(request, group_id: int, request_id: int):
    group = get_object_or_404(Group, pk=group_id, status='ACTIVE')
    if group.visibility != 'APPROVAL':
        return Response({'code': 4001, 'message': '当前群组无需审核申请'}, status=400)
    if not _is_group_reviewer(request.user, group):
        return Response({'code': 4030, 'message': '无权限审核'}, status=403)
    req = get_object_or_404(GroupJoinRequest, pk=request_id, group=group)
    if req.status != 'PENDING':
        return Response({'code': 4001, 'message': '申请状态不可审核'}, status=400)
    action = request.data.get('action')
    if action not in ['APPROVE', 'REJECT']:
        return Response({'code': 4001, 'message': '无效操作'}, status=400)
    req.reviewed_by = request.user
    req.review_note = request.data.get('reviewNote', '')
    req.reviewed_at = timezone.now()
    if action == 'APPROVE':
        req.status = 'APPROVED'
        _activate_member(group, req.user)
    else:
        req.status = 'REJECTED'
    req.save(update_fields=['status', 'reviewed_by', 'review_note', 'reviewed_at'])
    return Response({'code': 0, 'message': '审核完成'})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def group_reviewers(request, group_id: int):
    group = get_object_or_404(Group, pk=group_id, status='ACTIVE')
    if request.method == 'GET':
        if not _is_group_reviewer(request.user, group):
            return Response({'code': 4030, 'message': '无权限查看审核人列表'}, status=403)
        qs = GroupReviewer.objects.filter(group=group).select_related('user').order_by('-created_at')
        return Response({'code': 0, 'data': {'items': GroupReviewerSerializer(qs, many=True).data, 'total': qs.count()}})

    if not _is_group_owner(request.user, group):
        return Response({'code': 4030, 'message': '仅群主可设置审核人'}, status=403)
    if group.visibility != 'APPROVAL':
        return Response({'code': 4001, 'message': '仅审核加入群可设置审核人'}, status=400)
    user_id = request.data.get('userId')
    if not user_id:
        return Response({'code': 4001, 'message': 'userId 必填'}, status=400)
    member = GroupMember.objects.filter(group=group, user_id=user_id, status='ACTIVE').first()
    if not member:
        return Response({'code': 4040, 'message': '目标成员不在群内'}, status=404)
    reviewer, created = GroupReviewer.objects.get_or_create(group=group, user_id=user_id)
    if not created:
        return Response({'code': 4090, 'message': '该成员已是审核人'}, status=409)
    return Response({'code': 0, 'data': GroupReviewerSerializer(reviewer).data, 'message': '设置成功'}, status=201)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def group_reviewer_delete(request, group_id: int, user_id: int):
    group = get_object_or_404(Group, pk=group_id, status='ACTIVE')
    if not _is_group_owner(request.user, group):
        return Response({'code': 4030, 'message': '仅群主可移除审核人'}, status=403)
    if group.visibility != 'APPROVAL':
        return Response({'code': 4001, 'message': '仅审核加入群可设置审核人'}, status=400)
    if user_id == group.owner_id:
        return Response({'code': 4001, 'message': '群主审核权限不可移除'}, status=400)
    reviewer = GroupReviewer.objects.filter(group=group, user_id=user_id).first()
    if not reviewer:
        return Response({'code': 4040, 'message': '审核人不存在'}, status=404)
    reviewer.delete()
    return Response({'code': 0, 'message': '移除成功'})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def group_invites(request, group_id: int):
    group = get_object_or_404(Group, pk=group_id, status='ACTIVE')
    if group.visibility != 'PRIVATE':
        return Response({'code': 4001, 'message': '仅私密群支持邀请'}, status=400)

    if request.method == 'GET':
        if not _is_group_owner(request.user, group):
            return Response({'code': 4030, 'message': '仅群主可查看邀请列表'}, status=403)
        qs = GroupInvite.objects.filter(group=group).select_related('inviter', 'invitee').order_by('-created_at')
        return Response({'code': 0, 'data': {'items': GroupInviteSerializer(qs, many=True).data, 'total': qs.count()}})

    if not _is_group_owner(request.user, group):
        return Response({'code': 4030, 'message': '仅群主可发起邀请'}, status=403)
    invitee_id = request.data.get('inviteeId')
    if not invitee_id:
        return Response({'code': 4001, 'message': 'inviteeId 必填'}, status=400)
    if not User.objects.filter(pk=invitee_id).exists():
        return Response({'code': 4040, 'message': '被邀请用户不存在'}, status=404)
    if int(invitee_id) == request.user.id:
        return Response({'code': 4001, 'message': '不能邀请自己'}, status=400)
    if GroupMember.objects.filter(group=group, user_id=invitee_id, status='ACTIVE').exists():
        return Response({'code': 4090, 'message': '该用户已在群内'}, status=409)
    if GroupInvite.objects.filter(group=group, invitee_id=invitee_id, status='PENDING').exists():
        return Response({'code': 4090, 'message': '该用户已有待处理邀请'}, status=409)
    invite = GroupInvite.objects.create(
        group=group,
        inviter=request.user,
        invitee_id=invitee_id,
        status='PENDING',
        message=request.data.get('message', ''),
    )
    return Response({'code': 0, 'data': GroupInviteSerializer(invite).data, 'message': '邀请已发送'}, status=201)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def group_invite_respond(request, group_id: int, invite_id: int):
    group = get_object_or_404(Group, pk=group_id, status='ACTIVE')
    invite = get_object_or_404(GroupInvite, pk=invite_id, group=group)
    if invite.invitee_id != request.user.id:
        return Response({'code': 4030, 'message': '仅被邀请人可操作'}, status=403)
    if invite.status != 'PENDING':
        return Response({'code': 4001, 'message': '邀请状态不可操作'}, status=400)

    action = request.data.get('action')
    if action not in ['ACCEPT', 'REJECT']:
        return Response({'code': 4001, 'message': '无效操作'}, status=400)

    invite.responded_at = timezone.now()
    if action == 'ACCEPT':
        _activate_member(group, request.user)
        invite.status = 'ACCEPTED'
        message = '已加入群组'
    else:
        invite.status = 'REJECTED'
        message = '已拒绝邀请'
    invite.save(update_fields=['status', 'responded_at', 'updated_at'])
    return Response({'code': 0, 'message': message})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_group_invites(request):
    qs = GroupInvite.objects.filter(invitee=request.user).select_related('group', 'inviter', 'invitee').order_by('-created_at')
    status_filter = request.query_params.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter)
    return Response({'code': 0, 'data': {'items': GroupInviteSerializer(qs, many=True).data, 'total': qs.count()}})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def group_posts(request, group_id: int):
    group = get_object_or_404(Group, pk=group_id, status='ACTIVE')
    perm_error = _ensure_group_can_view(request.user, group)
    if perm_error:
        return perm_error

    if request.method == 'GET':
        if not _can_access_group_content(request.user, group):
            return _content_access_denied_response(request.user, group, '讨论')
        qs = GroupPost.objects.filter(group=group, status='PUBLISHED').select_related('author').order_by('-created_at')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('pageSize', 20))
        total = qs.count()
        start = (page - 1) * page_size
        items = qs[start:start + page_size]
        data = GroupPostSerializer(items, many=True).data
        return Response({'code': 0, 'data': {'items': data, 'page': page, 'pageSize': page_size, 'total': total}})

    if not _is_group_member(request.user, group):
        return Response({'code': 4030, 'message': '仅群成员可发布群讨论'}, status=403)
    serializer = GroupPostCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'code': 4001, 'message': '发布失败', 'errors': serializer.errors}, status=400)
    post = serializer.save(group=group, author=request.user, status='PUBLISHED')
    Group.objects.filter(pk=group.pk).update(post_count=F('post_count') + 1)
    return Response({'code': 0, 'data': GroupPostSerializer(post).data}, status=201)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def group_files(request, group_id: int):
    group = get_object_or_404(Group, pk=group_id, status='ACTIVE')
    perm_error = _ensure_group_can_view(request.user, group)
    if perm_error:
        return perm_error

    if request.method == 'GET':
        if not _can_access_group_content(request.user, group):
            return _content_access_denied_response(request.user, group, '资料')
        qs = GroupFile.objects.filter(group=group, status='ACTIVE').select_related('uploaded_by').order_by('-created_at')
        return Response({'code': 0, 'data': {'items': GroupFileSerializer(qs, many=True, context={'request': request}).data, 'total': qs.count()}})

    if not _is_group_member(request.user, group):
        return Response({'code': 4030, 'message': '仅群成员可上传群资料'}, status=403)
    upload = request.FILES.get('file')
    if not upload:
        return Response({'code': 4001, 'message': '缺少文件'}, status=400)
    ext = os.path.splitext(upload.name)[1].lower()
    allowed = {'.pdf', '.xls', '.xlsx', '.csv', '.png', '.jpg', '.jpeg', '.webp', '.doc', '.docx'}
    if ext not in allowed:
        return Response({'code': 4001, 'message': '不支持的文件类型'}, status=400)
    item = GroupFile.objects.create(
        group=group,
        uploaded_by=request.user,
        file=upload,
        original_name=upload.name,
        mime_type=getattr(upload, 'content_type', '') or '',
        file_size=getattr(upload, 'size', 0) or 0,
        status='ACTIVE',
    )
    Group.objects.filter(pk=group.pk).update(file_count=F('file_count') + 1)
    return Response({'code': 0, 'data': GroupFileSerializer(item, context={'request': request}).data}, status=201)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def group_file_delete(request, group_id: int, file_id: int):
    group = get_object_or_404(Group, pk=group_id, status='ACTIVE')
    file_obj = get_object_or_404(GroupFile, pk=file_id, group=group, status='ACTIVE')
    is_admin = _is_group_admin(request.user, group)
    if file_obj.uploaded_by_id != request.user.id and not is_admin:
        return Response({'code': 4030, 'message': '无权限删除资料'}, status=403)
    file_obj.status = 'DELETED'
    file_obj.save(update_fields=['status', 'updated_at'])
    Group.objects.filter(pk=group.pk, file_count__gt=0).update(file_count=F('file_count') - 1)
    return Response({'code': 0, 'message': '删除成功'})
