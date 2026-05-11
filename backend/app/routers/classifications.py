import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.classification import (
    CategoryTaxonomy,
    ClassificationRule,
    ClassificationSource,
    MovementClassification,
)
from app.models.movement import Movement
from app.schemas.classification import (
    BatchClassifyRequest,
    BatchClassifyResponse,
    ClassificationRuleCreate,
    ClassificationRuleResponse,
    ClassificationRuleUpdate,
    SingleClassifyResponse,
)
from app.services.classification.engine import classify_movement, load_active_rules

router = APIRouter(prefix="/classifications", tags=["classifications"])


class CategoryResponse(BaseModel):
    code: str
    parent_code: str | None
    name: str
    description: str
    cash_flow_section: str
    level: int
    is_active: bool

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Taxonomy
# ---------------------------------------------------------------------------


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CategoryTaxonomy)
        .where(CategoryTaxonomy.is_active.is_(True))
        .order_by(CategoryTaxonomy.level, CategoryTaxonomy.code)
    )
    return result.scalars().all()


# ---------------------------------------------------------------------------
# Rules CRUD
# ---------------------------------------------------------------------------


@router.get("/rules", response_model=list[ClassificationRuleResponse])
async def list_rules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ClassificationRule).order_by(ClassificationRule.priority, ClassificationRule.name)
    )
    return result.scalars().all()


@router.post("/rules", response_model=ClassificationRuleResponse, status_code=201)
async def create_rule(body: ClassificationRuleCreate, db: AsyncSession = Depends(get_db)):
    cat = (
        await db.execute(
            select(CategoryTaxonomy).where(
                CategoryTaxonomy.code == body.category_code,
                CategoryTaxonomy.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=422, detail=f"Unknown category code: {body.category_code}")

    rule = ClassificationRule(
        name=body.name,
        priority=body.priority,
        match_type=body.match_type,
        match_field=body.match_field,
        match_pattern=body.match_pattern,
        category_code=body.category_code,
        subcategory_code=body.subcategory_code,
        created_by="user",
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.put("/rules/{rule_id}", response_model=ClassificationRuleResponse)
async def update_rule(
    rule_id: uuid.UUID, body: ClassificationRuleUpdate, db: AsyncSession = Depends(get_db)
):
    rule = (
        await db.execute(select(ClassificationRule).where(ClassificationRule.id == rule_id))
    ).scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    if body.category_code is not None:
        cat = (
            await db.execute(
                select(CategoryTaxonomy).where(
                    CategoryTaxonomy.code == body.category_code,
                    CategoryTaxonomy.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()
        if not cat:
            raise HTTPException(status_code=422, detail=f"Unknown category code: {body.category_code}")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(rule, field, value)
    rule.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}", status_code=204)
async def deactivate_rule(rule_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    rule = (
        await db.execute(select(ClassificationRule).where(ClassificationRule.id == rule_id))
    ).scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.is_active = False
    await db.commit()


# ---------------------------------------------------------------------------
# Batch classification
# ---------------------------------------------------------------------------


@router.post("/batch", response_model=BatchClassifyResponse)
async def batch_classify(body: BatchClassifyRequest, db: AsyncSession = Depends(get_db)):
    rules = await load_active_rules(db)

    # Determine which movements to process
    stmt = select(Movement).where(Movement.is_deleted.is_(False))

    if body.movement_ids:
        stmt = stmt.where(Movement.id.in_(body.movement_ids))
    elif not body.force_reclassify:
        # Only unclassified (no MovementClassification row)
        classified_ids = select(MovementClassification.movement_id)
        stmt = stmt.where(Movement.id.notin_(classified_ids))

    movements = list((await db.execute(stmt)).scalars().all())

    # Count manual overrides that will be preserved
    override_count = 0
    if body.force_reclassify:
        override_result = await db.execute(
            select(MovementClassification).where(
                MovementClassification.source == ClassificationSource.MANUAL,
                MovementClassification.movement_id.in_([m.id for m in movements]),
            )
        )
        override_count = len(override_result.scalars().all())

    processed = 0
    classified = 0
    unclassified = 0

    for movement in movements:
        # Skip manual overrides during force re-classify
        if body.force_reclassify:
            existing = (
                await db.execute(
                    select(MovementClassification).where(
                        MovementClassification.movement_id == movement.id
                    )
                )
            ).scalar_one_or_none()
            if existing and existing.source == ClassificationSource.MANUAL:
                continue

        result = classify_movement(movement, rules)
        processed += 1

        existing = (
            await db.execute(
                select(MovementClassification).where(
                    MovementClassification.movement_id == movement.id
                )
            )
        ).scalar_one_or_none()

        if existing:
            existing.category_code = result.category_code
            existing.source = result.source
            existing.rule_id = result.rule_id
            existing.confidence = result.confidence
            existing.classified_at = datetime.utcnow()
            existing.classified_by = "system"
            existing.is_confirmed = True
        else:
            db.add(
                MovementClassification(
                    movement_id=movement.id,
                    category_code=result.category_code,
                    source=result.source,
                    rule_id=result.rule_id,
                    confidence=result.confidence,
                    classified_by="system",
                    is_confirmed=True,
                )
            )

        if result.category_code == "UNCLASSIFIED":
            unclassified += 1
        else:
            classified += 1

    await db.commit()

    return BatchClassifyResponse(
        processed=processed,
        classified=classified,
        unclassified=unclassified,
        overrides_preserved=override_count,
    )
