import asyncio
import traceback
from metric_anomaly_investigator.metric_anomaly_agent import MetricAnomalyAgent
import logging

logger = logging.getLogger(__name__)


async def main():
    agent = MetricAnomalyAgent()
    logger.info("Starting anomaly investigation via CLI")
    logger.info("Please wait, this may take a few moments...")
    logger.info("---------------------------------------------------")
    logger.info(f"Using model: {agent.investigation_planner.agent.model.model_name}")

    logger.info("Ask me about metric drops/spikes!")
    query = "There was a sudden drop in daily active users on Android last week. Investigate the cause."

    context_id = None

    while True:
        query = input("Enter your anomaly query (or 'exit' to quit): ").strip()
        if query.lower() == "exit":
            break
        if not query:
            continue

        try:
            plan, context_id = await agent.investigate_anomaly(
                query, context_id=context_id
            )
            logger.info(f"Investigation Plan:\n{plan}\n")
        except Exception as e:
            logger.error(f"Error during investigation: {e}")
            logger.error(traceback.format_exc())


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(main())
