from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

from metric_anomaly_investigator.schemas import (
    ConversationContext,
    InvestigationPlan,
    UserQuery,
)
from metric_anomaly_investigator.settings import settings


class InvestigationPlanner:
    def __init__(
        self,
        model_name: str = settings.MODEL_NAME,
    ):
        self.agent = Agent(
            model=AnthropicModel(
                model_name=model_name,
            ),
            output_type=InvestigationPlan,
            system_prompt=self._get_system_prompt(),
        )

    def _get_system_prompt(self) -> str:
        return """You are an expert data analyst investigating metric anomalies.

            When given a metric drop/spike, you generate a systematic investigation plan.

            DATA CONTEXT:
            - Data is available from 2026-01-25 to 2026-02-01
            - Platforms: ios, android, web
            - Countries: US, IN (India), BR (Brazil), UK, DE, FR
            - Metrics: dau (daily active users), wau, events_per_user

            Your investigation strategy should:
            1. ALWAYS segment by platform AND country to find affected segments
            2. Check deployments in the time range around the anomaly
            3. Look for correlations between deployment timing and metric drops

            Available investigation actions:
            - segment_by_dimension: Find which segments changed most (USE THIS FIRST)
              * dimension can be: platform, country, device_type, app_version
              * Requires time_range (anomaly period) and baseline_range (before anomaly)
            - check_deployments: Look for releases that correlate with the drop
            - query_metric: Get raw metric time series
            - analyze_retention: Check cohort retention rates
            - statistical_analysis: Compare two segments statistically

            IMPORTANT DATES:
            - If user mentions a specific date (e.g., "January 28th"), use:
              * baseline_range: before that date (e.g., 2026-01-25 to 2026-01-27)
              * time_range: on and after that date (e.g., 2026-01-28 to 2026-02-01)
            - If no date mentioned, use full range with midpoint split

            Generate 3-5 steps. Always include:
            1. segment_by_dimension for platform
            2. segment_by_dimension for country
            3. check_deployments
            """

    async def create_plan(
        self,
        query: UserQuery,
        context: ConversationContext | None = None,
    ) -> InvestigationPlan:
        """
        Generate investigation plan from user query

        If context exists (multi-turn), refine existing plan
        """

        user_prompt = f"User query: {query.query_text}\n\n"

        if context and context.executed_steps:
            user_prompt += "Previous findings:\n"
            for step_result in context.executed_steps:
                user_prompt += (
                    f"- Step {step_result.step_id}: {step_result.key_findings}\n"
                )
            user_prompt += "\nWhat should we investigate next?"
        else:
            user_prompt += "Generate initial investigation plan."

        response = await self.agent.run(user_prompt=user_prompt)

        return response.output
