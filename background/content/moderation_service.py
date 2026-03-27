from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import timedelta
from hashlib import sha256

from django.utils import timezone

from content.models import Content
from reports.models import ModerationRule, ModerationHit, ModerationQueueItem


@dataclass
class ModerationDecision:
    risk_score: int
    risk_level: str
    disposition: str
    summary: str
    hit_ids: list[int]


def _normalize_text(text: str) -> str:
    compact = re.sub(r"\s+", "", text or "")
    return compact.lower()


def _calc_risk_level(score: int) -> str:
    if score >= 80:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"


def _calc_disposition(level: str) -> str:
    if level == "HIGH":
        return "AUTO_REJECT"
    if level == "MEDIUM":
        return "PENDING_REVIEW"
    return "AUTO_PASS"


def evaluate_content_risk(*, text: str, title: str = "", author=None) -> ModerationDecision:
    full_text = f"{title}\n{text}".strip()
    normalized = _normalize_text(full_text)
    total_score = 0
    hit_ids: list[int] = []
    hit_summaries: list[str] = []

    active_rules = ModerationRule.objects.filter(is_active=True)
    for rule in active_rules:
        if rule.rule_type in ["SENSITIVE_WORD", "COMPLIANCE_POLICY"] and rule.pattern:
            if re.search(rule.pattern, full_text, flags=re.IGNORECASE):
                total_score += int(rule.risk_score)
                hit_summaries.append(rule.name)

    # 兜底默认词库：兼容现网旧逻辑
    fallback_words = ["保本收益", "稳赚不赔", "带单", "跟单", "内幕消息", "拉盘", "坐庄"]
    for word in fallback_words:
        if word in full_text:
            total_score += 12
            hit_summaries.append(f"fallback:{word}")

    # 轻量重复检测：同作者24小时内归一化文本哈希重复
    if author and normalized:
        now = timezone.now()
        day_ago = now - timedelta(hours=24)
        same_hash = sha256(normalized.encode("utf-8")).hexdigest()
        recent = Content.objects.filter(author=author, created_at__gte=day_ago).only("id", "body", "title")
        for old in recent:
            old_hash = sha256(_normalize_text(f"{old.title}\n{old.body}").encode("utf-8")).hexdigest()
            if old_hash == same_hash:
                total_score += 35
                hit_summaries.append("repetition:exact")
                break

    risk_level = _calc_risk_level(total_score)
    disposition = _calc_disposition(risk_level)
    summary = "、".join(hit_summaries[:6])

    return ModerationDecision(
        risk_score=total_score,
        risk_level=risk_level,
        disposition=disposition,
        summary=summary,
        hit_ids=hit_ids,
    )


def persist_moderation_result(*, content: Content, decision: ModerationDecision, author):
    content.risk_score = decision.risk_score
    content.risk_level = decision.risk_level
    content.moderation_source = "AUTO"
    if decision.disposition == "AUTO_REJECT":
        content.status = "REJECTED"
        if not content.reject_reason:
            content.reject_reason = "命中高风险规则，系统自动驳回"
    elif decision.disposition in ["PENDING_REVIEW", "AUTO_PASS"]:
        content.status = "PENDING_REVIEW"
    content.save(update_fields=["risk_score", "risk_level", "moderation_source", "status", "reject_reason", "updated_at"])

    if decision.summary:
        ModerationHit.objects.create(
            rule=None,
            content=content,
            user=author,
            hit_text=decision.summary[:255],
            evidence_json={"summary": decision.summary},
            risk_score=decision.risk_score,
            risk_level=decision.risk_level,
        )

    if decision.risk_level in ["MEDIUM", "HIGH"]:
        ModerationQueueItem.objects.get_or_create(
            content=content,
            status="PENDING",
            defaults={
                "source": "AUTO",
                "risk_level": decision.risk_level,
                "risk_score": decision.risk_score,
                "reason_summary": decision.summary[:255],
            },
        )
