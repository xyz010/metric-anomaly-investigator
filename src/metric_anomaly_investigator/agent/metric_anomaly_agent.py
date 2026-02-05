import logging
import uuid

from metric_anomaly_investigator.mock_warehouse import MockDataWarehouse
from metric_anomaly_investigator.schemas import (
    ConversationContext,
    InvestigationStep,
    UserQuery,
)

from metric_anomaly_investigator.agent.investigation_planner_agent import (
    InvestigationPlanner,
)
from metric_anomaly_investigator.agent.insights_agent import InsightsGenerator
from metric_anomaly_investigator.agent.tool_executor import ToolExecutor

logger = logging.getLogger(__name__)


class MetricAnomalyAgent:
    def __init__(self):
        self.warehouse = MockDataWarehouse()
        self.tool_executor = ToolExecutor(self.warehouse)
        self.investigation_planner = InvestigationPlanner()
        self.insights_generator = InsightsGenerator()

        self.conversations = {}

    async def investigate_anomaly(
        self, query: str, context_id: int | None = None
    ) -> tuple[InvestigationStep, str]:
        # strategy:
        # get or create context
        # get user's query
        # start investigation planning
        # execute steps
        # return results

        if context_id and context_id in self.conversations:
            context = self.conversations[context_id]
        else:
            context_id = str(uuid.uuid4())
            context = ConversationContext(conversation_id=context_id)
            self.conversations[context_id] = context

        user_query = UserQuery(query_text=query, context_id=context_id)

        logger.info(f"Starting investigation for context {context_id}")
        plan = await self.investigation_planner.create_plan(
            query=user_query, context=context
        )
        context.current_investigation = plan

        logger.info(f"Investigation plan created with {len(plan.steps)} steps")
        logger.info(f"Hypothesis: {plan.hypothesis}")
        logger.info(f"Priority dimensions: {plan.priority_dimensions}")

        logger.info("Executing investigation steps...")
        for step in plan.steps:
            logger.info(f"Step - action - {step.action}")
            logger.info(f"Step - reasoning - {step.reasoning}")

            result = self.tool_executor.execute_step(step)
            context.executed_steps.append(result)

            if result.success:
                logger.info(f"Step {step.step_id} executed successfully.")
                for finding in result.key_findings:
                    logger.info(f"Finding: {finding}")
            else:
                logger.error(
                    f"Step {step.step_id} failed with error: {result.error_message}"
                )

        context.insights = await self.insights_generator.generate_insights(
            plan=plan, results=context.executed_steps
        )

        return plan, context_id

    async def follow_up_conversation(
        self,
        query: str,
        context_id: str,
    ):
        # strategy:
        # get context
        # get user's query
        # re-run anomaly investigation with context
        # return results

        if context_id not in self.conversations:
            raise ValueError(f"Context ID {context_id} not found.")

        context = self.conversations[context_id]
        context.user_feedback.append(query)

        investigation_after_feedback = await self.investigate_anomaly(
            query=query, context_id=context_id
        )

        return investigation_after_feedback
