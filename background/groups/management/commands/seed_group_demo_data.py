import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from content.models import Comment, Content
from groups.models import Group, GroupInvite, GroupJoinRequest, GroupMember, GroupPost, GroupReviewer


User = get_user_model()


class Command(BaseCommand):
    help = "Seed realistic demo group data (10 groups + discussions + related comments)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete previously generated demo group data before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self._reset_demo_data()

        users = self._ensure_demo_users()
        groups = self._ensure_demo_groups(users)
        self._ensure_members(groups, users)
        self._ensure_reviewers(groups)
        self._ensure_join_requests(groups, users)
        self._ensure_invites(groups, users)
        self._ensure_group_posts(groups, users)
        self._ensure_related_contents_and_comments(users)
        self._recount_group_stats(groups)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete: groups={Group.objects.filter(slug__startswith='demo-group-').count()}, "
                f"group_posts={GroupPost.objects.filter(group__slug__startswith='demo-group-').count()}, "
                f"content_comments={Comment.objects.filter(content__title__startswith='[群组话题扩展]').count()}"
            )
        )

    def _reset_demo_data(self):
        Group.objects.filter(slug__startswith="demo-group-").delete()
        Content.objects.filter(title__startswith="[群组话题扩展]").delete()
        User.objects.filter(username__startswith="investor_demo_").delete()

    def _ensure_demo_users(self):
        users = []
        for i in range(1, 13):
            username = f"investor_demo_{i:02d}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@example.com",
                    "display_name": f"投资者{i:02d}号",
                    "role": "USER",
                    "status": "NORMAL",
                },
            )
            if created:
                user.set_password("Demo123456!")
                user.save(update_fields=["password"])
            users.append(user)
        return users

    def _ensure_demo_groups(self, users):
        group_specs = [
            ("A股价值投资研讨群", "围绕低估值蓝筹、股息策略与行业轮动进行长期研究。", "PUBLIC", "价值投资"),
            ("ETF轮动实战小组", "讨论宽基/行业ETF轮动信号与仓位管理。", "PUBLIC", "ETF轮动"),
            ("港美成长股跟踪营", "聚焦港股互联网与美股科技成长标的。", "APPROVAL", "成长股"),
            ("基金定投复盘会", "每周复盘定投组合，分享止盈与再平衡经验。", "PUBLIC", "基金定投"),
            ("可转债策略交流群", "覆盖低溢价、双低策略与打新节奏。", "APPROVAL", "可转债"),
            ("红利低波组合研究", "偏稳健风格，关注红利ETF和高股息资产。", "PRIVATE", "红利低波"),
            ("行业景气度观察站", "从宏观与产业链角度跟踪行业景气拐点。", "PUBLIC", "行业研究"),
            ("量化信号共创群", "分享技术指标、择时框架与回测心得。", "APPROVAL", "量化择时"),
            ("新手避坑与风控互助", "面向新手，强调风险管理与仓位纪律。", "PUBLIC", "风险控制"),
            ("FOF资产配置圆桌", "围绕股债商品多资产配置展开讨论。", "PRIVATE", "资产配置"),
        ]

        groups = []
        for idx, (name, desc, visibility, topic) in enumerate(group_specs, start=1):
            owner = users[(idx - 1) % len(users)]
            group, _ = Group.objects.update_or_create(
                slug=f"demo-group-{idx:02d}",
                defaults={
                    "name": name,
                    "description": desc,
                    "visibility": visibility,
                    "topic_direction": topic,
                    "tags_json": [topic, "实盘复盘", "风险控制"],
                    "owner": owner,
                    "status": "ACTIVE",
                },
            )
            groups.append(group)
        return groups

    def _ensure_members(self, groups, users):
        for idx, group in enumerate(groups):
            owner = group.owner
            GroupMember.objects.update_or_create(
                group=group,
                user=owner,
                defaults={"role": "OWNER", "status": "ACTIVE", "left_at": None},
            )

            candidates = [u for u in users if u.id != owner.id]
            random.shuffle(candidates)
            chosen = candidates[: random.randint(4, 8)]

            for member_idx, member_user in enumerate(chosen):
                role = "ADMIN" if member_idx == 0 else "MEMBER"
                GroupMember.objects.update_or_create(
                    group=group,
                    user=member_user,
                    defaults={
                        "role": role,
                        "status": "ACTIVE",
                        "joined_at": timezone.now() - timedelta(days=random.randint(1, 60)),
                        "left_at": None,
                    },
                )

    def _ensure_reviewers(self, groups):
        for group in groups:
            if group.visibility != "APPROVAL":
                continue
            GroupReviewer.objects.get_or_create(group=group, user=group.owner)
            admin_member = GroupMember.objects.filter(group=group, role="ADMIN", status="ACTIVE").first()
            if admin_member:
                GroupReviewer.objects.get_or_create(group=group, user=admin_member.user)

    def _ensure_join_requests(self, groups, users):
        for group in groups:
            if group.visibility != "APPROVAL":
                continue

            member_ids = set(GroupMember.objects.filter(group=group).values_list("user_id", flat=True))
            available = [u for u in users if u.id not in member_ids]
            if not available:
                continue

            requester = random.choice(available)
            req, _ = GroupJoinRequest.objects.update_or_create(
                group=group,
                user=requester,
                defaults={
                    "status": random.choice(["PENDING", "APPROVED", "REJECTED"]),
                    "message": "希望加入群组学习策略框架，并参与每周复盘。",
                    "review_note": "历史发言质量良好，可纳入观察。",
                    "reviewed_by": group.owner,
                    "created_at": timezone.now() - timedelta(days=random.randint(1, 20)),
                    "reviewed_at": timezone.now() - timedelta(days=random.randint(0, 10)),
                },
            )
            if req.status == "APPROVED":
                GroupMember.objects.update_or_create(
                    group=group,
                    user=requester,
                    defaults={"role": "MEMBER", "status": "ACTIVE", "left_at": None},
                )

    def _ensure_invites(self, groups, users):
        private_groups = [g for g in groups if g.visibility == "PRIVATE"]
        for group in private_groups:
            member_ids = set(GroupMember.objects.filter(group=group).values_list("user_id", flat=True))
            candidates = [u for u in users if u.id not in member_ids and u.id != group.owner_id]
            if not candidates:
                continue
            invitee = random.choice(candidates)
            GroupInvite.objects.update_or_create(
                group=group,
                invitee=invitee,
                defaults={
                    "inviter": group.owner,
                    "status": random.choice(["PENDING", "ACCEPTED", "REJECTED"]),
                    "message": "我们在做同主题研究，欢迎加入一起跟踪组合表现。",
                    "created_at": timezone.now() - timedelta(days=random.randint(1, 15)),
                },
            )

    def _ensure_group_posts(self, groups, users):
        titles = [
            "本周策略复盘：仓位如何调整更稳健",
            "下周观察池：3个值得跟踪的板块",
            "组合回撤控制：止损与分批买入实践",
            "市场分歧加大，如何做风格平衡",
            "月度总结：收益来源与失误复盘",
        ]
        bodies = [
            "本周我们把高波动仓位从35%降到20%，并增加红利资产对冲波动，组合净值回撤明显收敛。",
            "结合资金流与估值分位，当前更偏向防御+景气共振方向，建议避免单一赛道重仓。",
            "建议把策略拆成入场、加仓、减仓三个阶段，每个阶段写清触发条件，执行更稳定。",
            "短期情绪可能反复，保持分散与纪律更关键，关注成交量变化和板块轮动节奏。",
            "这次复盘最大的收获是仓位纪律比择时更重要，尤其在震荡行情下。",
        ]

        for group in groups:
            active_members = list(
                GroupMember.objects.filter(group=group, status="ACTIVE").select_related("user")
            )
            if not active_members:
                continue
            for i in range(3):
                author = random.choice(active_members).user
                GroupPost.objects.get_or_create(
                    group=group,
                    author=author,
                    title=f"{titles[(i + group.id) % len(titles)]} #{i + 1}",
                    defaults={
                        "body": bodies[(i + group.id) % len(bodies)],
                        "content_type": "NORMAL",
                        "status": "PUBLISHED",
                        "like_count": random.randint(3, 45),
                        "comment_count": random.randint(1, 16),
                        "created_at": timezone.now() - timedelta(days=random.randint(0, 12)),
                    },
                )

    def _ensure_related_contents_and_comments(self, users):
        content_specs = [
            "【群组话题扩展】ETF轮动里如何规避追高",
            "【群组话题扩展】红利策略在震荡市的表现复盘",
            "【群组话题扩展】新手如何建立第一套仓位纪律",
            "【群组话题扩展】成长股仓位与止盈节奏讨论",
            "【群组话题扩展】FOF配置中权益仓位动态调整",
        ]
        comment_pool = [
            "这条思路很实用，特别是仓位上限的限制，对控制回撤有帮助。",
            "我补充一个点：可以把止盈分成两档执行，避免一次性卖飞。",
            "实盘里最大的难点是执行一致性，建议做周度复盘记录。",
            "赞同，建议再加一个情绪指标过滤，能减少无效交易。",
            "这个方法我上个月试过，效果不错，回撤明显更可控。",
        ]

        for idx, title in enumerate(content_specs):
            author = users[idx % len(users)]
            content, _ = Content.objects.update_or_create(
                title=title,
                defaults={
                    "author": author,
                    "body": "该话题源于群组讨论整理，重点在于形成可执行的投资决策流程。",
                    "status": "PUBLISHED",
                    "tags_json": ["群组扩展", "策略复盘", "风控"],
                    "published_at": timezone.now() - timedelta(days=idx + 1),
                },
            )

            existing = Comment.objects.filter(content=content).count()
            if existing >= 3:
                continue

            root_author = users[(idx + 2) % len(users)]
            root = Comment.objects.create(
                content=content,
                author=root_author,
                body=comment_pool[idx % len(comment_pool)],
                status="NORMAL",
            )
            Comment.objects.create(
                content=content,
                author=users[(idx + 3) % len(users)],
                parent=root,
                reply_to_user=root_author,
                body=comment_pool[(idx + 1) % len(comment_pool)],
                status="NORMAL",
            )
            Comment.objects.create(
                content=content,
                author=users[(idx + 4) % len(users)],
                body=comment_pool[(idx + 2) % len(comment_pool)],
                status="NORMAL",
            )
            content.comment_count = Comment.objects.filter(content=content, status="NORMAL").count()
            content.save(update_fields=["comment_count", "updated_at"])

    def _recount_group_stats(self, groups):
        for group in groups:
            member_count = GroupMember.objects.filter(group=group, status="ACTIVE").count()
            post_count = GroupPost.objects.filter(group=group, status="PUBLISHED").count()
            Group.objects.filter(pk=group.pk).update(member_count=member_count, post_count=post_count)
