from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import User, UserInvestProfile, UserFollow
from .serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer, 
    UserProfileSerializer,
    UserInvestProfileSerializer,
    UserPublicSerializer,
    UserFollowSerializer
)

User = get_user_model()


def get_tokens_for_user(user):
    """为用户生成JWT token"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


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
        tokens = get_tokens_for_user(user)
        return Response({
            'code': 0,
            'data': {
                'access': tokens['access'],
                'refresh': tokens['refresh'],
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'displayName': user.display_name,
                    'role': user.role
                }
            }
        })
    return Response({
        'code': 4001,
        'message': '登录失败',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """获取当前用户信息"""
    serializer = UserProfileSerializer(request.user)
    return Response({
        'code': 0,
        'data': serializer.data
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


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """更新用户资料"""
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def follow_user(request, user_id):
    """关注用户"""
    target_user = get_object_or_404(User, id=user_id)
    
    if target_user == request.user:
        return Response({
            'code': 4001,
            'message': '不能关注自己'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    with transaction.atomic():
        follow, created = UserFollow.objects.get_or_create(
            follower=request.user,
            followee=target_user
        )
        
        if created:
            # 更新关注数和粉丝数
            request.user.following_count += 1
            target_user.followers_count += 1
            request.user.save(update_fields=['following_count'])
            target_user.save(update_fields=['followers_count'])
            
            return Response({
                'code': 0,
                'message': '关注成功'
            })
        else:
            return Response({
                'code': 4090,
                'message': '已经关注过了'
            }, status=status.HTTP_409_CONFLICT)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def unfollow_user(request, user_id):
    """取消关注用户"""
    target_user = get_object_or_404(User, id=user_id)
    
    try:
        follow = UserFollow.objects.get(follower=request.user, followee=target_user)
        with transaction.atomic():
            follow.delete()
            # 更新关注数和粉丝数
            request.user.following_count = max(0, request.user.following_count - 1)
            target_user.followers_count = max(0, target_user.followers_count - 1)
            request.user.save(update_fields=['following_count'])
            target_user.save(update_fields=['followers_count'])
        
        return Response({
            'code': 0,
            'message': '取消关注成功'
        })
    except UserFollow.DoesNotExist:
        return Response({
            'code': 4040,
            'message': '没有关注过该用户'
        }, status=status.HTTP_404_NOT_FOUND)


class UserFollowersView(generics.ListAPIView):
    """用户粉丝列表"""
    serializer_class = UserFollowSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return UserFollow.objects.filter(followee_id=user_id).select_related('follower')


class UserFollowingView(generics.ListAPIView):
    """用户关注列表"""
    serializer_class = UserFollowSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return UserFollow.objects.filter(follower_id=user_id).select_related('followee')


@api_view(['POST'])
@permission_classes([IsAuthenticated])  
def logout(request):
    """用户登出（可选实现）"""
    # 这里可以实现token黑名单逻辑
    # 目前前端清除token即可
    return Response({
        'code': 0,
        'message': '登出成功'
    })


class UserFavoritesView(generics.ListAPIView):
    """用户收藏列表"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        from content.models import Favorite
        from content.serializers import ContentListSerializer
        
        favorites = Favorite.objects.filter(user=request.user).select_related('content')
        contents = [fav.content for fav in favorites]
        
        serializer = ContentListSerializer(contents, many=True, context={'request': request})
        return Response({
            'code': 0,
            'data': {
                'items': serializer.data,
                'total': len(contents)
            }
        })


class UserReportsView(generics.ListAPIView):
    """用户举报列表"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        from reports.models import Report
        from reports.serializers import ReportListSerializer
        
        reports = Report.objects.filter(reporter=request.user).order_by('-created_at')
        serializer = ReportListSerializer(reports, many=True)
        
        return Response({
            'code': 0,
            'data': {
                'items': serializer.data,
                'total': reports.count()
            }
        })