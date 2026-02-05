from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from metric_anomaly_investigator.settings import settings
from metric_anomaly_investigator.schemas import (
    InsightReport,
    StepResult,
    InvestigationPlan,
)


class InsightsGenerator:
    def __init__(
        self,
        model_name: str = settings.MODEL_NAME,
    ):
        self.agent = Agent(
            model=AnthropicModel(
                model_name=model_name,
            ),
            output_type=InsightReport,
            system_prompt=self._get_system_prompt(),
        )

    def _get_system_prompt(self) -> str:
        return """You are a senior data analyst writing executive insights.

            Given investigation results, synthesize findings into a clear, actionable report.

            Your report should:
            1. Summarize the root cause clearly
            2. Identify affected user segments specifically
            3. Note correlated events (deployments, experiments)
            4. Provide concrete, prioritized recommendations
            5. Include confidence score based on data quality

            Be concise but comprehensive. Focus on what actions should be taken.
            """

    async def generate_insights(
        self,
        plan: InvestigationPlan,
        results: list[StepResult],
    ) -> InsightReport:
        # strategy
        # get context from plan
        # extract findings + confidencefrom the successful results

        prompt = f"Investigation plan hypothesis: {plan.hypothesis}\n\n"
        prompt += "Investigation findings:\n\n"

        for result in results:
            if result.success:
                prompt += f"Step {result.step_id}:\n"
                for finding in result.key_findings:
                    prompt += f"  {finding}\n"
                prompt += f"  Confidence score: {result.confidence_score}\n\n"

        prompt += """Based on the above findings, generate an insights report.
            IMPORTANT: Include specific details from the findings in your root_cause and affected_segments.
            If a deployment correlates with the metric drop timing, include it in correlated_events."""

        response = await self.agent.run(user_prompt=prompt)

        report = response.output
        report.confidence_score = sum(
            r.confidence_score for r in results if r.success
        ) / max(1, len([r for r in results if r.success]))

        return report
