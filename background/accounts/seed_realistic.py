"""
从 realistic_seed_data.json 映射到当前 Django 模型，并生成与 migrate 一致的 MySQL INSERT。
映射规则见 .cursor/rules/realistic_seed_data_README.md。
"""
from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.conf import settings

DEFAULT_JSON = Path(settings.BASE_DIR) / ".cursor" / "rules" / "realistic_seed_data.json"

# 与 realistic_seed_data_inserts.sql 注释一致：123456Aa!
SEED_PASSWORD_HASH = (
    "pbkdf2_sha256$870000$seed2026demo$Am5lEOKV7sy4zCXG6V0uuM8XkOCJC3mdPzrNbfQquXY="
)


def load_seed_json(path: Path | None = None) -> dict[str, Any]:
    p = path or DEFAULT_JSON
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def map_identity_level(raw: str) -> str:
    if raw == "ADVANCED":
        return "REAL_NAME"
    valid = {"UNVERIFIED", "BASIC", "REAL_NAME", "PROFESSIONAL"}
    return raw if raw in valid else "UNVERIFIED"


def map_verification_status(raw: str | None) -> str:
    if raw in ("VERIFIED", "DONE"):
        return "APPROVED"
    valid = {"NONE", "PENDING", "APPROVED", "REJECTED"}
    return raw if raw in valid else "NONE"


def map_json_risk_to_user_risk(raw: str | None) -> str | None:
    """JSON 的 LOW/MEDIUM/HIGH -> User.risk_level R1-R5。"""
    m = {"LOW": "R2", "MEDIUM": "R3", "HIGH": "R4"}
    if not raw:
        return None
    return m.get(raw, "R3")


def map_invest_risk_int(raw: str) -> int:
    m = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
    return m.get(raw, 2)


def map_horizon_int(raw: str) -> int:
    m = {"SHORT": 1, "MID": 2, "LONG": 3}
    return m.get(raw, 2)


def normalize_moderation_source(raw: str) -> str:
    if raw == "AUTO+MANUAL":
        return "MANUAL"
    if raw in ("MANUAL", "AUTO", "REPORT"):
        return raw
    return "MANUAL"


def normalize_asset_type(raw: str) -> str:
    u = raw.upper()
    if u in ("STOCK", "FUND", "ETF", "BOND"):
        return u
    return "STOCK"


def normalize_market(raw: str) -> str:
    if raw == "CN":
        return "SH"
    return raw


def content_meta_kind(raw_content_type: str) -> str:
    return "LONGFORM" if raw_content_type == "ARTICLE" else "NORMAL"


def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    return datetime.fromisoformat(s)


def sql_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "''")


def sql_bool(b: bool) -> str:
    return "1" if b else "0"


def render_fixed_mysql(data: dict[str, Any]) -> str:
    """生成可在已 migrate 的 MySQL 库执行的 INSERT（固定 ID，适合空库或已清空相关表）。"""
    lines: list[str] = [
        "-- realistic_seed_data_inserts_fixed.sql",
        "-- Aligned with Django models (see accounts/seed_realistic.py).",
        "-- Default login password (hashed below): 123456Aa!",
        "SET NAMES utf8mb4;",
        "SET FOREIGN_KEY_CHECKS = 0;",
        "START TRANSACTION;",
        "",
    ]

    # user
    ucols = (
        "`id`, `username`, `display_name`, `email`, `phone`, `password`, `avatar_url`, `bio`, "
        "`investment_experience`, `role`, `status`, `followers_count`, `following_count`, "
        "`points`, `level`, `quality_score`, `risk_level`, `phone_verified`, `email_verified`, "
        "`identity_level`, `real_name_status`, `professional_status`, `risk_assessment_status`, "
        "`v_badge`, `is_active`, `is_staff`, `is_superuser`, `created_at`, `updated_at`"
    )
    urows = []
    for u in data["users"]:
        urows.append(
            "({id}, '{username}', '{display_name}', '{email}', {phone}, '{password}', "
            "{avatar}, '{bio}', '{exp}', '{role}', '{status}', 0, 0, {points}, {level}, {qs}, "
            "{risk_level}, {pv}, {ev}, '{idl}', '{rns}', '{ps}', '{ras}', {vb}, {ia}, {isf}, {isu}, "
            "'{ca}', '{ua}')".format(
                id=u["id"],
                username=sql_escape(u["username"]),
                display_name=sql_escape(u["display_name"]),
                email=sql_escape(u["email"]),
                phone=f"'{sql_escape(u['phone'])}'" if u.get("phone") else "NULL",
                password=SEED_PASSWORD_HASH,
                avatar=f"'{sql_escape(u['avatar_url'])}'" if u.get("avatar_url") else "NULL",
                bio=sql_escape(u.get("bio") or ""),
                exp=sql_escape(u.get("investment_experience") or ""),
                role=u["role"],
                status=u["status"],
                points=u["points"],
                level=u["level"],
                qs=f"{Decimal(str(u['quality_score'])):.2f}",
                risk_level=f"'{map_json_risk_to_user_risk(u.get('risk_level'))}'"
                if map_json_risk_to_user_risk(u.get("risk_level"))
                else "NULL",
                pv=sql_bool(u.get("phone_verified", False)),
                ev=sql_bool(u.get("email_verified", False)),
                idl=map_identity_level(u.get("identity_level") or "UNVERIFIED"),
                rns=map_verification_status(u.get("real_name_status")),
                ps=map_verification_status(u.get("professional_status")),
                ras=map_verification_status(u.get("risk_assessment_status")),
                vb=sql_bool(u.get("v_badge", False)),
                ia=sql_bool(u.get("is_active", True)),
                isf=sql_bool(u.get("is_staff", False)),
                isu=sql_bool(u.get("is_superuser", False)),
                ca=str(parse_dt(u["created_at"]))[:19] if u.get("created_at") else "",
                ua=str(parse_dt(u["updated_at"]))[:19] if u.get("updated_at") else "",
            )
        )
    lines.append(f"INSERT INTO `user` ({ucols}) VALUES\n" + ",\n".join(urows) + ";")
    lines.append("")

    # user_invest_profile (risk_level / horizon 为 1–3 整数，见 UserInvestProfile 模型)
    pcols = "`user_id`, `risk_level`, `horizon`, `focus_market`, `preferred_assets`, `created_at`, `updated_at`"
    pros = []
    for p in data["user_invest_profiles"]:
        fm = sql_escape(json.dumps(p["focus_market"], ensure_ascii=False))
        pa = sql_escape(json.dumps(p["preferred_assets"], ensure_ascii=False))
        ua = str(parse_dt(p["updated_at"]))[:19]
        pros.append(
            f"({p['user_id']}, {map_invest_risk_int(p['risk_level'])}, "
            f"{map_horizon_int(p['horizon'])}, '{fm}', '{pa}', '{ua}', '{ua}')"
        )
    lines.append(f"INSERT INTO `user_invest_profile` ({pcols}) VALUES\n" + ",\n".join(pros) + ";")
    lines.append("")

    # asset
    acols = (
        "`id`, `code`, `name`, `asset_type`, `market`, `status`, `finnhub_symbol`, `exchange`, "
        "`currency`, `isin`, `industry`, `logo_url`, `description`, `meta_json`, `last_sync_at`, `created_at`, `updated_at`"
    )
    arows = []
    now = "2026-03-14 09:00:00"
    for a in data["assets"]:
        fs = a.get("finnhub_symbol")
        fs_sql = f"'{sql_escape(fs)}'" if fs else "NULL"
        at = normalize_asset_type(a["asset_type"])
        mk = normalize_market(a["market"])
        arows.append(
            "({id}, '{code}', '{name}', '{atype}', '{mkt}', 'ACTIVE', {fs}, '{ex}', '{cur}', '', "
            "'{ind}', '', '', '{{}}', NULL, '{now}', '{now}')".format(
                id=a["id"],
                code=sql_escape(a["code"]),
                name=sql_escape(a["name"]),
                atype=at,
                mkt=mk,
                fs=fs_sql,
                ex=sql_escape(a.get("exchange") or ""),
                cur=sql_escape(a.get("currency") or ""),
                ind=sql_escape(a.get("industry") or ""),
                now=now,
            )
        )
    lines.append(f"INSERT INTO `asset` ({acols}) VALUES\n" + ",\n".join(arows) + ";")
    lines.append("")

    # content (no content_type column)
    ccols = (
        "`id`, `author_id`, `title`, `body`, `tags_json`, `status`, `reviewed_by_id`, `reject_reason`, "
        "`risk_score`, `risk_level`, `moderation_source`, `like_count`, `comment_count`, `view_count`, "
        "`created_at`, `updated_at`, `published_at`"
    )
    crows = []
    for c in data["contents"]:
        rb = c.get("reviewed_by")
        rbs = str(rb) if rb else "NULL"
        rr = c.get("reject_reason")
        rrs = f"'{sql_escape(rr)}'" if rr else "NULL"
        pub = c.get("published_at")
        pss = f"'{str(parse_dt(pub))[:19]}'" if pub else "NULL"
        ct = str(parse_dt(c.get("published_at") or "2026-03-14T10:00:00Z"))[:19]
        msrc = normalize_moderation_source(c.get("moderation_source") or "MANUAL")
        tags = sql_escape(json.dumps(c.get("tags_json") or [], ensure_ascii=False))
        crows.append(
            "({id}, {aid}, '{title}', '{body}', '{tags}', '{st}', {rb}, {rr}, {rs}, '{rl}', '{ms}', "
            "{lc}, {cc}, {vc}, '{ct}', '{ct}', {pub})".format(
                id=c["id"],
                aid=c["author_id"],
                title=sql_escape(c["title"]),
                body=sql_escape(c["body"]),
                tags=tags,
                st=c["status"],
                rb=rbs,
                rr=rrs,
                rs=c.get("risk_score", 0),
                rl=c.get("risk_level", "LOW"),
                ms=msrc,
                lc=c.get("like_count", 0),
                cc=c.get("comment_count", 0),
                vc=c.get("view_count", 0),
                ct=ct,
                pub=pss,
            )
        )
    lines.append(f"INSERT INTO `content` ({ccols}) VALUES\n" + ",\n".join(crows) + ";")
    lines.append("")

    # content_meta
    mcols = "`content_id`, `content_type`, `format_type`, `repost_count`, `forward_count`, `created_at`, `updated_at`"
    mrows = []
    for c in data["contents"]:
        ck = content_meta_kind(c.get("content_type") or "POST")
        ts = str(parse_dt(c.get("published_at") or "2026-03-14T10:00:00Z"))[:19]
        mrows.append(f"({c['id']}, '{ck}', 'PLAIN', 0, 0, '{ts}', '{ts}')")
    lines.append(f"INSERT INTO `content_meta` ({mcols}) VALUES\n" + ",\n".join(mrows) + ";")
    lines.append("")

    # content_asset
    cacols = "`id`, `content_id`, `asset_id`, `created_at`"
    ca_rows = []
    for i, ca in enumerate(data["content_assets"], start=1):
        ts = str(parse_dt(ca["created_at"]))[:19]
        ca_rows.append(f"({i}, {ca['content_id']}, {ca['asset_id']}, '{ts}')")
    lines.append(f"INSERT INTO `content_asset` ({cacols}) VALUES\n" + ",\n".join(ca_rows) + ";")
    lines.append("")

    # comment
    cmcols = (
        "`id`, `content_id`, `author_id`, `parent_id`, `reply_to_user_id`, `body`, `status`, "
        "`like_count`, `created_at`, `updated_at`"
    )
    cmrows = []
    for cm in data["comments"]:
        pid = "NULL" if cm.get("parent_id") is None else str(cm["parent_id"])
        rid = "NULL" if cm.get("reply_to_user_id") is None else str(cm["reply_to_user_id"])
        ts = str(parse_dt(cm["created_at"]))[:19]
        cmrows.append(
            "({id}, {cid}, {aid}, {pid}, {rid}, '{body}', 'NORMAL', {lk}, '{ts}', '{ts}')".format(
                id=cm["id"],
                cid=cm["content_id"],
                aid=cm["author_id"],
                pid=pid,
                rid=rid,
                body=sql_escape(cm["body"]),
                lk=cm.get("like_count", 0),
                ts=ts,
            )
        )
    lines.append(f"INSERT INTO `comment` ({cmcols}) VALUES\n" + ",\n".join(cmrows) + ";")
    lines.append("")

    # user_follow
    fcols = "`id`, `follower_id`, `followee_id`, `created_at`"
    frows = []
    for i, f in enumerate(data["user_follows"], start=1):
        ts = str(parse_dt(f["created_at"]))[:19]
        frows.append(f"({i}, {f['follower_id']}, {f['followee_id']}, '{ts}')")
    lines.append(f"INSERT INTO `user_follow` ({fcols}) VALUES\n" + ",\n".join(frows) + ";")
    lines.append("")

    # portfolio
    pfolcols = (
        "`id`, `owner_id`, `title`, `description`, `strategy_note`, `risk_level`, `returns_ytd`, "
        "`is_public`, `like_count`, `created_at`, `updated_at`"
    )
    pfolrows = []
    for p in data["portfolios"]:
        ts = str(parse_dt(p["created_at"]))[:19]
        ry = Decimal(str(p["returns_ytd"]))
        pfolrows.append(
            "({id}, {oid}, '{title}', '{desc}', '', '{risk}', {ry}, {pub}, {lk}, '{ts}', '{ts}')".format(
                id=p["id"],
                oid=p["user_id"],
                title=sql_escape(p["title"]),
                desc=sql_escape(p.get("description") or ""),
                risk=p["risk_level"],
                ry=f"{ry:.4f}",
                pub=1 if p.get("is_public") else 0,
                lk=p.get("likes", 0),
                ts=ts,
            )
        )
    lines.append(f"INSERT INTO `portfolio` ({pfolcols}) VALUES\n" + ",\n".join(pfolrows) + ";")
    lines.append("")

    # portfolio_asset
    pacols = "`id`, `portfolio_id`, `asset_id`, `symbol`, `name`, `allocation`, `created_at`, `updated_at`"
    parows = []
    for i, pa in enumerate(data["portfolio_assets"], start=1):
        ts = "2026-03-14 09:00:00"
        ad = Decimal(str(pa["allocation"]))
        parows.append(
            "({i}, {pid}, {aid}, '{sym}', '{nm}', {alloc}, '{ts}', '{ts}')".format(
                i=i,
                pid=pa["portfolio_id"],
                aid=pa["asset_id"],
                sym=sql_escape(pa["symbol"]),
                nm=sql_escape(pa["name"]),
                alloc=f"{ad:.2f}",
                ts=ts,
            )
        )
    lines.append(f"INSERT INTO `portfolio_asset` ({pacols}) VALUES\n" + ",\n".join(parows) + ";")
    lines.append("")

    # user_holding
    uhcols = "`id`, `user_id`, `asset_id`, `quantity`, `cost_price`, `notes`, `created_at`, `updated_at`"
    uhrows = []
    for h in data["user_holdings"]:
        notes = ""
        if h.get("opened_at"):
            notes = f"opened_at={h['opened_at']}"
        ts = str(parse_dt(h.get("opened_at") or "2026-03-14T10:00:00Z"))[:19]
        qty = Decimal(str(h["quantity"]))
        cp = Decimal(str(h["avg_cost"]))
        uhrows.append(
            "({id}, {uid}, {aid}, {qty}, {cp}, '{notes}', '{ts}', '{ts}')".format(
                id=h["id"],
                uid=h["user_id"],
                aid=h["asset_id"],
                qty=f"{qty:.4f}",
                cp=f"{cp:.4f}",
                notes=sql_escape(notes),
                ts=ts,
            )
        )
    lines.append(f"INSERT INTO `user_holding` ({uhcols}) VALUES\n" + ",\n".join(uhrows) + ";")
    lines.append("")

    # like
    lcols = "`id`, `user_id`, `target_type`, `target_id`, `created_at`"
    lrows = []
    for lk in data["likes"]:
        ts = str(parse_dt(lk["created_at"]))[:19]
        lrows.append(f"({lk['id']}, {lk['user_id']}, '{lk['target_type']}', {lk['target_id']}, '{ts}')")
    lines.append(f"INSERT INTO `like` ({lcols}) VALUES\n" + ",\n".join(lrows) + ";")
    lines.append("")

    # favorite
    fvcols = "`id`, `user_id`, `content_id`, `created_at`"
    fvrows = []
    for fv in data["favorites"]:
        ts = str(parse_dt(fv["created_at"]))[:19]
        fvrows.append(f"({fv['id']}, {fv['user_id']}, {fv['content_id']}, '{ts}')")
    lines.append(f"INSERT INTO `favorite` ({fvcols}) VALUES\n" + ",\n".join(fvrows) + ";")
    lines.append("")

    lines.extend(
        [
            "COMMIT;",
            "SET FOREIGN_KEY_CHECKS = 1;",
            "",
            "-- Reset AUTO_INCREMENT (adjust if you add rows manually)",
            "ALTER TABLE `user` AUTO_INCREMENT = 13;",
            "ALTER TABLE `asset` AUTO_INCREMENT = 17;",
            "ALTER TABLE `content` AUTO_INCREMENT = 17;",
            "ALTER TABLE `content_asset` AUTO_INCREMENT = 25;",
            "ALTER TABLE `comment` AUTO_INCREMENT = 16;",
            "ALTER TABLE `user_follow` AUTO_INCREMENT = 25;",
            "ALTER TABLE `portfolio` AUTO_INCREMENT = 7;",
            "ALTER TABLE `portfolio_asset` AUTO_INCREMENT = 16;",
            "ALTER TABLE `user_holding` AUTO_INCREMENT = 19;",
            "ALTER TABLE `like` AUTO_INCREMENT = 33;",
            "ALTER TABLE `favorite` AUTO_INCREMENT = 8;",
        ]
    )
    return "\n".join(lines)


def apply_seed_orm(data: dict[str, Any]) -> None:
    """使用 ORM 写入种子数据（须在空库或已清空相关表后执行）。"""
    from django.db import transaction

    from accounts.models import User, UserFollow, UserInvestProfile
    from content.models import Asset, Comment, Content, ContentAsset, ContentMeta, Favorite, Like
    from portfolios.models import Portfolio, PortfolioAsset, UserHolding

    with transaction.atomic():
        for u in data["users"]:
            User.objects.update_or_create(
                id=u["id"],
                defaults={
                    "username": u["username"],
                    "email": u["email"],
                    "phone": u.get("phone") or None,
                    "display_name": u["display_name"],
                    "password": SEED_PASSWORD_HASH,
                    "avatar_url": u.get("avatar_url") or None,
                    "bio": u.get("bio") or "",
                    "investment_experience": u.get("investment_experience") or "",
                    "role": u["role"],
                    "status": u["status"],
                    "points": u["points"],
                    "level": u["level"],
                    "quality_score": Decimal(str(u["quality_score"])),
                    "risk_level": map_json_risk_to_user_risk(u.get("risk_level")),
                    "phone_verified": u.get("phone_verified", False),
                    "email_verified": u.get("email_verified", False),
                    "identity_level": map_identity_level(u.get("identity_level") or "UNVERIFIED"),
                    "real_name_status": map_verification_status(u.get("real_name_status")),
                    "professional_status": map_verification_status(u.get("professional_status")),
                    "risk_assessment_status": map_verification_status(u.get("risk_assessment_status")),
                    "v_badge": u.get("v_badge", False),
                    "is_active": u.get("is_active", True),
                    "is_staff": u.get("is_staff", False),
                    "is_superuser": u.get("is_superuser", False),
                },
            )
            User.objects.filter(pk=u["id"]).update(
                created_at=parse_dt(u["created_at"]),
                updated_at=parse_dt(u["updated_at"]),
            )

        for p in data["user_invest_profiles"]:
            ts = parse_dt(p["updated_at"])
            UserInvestProfile.objects.update_or_create(
                user_id=p["user_id"],
                defaults={
                    "risk_level": map_invest_risk_int(p["risk_level"]),
                    "horizon": map_horizon_int(p["horizon"]),
                    "focus_market": p["focus_market"],
                    "preferred_assets": p["preferred_assets"],
                    "created_at": ts,
                    "updated_at": ts,
                },
            )

        for a in data["assets"]:
            Asset.objects.update_or_create(
                id=a["id"],
                defaults={
                    "code": a["code"],
                    "name": a["name"],
                    "asset_type": normalize_asset_type(a["asset_type"]),
                    "market": normalize_market(a["market"]),
                    "status": a.get("status") or "ACTIVE",
                    "finnhub_symbol": a.get("finnhub_symbol") or None,
                    "exchange": a.get("exchange") or "",
                    "currency": a.get("currency") or "",
                    "industry": a.get("industry") or "",
                },
            )

        for c in data["contents"]:
            pub = parse_dt(c["published_at"]) if c.get("published_at") else None
            ct = pub or parse_dt("2026-03-14T10:00:00Z")
            Content.objects.update_or_create(
                id=c["id"],
                defaults={
                    "author_id": c["author_id"],
                    "title": c["title"],
                    "body": c["body"],
                    "tags_json": c.get("tags_json") or [],
                    "status": c["status"],
                    "reviewed_by_id": c.get("reviewed_by"),
                    "reject_reason": c.get("reject_reason") or "",
                    "risk_score": c.get("risk_score", 0),
                    "risk_level": c.get("risk_level", "LOW"),
                    "moderation_source": normalize_moderation_source(
                        c.get("moderation_source") or "MANUAL"
                    ),
                    "like_count": c.get("like_count", 0),
                    "comment_count": c.get("comment_count", 0),
                    "view_count": c.get("view_count", 0),
                    "published_at": pub,
                },
            )
            Content.objects.filter(pk=c["id"]).update(created_at=ct, updated_at=ct)

        for c in data["contents"]:
            ck = content_meta_kind(c.get("content_type") or "POST")
            ts = parse_dt(c.get("published_at") or "2026-03-14T10:00:00Z")
            ContentMeta.objects.update_or_create(
                content_id=c["id"],
                defaults={
                    "content_type": ck,
                    "format_type": "PLAIN",
                    "created_at": ts,
                    "updated_at": ts,
                },
            )

        for ca in data["content_assets"]:
            ts = parse_dt(ca["created_at"])
            ContentAsset.objects.get_or_create(
                content_id=ca["content_id"],
                asset_id=ca["asset_id"],
                defaults={"created_at": ts},
            )

        for cm in data["comments"]:
            Comment.objects.update_or_create(
                id=cm["id"],
                defaults={
                    "content_id": cm["content_id"],
                    "author_id": cm["author_id"],
                    "parent_id": cm.get("parent_id"),
                    "reply_to_user_id": cm.get("reply_to_user_id"),
                    "body": cm["body"],
                    "status": cm.get("status") or "NORMAL",
                    "like_count": cm.get("like_count", 0),
                },
            )
            tsc = parse_dt(cm["created_at"])
            Comment.objects.filter(pk=cm["id"]).update(
                created_at=tsc, updated_at=tsc
            )

        for f in data["user_follows"]:
            UserFollow.objects.get_or_create(
                follower_id=f["follower_id"],
                followee_id=f["followee_id"],
                defaults={"created_at": parse_dt(f["created_at"])},
            )

        for p in data["portfolios"]:
            ts = parse_dt(p["created_at"])
            Portfolio.objects.update_or_create(
                id=p["id"],
                defaults={
                    "owner_id": p["user_id"],
                    "title": p["title"],
                    "description": p.get("description") or "",
                    "strategy_note": "",
                    "risk_level": p["risk_level"],
                    "returns_ytd": Decimal(str(p["returns_ytd"])),
                    "is_public": p.get("is_public", True),
                    "like_count": p.get("likes", 0),
                },
            )
            Portfolio.objects.filter(pk=p["id"]).update(created_at=ts, updated_at=ts)

        for pa in data["portfolio_assets"]:
            PortfolioAsset.objects.get_or_create(
                portfolio_id=pa["portfolio_id"],
                asset_id=pa["asset_id"],
                defaults={
                    "symbol": pa["symbol"],
                    "name": pa["name"],
                    "allocation": Decimal(str(pa["allocation"])),
                },
            )

        for h in data["user_holdings"]:
            notes = ""
            if h.get("opened_at"):
                notes = f"opened_at={h['opened_at']}"
            ts = parse_dt(h.get("opened_at") or "2026-03-14T10:00:00Z")
            UserHolding.objects.update_or_create(
                id=h["id"],
                defaults={
                    "user_id": h["user_id"],
                    "asset_id": h["asset_id"],
                    "quantity": Decimal(str(h["quantity"])),
                    "cost_price": Decimal(str(h["avg_cost"])),
                    "notes": notes,
                },
            )
            UserHolding.objects.filter(pk=h["id"]).update(
                created_at=ts, updated_at=ts
            )

        for lk in data["likes"]:
            Like.objects.update_or_create(
                id=lk["id"],
                defaults={
                    "user_id": lk["user_id"],
                    "target_type": lk["target_type"],
                    "target_id": lk["target_id"],
                    "created_at": parse_dt(lk["created_at"]),
                },
            )

        for fv in data["favorites"]:
            Favorite.objects.update_or_create(
                id=fv["id"],
                defaults={
                    "user_id": fv["user_id"],
                    "content_id": fv["content_id"],
                    "created_at": parse_dt(fv["created_at"]),
                },
            )


def apply_seed_merge(data: dict[str, Any]) -> dict[str, Any]:
    """
    在保留现有数据的前提下合并种子：按 username/email、标的唯一键匹配已有行并建立 ID 映射；
    帖子/评论/组合/点赞等始终插入新行（新主键），不执行固定 ID 的 SQL。

    返回统计信息 dict，便于命令行输出。
    """
    from django.db import transaction

    from accounts.models import User, UserFollow, UserInvestProfile
    from content.models import Asset, Comment, Content, ContentAsset, ContentMeta, Favorite, Like
    from portfolios.models import Portfolio, PortfolioAsset, UserHolding

    user_map: dict[int, int] = {}
    asset_map: dict[int, int] = {}
    content_map: dict[int, int] = {}
    comment_map: dict[int, int] = {}
    portfolio_map: dict[int, int] = {}

    stats = {
        "users_created": 0,
        "users_matched": 0,
        "assets_created": 0,
        "assets_matched": 0,
        "contents_created": 0,
        "comments_created": 0,
        "holdings_skipped_existing": 0,
    }

    with transaction.atomic():
        # 1) Users：按 username → email 匹配已有账号，否则新建
        for u in data["users"]:
            oid = u["id"]
            existing = User.objects.filter(username=u["username"]).first()
            if not existing:
                existing = User.objects.filter(email=u["email"]).first()
            if existing:
                user_map[oid] = existing.pk
                stats["users_matched"] += 1
                continue
            user = User.objects.create(
                username=u["username"],
                email=u["email"],
                password=SEED_PASSWORD_HASH,
                phone=u.get("phone") or None,
                display_name=u["display_name"],
                avatar_url=u.get("avatar_url") or None,
                bio=u.get("bio") or "",
                investment_experience=u.get("investment_experience") or "",
                role=u["role"],
                status=u["status"],
                points=u["points"],
                level=u["level"],
                quality_score=Decimal(str(u["quality_score"])),
                risk_level=map_json_risk_to_user_risk(u.get("risk_level")),
                phone_verified=u.get("phone_verified", False),
                email_verified=u.get("email_verified", False),
                identity_level=map_identity_level(u.get("identity_level") or "UNVERIFIED"),
                real_name_status=map_verification_status(u.get("real_name_status")),
                professional_status=map_verification_status(u.get("professional_status")),
                risk_assessment_status=map_verification_status(u.get("risk_assessment_status")),
                v_badge=u.get("v_badge", False),
                is_active=u.get("is_active", True),
                is_staff=u.get("is_staff", False),
                is_superuser=u.get("is_superuser", False),
            )
            User.objects.filter(pk=user.pk).update(
                created_at=parse_dt(u["created_at"]),
                updated_at=parse_dt(u["updated_at"]),
            )
            user_map[oid] = user.pk
            stats["users_created"] += 1

        # 2) UserInvestProfile
        for p in data["user_invest_profiles"]:
            uid = user_map.get(p["user_id"])
            if uid is None:
                continue
            ts = parse_dt(p["updated_at"])
            UserInvestProfile.objects.update_or_create(
                user_id=uid,
                defaults={
                    "risk_level": map_invest_risk_int(p["risk_level"]),
                    "horizon": map_horizon_int(p["horizon"]),
                    "focus_market": p["focus_market"],
                    "preferred_assets": p["preferred_assets"],
                    "created_at": ts,
                    "updated_at": ts,
                },
            )

        # 3) Assets：unique (asset_type, code, market)
        for a in data["assets"]:
            oid = a["id"]
            at = normalize_asset_type(a["asset_type"])
            mk = normalize_market(a["market"])
            asset, created = Asset.objects.get_or_create(
                asset_type=at,
                code=a["code"],
                market=mk,
                defaults={
                    "name": a["name"],
                    "status": a.get("status") or "ACTIVE",
                    "finnhub_symbol": a.get("finnhub_symbol") or None,
                    "exchange": a.get("exchange") or "",
                    "currency": a.get("currency") or "",
                    "industry": a.get("industry") or "",
                },
            )
            asset_map[oid] = asset.pk
            if created:
                stats["assets_created"] += 1
            else:
                stats["assets_matched"] += 1

        # 4) Content（新建行，不占用种子里的 id）
        for c in data["contents"]:
            oid = c["id"]
            pub = parse_dt(c["published_at"]) if c.get("published_at") else None
            ct = pub or parse_dt("2026-03-14T10:00:00Z")
            rb = c.get("reviewed_by")
            reviewed_id = user_map[rb] if rb is not None else None
            co = Content.objects.create(
                author_id=user_map[c["author_id"]],
                title=c["title"],
                body=c["body"],
                tags_json=c.get("tags_json") or [],
                status=c["status"],
                reviewed_by_id=reviewed_id,
                reject_reason=c.get("reject_reason") or "",
                risk_score=c.get("risk_score", 0),
                risk_level=c.get("risk_level", "LOW"),
                moderation_source=normalize_moderation_source(
                    c.get("moderation_source") or "MANUAL"
                ),
                like_count=c.get("like_count", 0),
                comment_count=c.get("comment_count", 0),
                view_count=c.get("view_count", 0),
                published_at=pub,
            )
            Content.objects.filter(pk=co.pk).update(created_at=ct, updated_at=ct)
            content_map[oid] = co.pk
            stats["contents_created"] += 1

        # 5) ContentMeta
        for c in data["contents"]:
            nid = content_map.get(c["id"])
            if nid is None:
                continue
            ck = content_meta_kind(c.get("content_type") or "POST")
            ts = parse_dt(c.get("published_at") or "2026-03-14T10:00:00Z")
            ContentMeta.objects.update_or_create(
                content_id=nid,
                defaults={
                    "content_type": ck,
                    "format_type": "PLAIN",
                    "created_at": ts,
                    "updated_at": ts,
                },
            )

        # 6) ContentAsset
        for ca in data["content_assets"]:
            cid = content_map.get(ca["content_id"])
            aid = asset_map.get(ca["asset_id"])
            if cid is None or aid is None:
                continue
            ts = parse_dt(ca["created_at"])
            ContentAsset.objects.get_or_create(
                content_id=cid,
                asset_id=aid,
                defaults={"created_at": ts},
            )

        # 7) Comments（父评论先于子评论）
        pending = list(data["comments"])
        while pending:
            progressed = False
            for cm in list(pending):
                pid = cm.get("parent_id")
                if pid is not None and pid not in comment_map:
                    continue
                cid = content_map.get(cm["content_id"])
                if cid is None:
                    pending.remove(cm)
                    progressed = True
                    continue
                parent_pk = comment_map[pid] if pid is not None else None
                ru = cm.get("reply_to_user_id")
                new_c = Comment.objects.create(
                    content_id=cid,
                    author_id=user_map[cm["author_id"]],
                    parent_id=parent_pk,
                    reply_to_user_id=user_map[ru] if ru is not None else None,
                    body=cm["body"],
                    status=cm.get("status") or "NORMAL",
                    like_count=cm.get("like_count", 0),
                )
                tsc = parse_dt(cm["created_at"])
                Comment.objects.filter(pk=new_c.pk).update(
                    created_at=tsc, updated_at=tsc
                )
                comment_map[cm["id"]] = new_c.pk
                pending.remove(cm)
                progressed = True
                stats["comments_created"] += 1
            if not progressed:
                raise ValueError(
                    "种子评论无法解析（可能缺少父评论或 content 映射），请检查 JSON。"
                )

        # 8) UserFollow
        for f in data["user_follows"]:
            fi = user_map.get(f["follower_id"])
            fe = user_map.get(f["followee_id"])
            if fi is None or fe is None:
                continue
            UserFollow.objects.get_or_create(
                follower_id=fi,
                followee_id=fe,
                defaults={"created_at": parse_dt(f["created_at"])},
            )

        # 9) Portfolio
        for p in data["portfolios"]:
            oid = p["id"]
            owner = user_map.get(p["user_id"])
            if owner is None:
                continue
            ts = parse_dt(p["created_at"])
            po = Portfolio.objects.create(
                owner_id=owner,
                title=p["title"],
                description=p.get("description") or "",
                strategy_note="",
                risk_level=p["risk_level"],
                returns_ytd=Decimal(str(p["returns_ytd"])),
                is_public=p.get("is_public", True),
                like_count=p.get("likes", 0),
            )
            Portfolio.objects.filter(pk=po.pk).update(created_at=ts, updated_at=ts)
            portfolio_map[oid] = po.pk

        # 10) PortfolioAsset
        for pa in data["portfolio_assets"]:
            pid = portfolio_map.get(pa["portfolio_id"])
            aid = asset_map.get(pa["asset_id"])
            if pid is None or aid is None:
                continue
            PortfolioAsset.objects.get_or_create(
                portfolio_id=pid,
                asset_id=aid,
                defaults={
                    "symbol": pa["symbol"],
                    "name": pa["name"],
                    "allocation": Decimal(str(pa["allocation"])),
                },
            )

        # 11) UserHolding：若该用户已持有该标的则跳过，避免覆盖真实持仓
        for h in data["user_holdings"]:
            uid = user_map.get(h["user_id"])
            aid = asset_map.get(h["asset_id"])
            if uid is None or aid is None:
                continue
            notes = ""
            if h.get("opened_at"):
                notes = f"opened_at={h['opened_at']}"
            ts = parse_dt(h.get("opened_at") or "2026-03-14T10:00:00Z")
            if UserHolding.objects.filter(user_id=uid, asset_id=aid).exists():
                stats["holdings_skipped_existing"] += 1
                continue
            uh = UserHolding.objects.create(
                user_id=uid,
                asset_id=aid,
                quantity=Decimal(str(h["quantity"])),
                cost_price=Decimal(str(h["avg_cost"])),
                notes=notes,
            )
            UserHolding.objects.filter(pk=uh.pk).update(created_at=ts, updated_at=ts)

        # 12) Like
        for lk in data["likes"]:
            uid = user_map.get(lk["user_id"])
            if uid is None:
                continue
            tt = lk["target_type"]
            tid = lk["target_id"]
            if tt == "POST":
                new_tid = content_map.get(tid)
            elif tt == "COMMENT":
                new_tid = comment_map.get(tid)
            elif tt == "PORTFOLIO":
                new_tid = portfolio_map.get(tid)
            else:
                continue
            if new_tid is None:
                continue
            Like.objects.get_or_create(
                user_id=uid,
                target_type=tt,
                target_id=new_tid,
                defaults={"created_at": parse_dt(lk["created_at"])},
            )

        # 13) Favorite
        for fv in data["favorites"]:
            uid = user_map.get(fv["user_id"])
            cid = content_map.get(fv["content_id"])
            if uid is None or cid is None:
                continue
            Favorite.objects.get_or_create(
                user_id=uid,
                content_id=cid,
                defaults={"created_at": parse_dt(fv["created_at"])},
            )

    return stats
