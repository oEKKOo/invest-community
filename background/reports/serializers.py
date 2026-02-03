from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Report, Alert

User = get_user_model()


class ReportCreateSerializer(serializers.ModelSerializer):
    """举报创建序列化器"""
    class Meta:
        model = Report
        fields = ['target_type', 'target_id', 'reason']

    def validate(self, attrs):
        target_type = attrs['target_type']
        target_id = attrs['target_id']
        
        # 验证目标是否存在
        if target_type == 'POST':
            from content.models import Content
            if not Content.objects.filter(id=target_id).exists():
                raise serializers.ValidationError("帖子不存在")
        elif target_type == 'COMMENT':
            from content.models import Comment
            if not Comment.objects.filter(id=target_id).exists():
                raise serializers.ValidationError("评论不存在")
        elif target_type == 'USER':
            if not User.objects.filter(id=target_id).exists():
                raise serializers.ValidationError("用户不存在")
        
        return attrs

    def create(self, validated_data):
        validated_data['reporter'] = self.context['request'].user
        return Report.objects.create(**validated_data)


class ReportListSerializer(serializers.ModelSerializer):
    """举报列表序列化器"""
    reporter_name = serializers.CharField(source='reporter.username', read_only=True)
    handled_by_name = serializers.CharField(source='handled_by.username', read_only=True)

    class Meta:
        model = Report
        fields = [
            'id', 'reporter_name', 'target_type', 'target_id',
            'reason', 'status', 'handled_by_name', 'handle_result',
            'created_at', 'handle_time'
        ]


class AlertSerializer(serializers.ModelSerializer):
    """告警序列化器"""
    handled_by_name = serializers.CharField(source='handled_by.username', read_only=True)

    class Meta:
        model = Alert
        fields = [
            'id', 'alert_type', 'title', 'description',
            'related_object_type', 'related_object_id',
            'severity', 'status', 'handled_by_name', 'handle_result',
            'created_at', 'handle_time'
        ]