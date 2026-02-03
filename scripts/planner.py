from metric_anomaly_investigator.investigation_planner import InvestigationPlanner
from metric_anomaly_investigator.models import UserQuery
import asyncio


async def main():
    planner = InvestigationPlanner()
    query = UserQuery(
        query_text="There was a sudden drop in daily active users on 2026-02-01. Investigate possible causes."
    )
    plan = await planner.create_plan(query=query)
    for step in plan.steps:
        print(f"Step {step.step_id}: {step.action.value}")
        print(f"Parameters: {step.parameters}")
        print(f"Reasoning: {step.reasoning}\n")


if __name__ == "__main__":
    asyncio.run(main())
