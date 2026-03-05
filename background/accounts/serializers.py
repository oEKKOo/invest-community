from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, UserInvestProfile, UserFollow


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
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
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


class UserProfileSerializer(serializers.ModelSerializer):
    """用户个人资料序列化器"""
    displayName = serializers.CharField(source='display_name')
    avatar = serializers.URLField(source='avatar_url')
    followers = serializers.IntegerField(source='followers_count', read_only=True)
    following = serializers.IntegerField(source='following_count', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'displayName', 
            'avatar', 'bio', 'role', 'status',
            'followers', 'following', 'created_at'
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