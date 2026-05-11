import json
import re
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classification import ClassificationRule, ClassificationSource, MatchType


class ClassificationResult:
    def __init__(
        self,
        category_code: str,
        source: ClassificationSource,
        rule_id=None,
        confidence: float = 1.0,
    ):
        self.category_code = category_code
        self.source = source
        self.rule_id = rule_id
        self.confidence = confidence


def _evaluate_condition(cond: dict, movement) -> bool:
    cond_type = cond.get("type", "")
    if cond_type == "KEYWORD":
        value = getattr(movement, cond.get("field", "description"), "") or ""
        return cond.get("value", "").upper() in value.upper()
    if cond_type == "AMOUNT_RANGE":
        amount = float(movement.amount or 0)
        return cond.get("min", float("-inf")) <= amount <= cond.get("max", float("inf"))
    return False


def evaluate_rule(rule: ClassificationRule, movement) -> bool:
    match rule.match_type:
        case MatchType.KEYWORD:
            field_value = getattr(movement, rule.match_field, "") or ""
            return rule.match_pattern.upper() in field_value.upper()

        case MatchType.REGEX:
            field_value = getattr(movement, rule.match_field, "") or ""
            return bool(re.search(rule.match_pattern, field_value, re.IGNORECASE))

        case MatchType.COUNTERPART_NAME:
            field_value = movement.counterpart_name or ""
            return rule.match_pattern.upper() in field_value.upper()

        case MatchType.AMOUNT_RANGE:
            bounds = json.loads(rule.match_pattern)
            amount = float(movement.amount or 0)
            min_val = bounds.get("min", float("-inf"))
            max_val = bounds.get("max", float("inf"))
            return min_val <= amount <= max_val

        case MatchType.COMPOSITE:
            conditions = json.loads(rule.match_pattern)
            return all(_evaluate_condition(c, movement) for c in conditions)

    return False


def classify_movement(movement, rules: list[ClassificationRule]) -> ClassificationResult:
    for rule in sorted(rules, key=lambda r: r.priority):
        if rule.is_active and evaluate_rule(rule, movement):
            return ClassificationResult(
                category_code=rule.category_code,
                source=ClassificationSource.RULE,
                rule_id=rule.id,
                confidence=1.0,
            )
    return ClassificationResult(
        category_code="UNCLASSIFIED",
        source=ClassificationSource.RULE,
        rule_id=None,
        confidence=1.0,
    )


async def load_active_rules(db: AsyncSession) -> list[ClassificationRule]:
    result = await db.execute(
        select(ClassificationRule)
        .where(ClassificationRule.is_active.is_(True))
        .order_by(ClassificationRule.priority)
    )
    return list(result.scalars().all())
