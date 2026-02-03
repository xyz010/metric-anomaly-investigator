from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from metric_anomaly_investigator.models import (
    InvestigationPlan,
    ConversationContext,
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

            Your investigation strategy should:
            1. Start with high-level segmentation (platform, country, device)
            2. Drill into segments showing largest changes
            3. Check for correlated events (deployments, experiments)
            4. Validate with statistical tests
            5. Analyze user behavior impact (retention, engagement)

            Available investigation actions:
            - query_metric: Get metric time series with filters
            - segment_by_dimension: Find which segments changed most
            - check_deployments: Look for releases/feature flags
            - analyze_retention: Check cohort retention rates
            - statistical_test: Compare two segments statistically

            Prioritize steps that narrow down root cause most efficiently.
            Include reasoning for each step.
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
