from pydantic import BaseModel, Field
from typing import Any, Dict
from datetime import datetime
from metric_anomaly_investigator.schemas.investigation_actions import (
    InvestigationPlan,
)


# Result Models
class StepResult(BaseModel):
    step_id: int
    success: bool
    data: dict[str, Any] | None = None
    error_message: str | None = None
    key_findings: list[str] = []
    confidence_score: float = Field(ge=0.0, le=1.0)


class InsightReport(BaseModel):
    summary: str
    root_cause: str
    affected_segments: list[dict[str, Any]]
    correlated_events: list[str]  # Deployments or experiments
    recommendations: list[str]
    confidence_score: float = Field(ge=0.0, le=1.0)
    supporting_data: dict[str, Any]


# Conversation Models
class ConversationContext(BaseModel):
    conversation_id: str
    current_investigation: InvestigationPlan | None = None
    executed_steps: list[StepResult] = []
    insights: InsightReport | None = None
    user_feedback: list[str] = []  # Track refinements


class UserQuery(BaseModel):
    query_text: str
    context_id: str | None = None  # For multi-turn


# Warehouse Models
class MetricDataPoint(BaseModel):
    timestamp: datetime
    value: float
    dimensions: Dict[str, str] = {}


class DimensionalBreakdown(BaseModel):
    dimension_name: str
    dimension_value: str
    before_value: float
    after_value: float
    pct_change: float
    sample_size: int


class Deployment(BaseModel):
    deployment_id: str
    deployment_date: datetime
    app_version: str
    platform: str
    regions: list[str]
    rollout_percentage: float
