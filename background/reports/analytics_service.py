from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from django.db.models import Count, Sum, Q
from django.utils import timezone

from accounts.models import User, UserBehaviorDaily, LevelRule
from content.models import Content, Comment
from reports.models import Report, CommunityMetricDaily, TopicMetricDaily


def rebuild_behavior_daily(days: int = 30):
    today = timezone.now().date()
    start = today - timedelta(days=days - 1)
    for i in range(days):
        day = start + timedelta(days=i)
        next_day = day + timedelta(days=1)
        posts = (
            Content.objects.filter(created_at__date=day)
            .values('author_id')
            .annotate(
                post_count=Count('id'),
                taken_down_count=Count('id', filter=Q(status__in=['REJECTED', 'TAKEN_DOWN'])),
                received_likes=Sum('like_count'),
            )
        )
        comments = (
            Comment.objects.filter(created_at__date=day)
            .values('author_id')
            .annotate(comment_count=Count('id'))
        )
        reports = (
            Report.objects.filter(created_at__date=day, target_type='POST')
            .values('target_id')
            .annotate(reported_count=Count('id'))
        )
        report_content_ids = [x['target_id'] for x in reports]
        author_by_content = dict(Content.objects.filter(id__in=report_content_ids).values_list('id', 'author_id'))

        stats_map = defaultdict(lambda: {
            'post_count': 0, 'comment_count': 0, 'reported_count': 0,
            'violation_count': 0, 'received_likes': 0, 'taken_down_count': 0,
            'quality_score': 0,
        })
        for row in posts:
            x = stats_map[row['author_id']]
            x['post_count'] = row['post_count']
            x['taken_down_count'] = row['taken_down_count'] or 0
            x['received_likes'] = row['received_likes'] or 0
        for row in comments:
            stats_map[row['author_id']]['comment_count'] = row['comment_count']
        for row in reports:
            author_id = author_by_content.get(row['target_id'])
            if author_id:
                stats_map[author_id]['reported_count'] += row['reported_count']

        for user_id, payload in stats_map.items():
            violation_count = payload['taken_down_count']
            payload['violation_count'] = violation_count
            payload['quality_score'] = max(
                0,
                100 - violation_count * 15 - payload['reported_count'] * 5 + min(payload['received_likes'], 20),
            )
            UserBehaviorDaily.objects.update_or_create(
                user_id=user_id,
                stat_date=day,
                defaults=payload,
            )


def rebuild_community_metrics(days: int = 30):
    today = timezone.now().date()
    start = today - timedelta(days=days - 1)
    for i in range(days):
        day = start + timedelta(days=i)
        post_qs = Content.objects.filter(created_at__date=day)
        reviewed = Content.objects.filter(updated_at__date=day, status__in=['PUBLISHED', 'REJECTED', 'TAKEN_DOWN'])
        pass_count = reviewed.filter(status='PUBLISHED').count()
        total_reviewed = reviewed.count()
        review_pass_rate = round((pass_count / total_reviewed) * 100, 2) if total_reviewed else 0
        CommunityMetricDaily.objects.update_or_create(
            stat_date=day,
            defaults={
                'dau': User.objects.filter(updated_at__date=day).count(),
                'post_count': post_qs.count(),
                'comment_count': Comment.objects.filter(created_at__date=day).count(),
                'report_count': Report.objects.filter(created_at__date=day).count(),
                'review_pass_rate': review_pass_rate,
                'taken_down_count': post_qs.filter(status__in=['REJECTED', 'TAKEN_DOWN']).count(),
            }
        )


def refresh_topic_metrics(days: int = 30, top_n: int = 50):
    today = timezone.now().date()
    start = today - timedelta(days=days - 1)
    TopicMetricDaily.objects.filter(stat_date__gte=start).delete()
    for i in range(days):
        day = start + timedelta(days=i)
        posts = Content.objects.filter(created_at__date=day).values('tags_json', 'like_count', 'comment_count')
        topic_stat = defaultdict(lambda: {'post_count': 0, 'comment_count': 0, 'like_count': 0})
        for row in posts:
            tags = row.get('tags_json') or []
            for tag in tags[:5]:
                topic_stat[tag]['post_count'] += 1
                topic_stat[tag]['comment_count'] += row.get('comment_count', 0) or 0
                topic_stat[tag]['like_count'] += row.get('like_count', 0) or 0
        sorted_topics = sorted(
            topic_stat.items(),
            key=lambda x: x[1]['post_count'] * 5 + x[1]['comment_count'] * 3 + x[1]['like_count'] * 2,
            reverse=True,
        )[:top_n]
        for topic, payload in sorted_topics:
            heat = payload['post_count'] * 5 + payload['comment_count'] * 3 + payload['like_count'] * 2
            TopicMetricDaily.objects.create(
                stat_date=day,
                topic=topic,
                post_count=payload['post_count'],
                comment_count=payload['comment_count'],
                like_count=payload['like_count'],
                heat_score=heat,
            )


def rebuild_user_levels():
    rules = LevelRule.objects.filter(is_active=True).order_by('level')
    for user in User.objects.all().only('id', 'points', 'level'):
        next_level = user.level
        for rule in rules:
            if rule.min_points <= user.points <= rule.max_points:
                next_level = rule.level
                break
        if user.level != next_level:
            user.level = next_level
            user.save(update_fields=['level', 'updated_at'])
