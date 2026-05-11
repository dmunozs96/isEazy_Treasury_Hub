import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.classification import MatchType


class ClassificationRuleCreate(BaseModel):
    name: str
    priority: int = 100
    match_type: MatchType
    match_field: str
    match_pattern: str
    category_code: str
    subcategory_code: str | None = None


class ClassificationRuleUpdate(BaseModel):
    name: str | None = None
    priority: int | None = None
    is_active: bool | None = None
    match_type: MatchType | None = None
    match_field: str | None = None
    match_pattern: str | None = None
    category_code: str | None = None
    subcategory_code: str | None = None


class ClassificationRuleResponse(BaseModel):
    id: uuid.UUID
    name: str
    priority: int
    is_active: bool
    match_type: MatchType
    match_field: str
    match_pattern: str
    category_code: str
    subcategory_code: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BatchClassifyRequest(BaseModel):
    movement_ids: list[uuid.UUID] | None = None
    force_reclassify: bool = False


class BatchClassifyResponse(BaseModel):
    processed: int
    classified: int
    unclassified: int
    overrides_preserved: int


class SingleClassifyResponse(BaseModel):
    movement_id: uuid.UUID
    category_code: str
    rule_id: uuid.UUID | None
    source: str
