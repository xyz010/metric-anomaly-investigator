import asyncio
import logging
import traceback
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table

from metric_anomaly_investigator.agent import MetricAnomalyAgent
from metric_anomaly_investigator.schemas import InsightReport

logger = logging.getLogger(__name__)
console = Console()

# Android users in India on v2.3.0 experience 60% drop after Jan 28
GROUND_TRUTH = {
    "platform": "android",
    "country": "IN",
    "app_version": "2.3.0",
    "deployment_id": "deploy_003",
    "anomaly_date": "2026-01-28",
}

TEST_CASES = [
    {
        "id": "clear_signal",
        "query": "We're seeing a drop in daily active users starting January 28th. Can you investigate?",
        "difficulty": "easy",
    },
    {
        "id": "misleading",
        "query": "iOS users are complaining about crashes. Please investigate the DAU drop",
        "difficulty": "medium",
    },
    {
        "id": "vague_query",
        "query": "Something seems off with our metrics lately",
        "difficulty": "hard",
    },
]


@dataclass
class EvalResult:
    test_id: str
    difficulty: str
    root_cause_recall: float
    root_cause_details: dict
    deployment_match: bool
    segment_android: bool
    segment_india: bool
    confidence: float
    error: str | None = None

    @property
    def passed(self) -> bool:
        """
        Definition of success
        """
        return (
            self.root_cause_details.get("platform", False)
            and self.root_cause_details.get("region", False)
            and self.deployment_match
        )


def score_root_cause(report: InsightReport) -> dict:
    """
    To check if the root cause contains the necessary info
    """
    root_cause_lower = report.root_cause.lower()

    found = {
        "platform": "android" in root_cause_lower,
        "region": "india" in root_cause_lower
        or " in " in root_cause_lower.replace("in", " in "),
        "version": "2.3.0" in report.root_cause,
        "date": "28" in report.root_cause or "january" in root_cause_lower,
    }

    segments_str = str(report.affected_segments).lower()
    if not found["region"]:
        found["region"] = "india" in segments_str or "'in'" in segments_str

    recall = sum(found.values()) / len(found)
    return {"recall": recall, "details": found}


def score_deployment_match(report: InsightReport) -> bool:
    """
    To check if the app deployment is correctly identified
    """
    for event in report.correlated_events:
        event_lower = event.lower()
        if "deploy_003" in event_lower:
            return True
        if "2.3.0" in event and "android" in event_lower:
            return True

    root_cause_lower = report.root_cause.lower()

    if "deploy_003" in root_cause_lower:
        return True

    if "2.3.0" in report.root_cause and "android" in root_cause_lower:
        return True
    return False


def score_affected_segments(report: InsightReport) -> dict:
    """
    Affected segments are android and India in this eval
    """
    segments_str = str(report.affected_segments).lower()
    root_cause_lower = report.root_cause.lower()

    return {
        "has_android": "android" in segments_str or "android" in root_cause_lower,
        "has_india": "india" in segments_str or "'in'" in segments_str,
    }


async def run_single_eval(agent: MetricAnomalyAgent, test_case: dict) -> EvalResult:
    test_id = test_case["id"]
    difficulty = test_case["difficulty"]

    try:
        console.print(
            f"\n[bold blue]Running: {test_id}[/bold blue] (difficulty: {difficulty})"
        )
        console.print(f"  Query: {test_case['query'][:60]}...")

        _, context_id = await agent.investigate_anomaly(test_case["query"])
        report = agent.conversations[context_id].insights

        if not report:
            return EvalResult(
                test_id=test_id,
                difficulty=difficulty,
                root_cause_recall=0.0,
                root_cause_details={},
                deployment_match=False,
                segment_android=False,
                segment_india=False,
                confidence=0.0,
                error="No report generated",
            )

        root_cause_scores = score_root_cause(report)
        deployment_match = score_deployment_match(report)
        segments = score_affected_segments(report)

        return EvalResult(
            test_id=test_id,
            difficulty=difficulty,
            root_cause_recall=root_cause_scores["recall"],
            root_cause_details=root_cause_scores["details"],
            deployment_match=deployment_match,
            segment_android=segments["has_android"],
            segment_india=segments["has_india"],
            confidence=report.confidence_score,
        )

    except Exception as e:
        logger.error(f"Error in {test_id}: {e}")
        logger.error(traceback.format_exc())
        return EvalResult(
            test_id=test_id,
            difficulty=difficulty,
            root_cause_recall=0.0,
            root_cause_details={},
            deployment_match=False,
            segment_android=False,
            segment_india=False,
            confidence=0.0,
            error=str(e),
        )


def print_results(results: list[EvalResult]):
    """Print evaluation results as a formatted table."""
    console.print("\n")
    console.print("=" * 80)
    console.print("[bold]EVALUATION RESULTS[/bold]", justify="center")
    console.print("=" * 80)

    # Results table
    table = Table(title="Test Case Results")
    table.add_column("Test ID", style="cyan")
    table.add_column("Difficulty")
    table.add_column("Root Cause Recall", justify="right")
    table.add_column("Platform", justify="center")
    table.add_column("Region", justify="center")
    table.add_column("Deployment", justify="center")
    table.add_column("Pass", justify="center")

    for r in results:
        platform = "✓" if r.root_cause_details.get("platform") else "✗"
        region = "✓" if r.root_cause_details.get("region") else "✗"
        deployment = "✓" if r.deployment_match else "✗"
        passed = "[green]PASS[/green]" if r.passed else "[red]FAIL[/red]"

        if r.error:
            passed = f"[red]ERROR: {r.error[:20]}[/red]"

        table.add_row(
            r.test_id,
            r.difficulty,
            f"{r.root_cause_recall:.0%}",
            platform,
            region,
            deployment,
            passed,
        )

    console.print(table)

    # Aggregate stats
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    avg_recall = sum(r.root_cause_recall for r in results) / total if total > 0 else 0

    console.print("\n[bold]Aggregate Scores[/bold]")
    console.print(f"  Pass Rate: {passed}/{total} ({passed / total:.0%})")
    console.print(f"  Avg Root Cause Recall: {avg_recall:.0%}")
    console.print(
        f"  Deployment Match Rate: {sum(1 for r in results if r.deployment_match)}/{total}"
    )

    console.print("\n" + "=" * 80)
    overall = "[green]PASS[/green]" if passed >= total * 0.5 else "[red]FAIL[/red]"
    console.print(f"[bold]OVERALL: {overall}[/bold]", justify="center")
    console.print("=" * 80)


async def run_eval(test_cases: list[dict] | None = None):
    if test_cases is None:
        test_cases = TEST_CASES

    agent = MetricAnomalyAgent()
    console.print(
        f"[dim]Model: {agent.investigation_planner.agent.model.model_name}[/dim]"
    )
    console.print(f"[dim]Running {len(test_cases)} test cases...[/dim]")

    results = []
    for test_case in test_cases:
        result = await run_single_eval(agent, test_case)
        results.append(result)

    print_results(results)
    return results


def main():
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s - %(message)s",
    )
    asyncio.run(run_eval())


if __name__ == "__main__":
    main()
