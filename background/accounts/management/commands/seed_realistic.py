from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from accounts.seed_realistic import (
    apply_seed_merge,
    apply_seed_orm,
    load_seed_json,
    render_fixed_mysql,
)


class Command(BaseCommand):
    help = (
        "加载 .cursor/rules/realistic_seed_data.json 高仿真种子。"
        "使用 --write-fixed-sql 生成与当前模型一致的 SQL；"
        "使用 --orm 固定 ID 写入（仅适合空库）；"
        "使用 --merge 合并到现有库（保留已有数据，见 README）。"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--json",
            type=str,
            default=None,
            help="JSON 路径，默认 BASE_DIR/.cursor/rules/realistic_seed_data.json",
        )
        parser.add_argument(
            "--write-fixed-sql",
            action="store_true",
            help="写入 background/.cursor/rules/realistic_seed_data_inserts_fixed.sql",
        )
        parser.add_argument(
            "--orm",
            action="store_true",
            help="通过 Django ORM 导入固定 ID 种子（仅适合空库/已清空相关表）",
        )
        parser.add_argument(
            "--merge",
            action="store_true",
            help="合并导入：匹配已有用户/标的，新增帖子与关联（保留 community_db 原有数据）",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="仅加载 JSON 并生成 SQL 字符串到内存，不写库、不写文件",
        )
        parser.add_argument(
            "--print-sql",
            action="store_true",
            help="将生成的固定 SQL 打印到 stdout",
        )

    def handle(self, *args, **options):
        path = Path(options["json"]) if options.get("json") else None
        try:
            data = load_seed_json(path)
        except FileNotFoundError as e:
            raise CommandError(f"找不到种子 JSON: {e}") from e

        if options["dry_run"]:
            render_fixed_mysql(data)
            self.stdout.write(self.style.SUCCESS("dry-run: JSON 解析与 SQL 生成逻辑执行成功"))
            return

        if options["write_fixed_sql"]:
            out = Path(settings.BASE_DIR) / ".cursor" / "rules" / "realistic_seed_data_inserts_fixed.sql"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(render_fixed_mysql(data), encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"已写入 {out}"))
            return

        if options["print_sql"]:
            self.stdout.write(render_fixed_mysql(data))
            return

        if options["orm"] and options["merge"]:
            raise CommandError("--orm 与 --merge 互斥，请只选其一")

        if options["merge"]:
            stats = apply_seed_merge(data)
            self.stdout.write(
                self.style.SUCCESS(
                    "合并导入完成："
                    f"新建用户 {stats['users_created']}，匹配已有用户 {stats['users_matched']}；"
                    f"新建标的 {stats['assets_created']}，匹配已有标的 {stats['assets_matched']}；"
                    f"新建帖子 {stats['contents_created']}，新建评论 {stats['comments_created']}；"
                    f"跳过已存在持仓 {stats['holdings_skipped_existing']} 条。"
                )
            )
            return

        if options["orm"]:
            apply_seed_orm(data)
            self.stdout.write(self.style.SUCCESS("ORM 种子导入完成"))
            return

        raise CommandError("请指定 --write-fixed-sql、--orm、--merge、--dry-run 或 --print-sql 之一")
