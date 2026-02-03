from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from metric_anomaly_investigator.schemas import InsightReport


def get_confidence_color(score: float) -> str:
    """Return color based on confidence score."""
    if score >= 0.7:
        return "green"
    elif score >= 0.4:
        return "yellow"
    return "red"


def format_confidence(score: float) -> Text:
    """Format confidence score with color."""
    color = get_confidence_color(score)
    percentage = f"{score * 100:.1f}%"
    return Text(percentage, style=f"bold {color}")


def print_report(report: InsightReport, console: Console | None = None) -> None:
    """Print a formatted InsightReport to the console."""
    if console is None:
        console = Console()

    # Header with confidence
    confidence_text = format_confidence(report.confidence_score)
    header = Text()
    header.append("Investigation Report", style="bold blue")
    header.append(" | Confidence: ")
    header.append(confidence_text)

    console.print()
    console.rule(header)
    console.print()

    # Summary
    console.print(Panel(report.summary, title="Summary", border_style="blue"))

    # Root Cause
    root_cause_color = get_confidence_color(report.confidence_score)
    console.print(
        Panel(report.root_cause, title="Root Cause", border_style=root_cause_color)
    )

    # Affected Segments Table
    if report.affected_segments:
        table = Table(title="Affected Segments", box=box.ROUNDED)
        table.add_column("Segment", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Confidence", justify="right")
        table.add_column("Description")

        for segment in report.affected_segments:
            seg_confidence = segment.get("confidence", 0)
            conf_text = format_confidence(seg_confidence)
            table.add_row(
                segment.get("segment_name", "Unknown"),
                segment.get("segment_type", "Unknown"),
                conf_text,
                segment.get("description", ""),
            )

        console.print(table)
        console.print()

    # Correlated Events
    if report.correlated_events:
        events_text = "\n".join(f"• {event}" for event in report.correlated_events)
        console.print(
            Panel(events_text, title="Correlated Events", border_style="yellow")
        )

    # Recommendations
    if report.recommendations:
        recommendations_text = "\n".join(
            f"[bold]{i + 1}.[/bold] {rec}"
            for i, rec in enumerate(report.recommendations)
        )
        console.print(
            Panel(recommendations_text, title="Recommendations", border_style="green")
        )

    # Supporting Data (key metrics only)
    if report.supporting_data:
        data = report.supporting_data
        metrics_table = Table(title="Investigation Metrics", box=box.SIMPLE)
        metrics_table.add_column("Metric", style="dim")
        metrics_table.add_column("Value", justify="right")

        key_metrics = [
            ("Steps Completed", data.get("investigation_steps_completed")),
            ("Data Points Analyzed", data.get("data_points_analyzed")),
            ("Deployments Found", data.get("deployments_found")),
            ("Avg Confidence", data.get("average_confidence_score")),
            ("Requires Follow-up", data.get("requires_followup")),
        ]

        for name, value in key_metrics:
            if value is not None:
                if isinstance(value, float):
                    value = f"{value:.2f}"
                elif isinstance(value, bool):
                    value = "Yes" if value else "No"
                metrics_table.add_row(name, str(value))

        console.print(metrics_table)

        # Key limitations if present
        limitations = data.get("key_limitations", [])
        if limitations:
            console.print()
            lim_text = "\n".join(f"⚠ {lim}" for lim in limitations)
            console.print(Panel(lim_text, title="Key Limitations", border_style="red"))

    console.print()
    console.rule(style="dim")
