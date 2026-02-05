import asyncio
import logging
import traceback

from rich.console import Console

from metric_anomaly_investigator.agent import MetricAnomalyAgent
from metric_anomaly_investigator.report_formatter import print_report

logger = logging.getLogger(__name__)
console = Console()


async def async_main():
    agent = MetricAnomalyAgent()
    logger.info("Starting anomaly investigation via CLI")
    logger.info("---------------------------------------------------")
    logger.info("Two sub-agents: Step Decision + Insights Generator")

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
            context = await agent.investigate_anomaly(query, context_id=context_id)
            logger.info(f"Investigation Plan:\n{context}\n")

            report = agent.conversations[context.conversation_id].insights
            if report:
                print_report(report, console)
            else:
                logger.warning("No insights report generated.")
        except Exception as e:
            logger.error(f"Error during investigation: {e}")
            logger.error(traceback.format_exc())


def main():
    """Entry point for the CLI."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
