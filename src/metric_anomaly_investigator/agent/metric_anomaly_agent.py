import logging
import uuid

from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

from metric_anomaly_investigator.mock_warehouse import MockDataWarehouse
from metric_anomaly_investigator.schemas import (
    ConversationContext,
    InvestigationStep,
    UserQuery,
    StepResult,
    InsightReport,
)
from metric_anomaly_investigator.agent.tool_executor import ToolExecutor
from metric_anomaly_investigator.agent.prompts import (
    STEP_DECISION_AGENT_PROMPT,
    INSIGHTS_GENERATOR_AGENT_PROMPT,
)
from metric_anomaly_investigator.settings import settings

logger = logging.getLogger(__name__)


class MetricAnomalyAgent:
    """
    Main orchestrator agent for metric anomaly investigation.

    Uses two sub-agents:
    1. Step Decision Agent - decides the next investigation action
    2. Insights Generator Agent - synthesizes findings into a report
    """

    def __init__(self):
        self.warehouse = MockDataWarehouse()
        self.tool_executor = ToolExecutor(self.warehouse)
        self._step_agent = self._create_step_decision_agent()
        self._insights_agent = self._create_insights_agent()
        self.conversations: dict[str, ConversationContext] = {}

    def _create_step_decision_agent(self) -> Agent:
        """Create the agent that decides the next investigation step."""
        return Agent(
            model=AnthropicModel(model_name=settings.MODEL_NAME),
            output_type=InvestigationStep,
            system_prompt=STEP_DECISION_AGENT_PROMPT,
        )

    def _create_insights_agent(self) -> Agent:
        """Create the agent that generates the final insights report."""
        return Agent(
            model=AnthropicModel(model_name=settings.MODEL_NAME),
            output_type=InsightReport,
            system_prompt=INSIGHTS_GENERATOR_AGENT_PROMPT,
        )

    async def _decide_next_step(
        self, query: UserQuery, executed_steps: list[StepResult]
    ) -> InvestigationStep:
        """Use the step agent to decide the next investigation action."""
        prompt = f"User query: {query.query_text}\n"
        if executed_steps:
            prompt += "\nPrevious step results:\n"
            for step in executed_steps:
                prompt += f"- Step {step.step_id}: success={step.success}\n"
                prompt += f"  Findings: {step.key_findings}\n"

        result = await self._step_agent.run(user_prompt=prompt)
        return result.output

    async def _generate_insights(
        self, query: str, executed_steps: list[StepResult], hypothesis: str
    ) -> InsightReport:
        """Use the insights agent to generate the final report."""
        prompt = f"Original query: {query}\n"
        prompt += f"Preliminary hypothesis: {hypothesis}\n\n"
        prompt += "Investigation steps and findings:\n"

        for step in executed_steps:
            prompt += f"\nStep {step.step_id}:\n"
            prompt += f"  Success: {step.success}\n"
            prompt += "  Key findings:\n"
            for finding in step.key_findings:
                prompt += f"    - {finding}\n"
            if step.data:
                prompt += f"  Data summary: {self._summarize_data(step.data)}\n"

        prompt += "\nGenerate a comprehensive InsightReport based on these findings."

        result = await self._insights_agent.run(user_prompt=prompt)
        return result.output

    def _summarize_data(self, data: dict) -> str:
        """Create a brief summary of step data for the insights agent."""
        if not data:
            return "No data"

        summaries = []
        if "results" in data:
            summaries.append(f"{len(data['results'])} data points")
        if "deployments" in data:
            summaries.append(f"{len(data['deployments'])} deployments found")
        if "retention" in data:
            summaries.append(f"retention data: {data['retention']}")
        if "is_significant" in data:
            summaries.append(f"statistical significance: {data['is_significant']}")

        return ", ".join(summaries) if summaries else str(data)[:100]

    def _compute_supporting_data(self, executed_steps: list[StepResult]) -> dict:
        """Compute supporting_data metrics from executed steps."""
        data_points = 0
        deployments_found = 0
        confidence_scores = []

        for step in executed_steps:
            if step.success:
                confidence_scores.append(step.confidence_score)
                if step.data:
                    if "results" in step.data:
                        data_points += len(step.data["results"])
                    if "deployments" in step.data:
                        deployments_found += len(step.data["deployments"])

        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores)
            if confidence_scores
            else 0.0
        )

        return {
            "investigation_steps_completed": len(executed_steps),
            "data_points_analyzed": data_points,
            "deployments_found": deployments_found,
            "average_confidence_score": round(avg_confidence, 2),
            "requires_followup": avg_confidence < 0.7,
        }

    async def investigate_anomaly(
        self, query: str, context_id: str | None = None
    ) -> ConversationContext:
        """
        Investigate a metric anomaly using the iterative step-by-step approach.

        Flow:
        1. Step agent decides next action
        2. Execute the action
        3. Repeat until step agent chooses generate_insights
        4. Insights agent synthesizes all findings into InsightReport
        """
        if context_id and context_id in self.conversations:
            context = self.conversations[context_id]
        else:
            context_id = str(uuid.uuid4())
            context = ConversationContext(conversation_id=context_id)
            self.conversations[context_id] = context

        user_query = UserQuery(query_text=query, context_id=context_id)
        logger.info(f"Starting investigation for context {context_id}")

        insights = None
        for iteration in range(settings.MAX_INVESTIGATION_STEPS):
            next_step = await self._decide_next_step(
                query=user_query, executed_steps=context.executed_steps
            )
            logger.info(
                f"Step {iteration + 1}: {next_step.action} - {next_step.reasoning}"
            )

            if next_step.action == "generate_insights":
                logger.info("Generating insights report...")
                hypothesis = next_step.parameters.preliminary_hypothesis
                insights = await self._generate_insights(
                    query=query,
                    executed_steps=context.executed_steps,
                    hypothesis=hypothesis,
                )
                # Compute supporting_data programmatically
                insights.supporting_data = self._compute_supporting_data(
                    context.executed_steps
                )
                logger.info(
                    f"Insights generated with confidence {insights.confidence_score}"
                )
                break

            result = self.tool_executor.execute_step(next_step)
            context.executed_steps.append(result)

            if result.success:
                logger.info(f"Step {next_step.step_id} executed successfully")
                for finding in result.key_findings:
                    logger.info(f"  Finding: {finding}")
            else:
                logger.error(f"Step {next_step.step_id} failed: {result.error_message}")

        context.insights = insights
        return context

    async def follow_up_conversation(
        self,
        query: str,
        context_id: str,
    ) -> ConversationContext:
        """Handle follow-up questions about an investigation."""
        if context_id not in self.conversations:
            raise ValueError(f"Context ID {context_id} not found.")

        context = self.conversations[context_id]
        context.user_feedback.append(query)

        return await self.investigate_anomaly(query=query, context_id=context_id)
