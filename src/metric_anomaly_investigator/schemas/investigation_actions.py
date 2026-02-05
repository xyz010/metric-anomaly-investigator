from typing import Literal, Annotated, Union

from pydantic import BaseModel, Field


class BaseStep(BaseModel):
    step_id: int
    reasoning: str


class QueryMetricParams(BaseModel):
    metric_name: Literal["dau", "wau", "events_per_user"]
    time_range: tuple[str, str] = Field(
        description="Start and end date as ISO strings, e.g. ('2026-01-25', '2026-02-01')"
    )
    dimensions: list[str] | None = Field(
        default=None,
        description="Dimensions to group by: platform, country, device_type, app_version",
    )
    filters: dict[str, str] | None = Field(
        default=None, description="Filter conditions, e.g. {'platform': 'android'}"
    )


class SegmentByDimensionParams(BaseModel):
    metric_name: Literal["dau", "wau", "events_per_user"]
    dimension: Literal["platform", "country", "device_type", "app_version"]
    time_range: tuple[str, str]
    baseline_range: tuple[str, str]
    min_drop_threshold: float = 0.10


class CheckDeploymentsParams(BaseModel):
    time_range: tuple[str, str]
    platform: Literal["ios", "android", "web"] | None = None


class AnalyzeRetentionParams(BaseModel):
    cohort_date: str = Field(description="ISO date string, e.g. '2026-01-25'")
    retention_days: list[int] = [1, 7, 30]
    filters: dict[str, str] | None = None


class StatisticalTestParams(BaseModel):
    metric_name: Literal["dau", "wau", "events_per_user"]
    control_filters: dict[str, str]
    treatment_filters: dict[str, str]
    time_range: tuple[str, str]


class GenerateInsightsParams(BaseModel):
    preliminary_hypothesis: str = Field(
        description="Your current hypothesis about the root cause based on findings so far"
    )


class QueryMetricStep(BaseStep):
    action: Literal["query_metric"] = "query_metric"
    parameters: QueryMetricParams


class SegmentByDimensionStep(BaseStep):
    action: Literal["segment_by_dimension"] = "segment_by_dimension"
    parameters: SegmentByDimensionParams


class CheckDeploymentsStep(BaseStep):
    action: Literal["check_deployments"] = "check_deployments"
    parameters: CheckDeploymentsParams


class AnalyzeRetentionStep(BaseStep):
    action: Literal["analyze_retention"] = "analyze_retention"
    parameters: AnalyzeRetentionParams


class StatisticalTestStep(BaseStep):
    action: Literal["statistical_analysis"] = "statistical_analysis"
    parameters: StatisticalTestParams


class GenerateInsightsStep(BaseStep):
    action: Literal["generate_insights"] = "generate_insights"
    parameters: GenerateInsightsParams


InvestigationStep = Annotated[
    Union[
        QueryMetricStep,
        SegmentByDimensionStep,
        CheckDeploymentsStep,
        AnalyzeRetentionStep,
        StatisticalTestStep,
        GenerateInsightsStep,
    ],
    Field(discriminator="action"),
]


class InvestigationPlan(BaseModel):
    steps: list[InvestigationStep]
    priority_dimensions: list[str] = Field(
        description="Dimensions to investigate first"
    )
    hypothesis: str = Field(description="Initial hypothesis about the anomaly cause")
