from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Report, Alert, ModerationRule, ModerationQueueItem, ModerationHit,
    CommunityMetricDaily, TopicMetricDaily,
)

User = get_user_model()


class ReportCreateSerializer(serializers.ModelSerializer):
    """举报创建序列化器"""
    reportTypeDetail = serializers.CharField(
        source='report_type_detail',
        required=False,
        allow_blank=True
    )
    evidence = serializers.JSONField(
        source='evidence_json',
        required=False
    )

    class Meta:
        model = Report
        fields = ['target_type', 'target_id', 'reason', 'reportTypeDetail', 'evidence']

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
        elif target_type == 'PORTFOLIO':
            from portfolios.models import Portfolio
            if not Portfolio.objects.filter(id=target_id).exists():
                raise serializers.ValidationError("组合不存在")
        
        return attrs

    def create(self, validated_data):
        validated_data['reporter'] = self.context['request'].user
        return Report.objects.create(**validated_data)


class ReportListSerializer(serializers.ModelSerializer):
    """举报列表序列化器"""
    reporterName = serializers.CharField(source='reporter.username', read_only=True)
    handledByName = serializers.CharField(source='handled_by.username', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    handleTime = serializers.DateTimeField(source='handle_time', read_only=True)
    reportTypeDetail = serializers.CharField(source='report_type_detail', read_only=True)
    priority = serializers.IntegerField(read_only=True)
    result = serializers.CharField(read_only=True)

    class Meta:
        model = Report
        fields = [
            'id',
            'reporterName',
            'target_type', 'target_id',
            'reason', 'status',
            'reportTypeDetail', 'priority',
            'handledByName', 'handle_result', 'result',
            'createdAt', 'handleTime',
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


class ModerationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModerationRule
        fields = [
            'id', 'name', 'rule_type', 'pattern', 'config_json',
            'risk_level', 'risk_score', 'action', 'is_active',
            'created_at', 'updated_at',
        ]


class ModerationQueueItemSerializer(serializers.ModelSerializer):
    content_title = serializers.CharField(source='content.title', read_only=True)
    content_id = serializers.IntegerField(source='content.id', read_only=True)
    decided_by_name = serializers.CharField(source='decided_by.display_name', read_only=True)

    class Meta:
        model = ModerationQueueItem
        fields = [
            'id', 'content_id', 'content_title', 'source', 'risk_level', 'risk_score',
            'reason_summary', 'status', 'decided_status', 'decided_by_name',
            'decided_at', 'created_at',
        ]


class ModerationHitSerializer(serializers.ModelSerializer):
    content_title = serializers.CharField(source='content.title', read_only=True)
    user_name = serializers.CharField(source='user.display_name', read_only=True)
    rule_name = serializers.CharField(source='rule.name', read_only=True)

    class Meta:
        model = ModerationHit
        fields = [
            'id', 'rule_name', 'content', 'content_title', 'user', 'user_name',
            'hit_text', 'evidence_json', 'risk_score', 'risk_level', 'created_at',
        ]


class CommunityMetricDailySerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityMetricDaily
        fields = [
            'stat_date', 'dau', 'post_count', 'comment_count', 'report_count',
            'review_pass_rate', 'taken_down_count',
        ]


class TopicMetricDailySerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicMetricDaily
        fields = [
            'stat_date', 'topic', 'post_count', 'comment_count', 'like_count', 'heat_score',
        ]