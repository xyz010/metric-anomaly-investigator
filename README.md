# Metric Anomaly Investigator

An autonomous AI agent that investigates metric anomalies through iterative multi-step reasoning.

## The Problem

As a platform engineer, I've spent countless hours trying to find the source of bugs, weird behavior, and production incidents. The process would almost always look the same: manually opening up Sentry to identify key components and services involved, then manually exploring CloudWatch with ad-hoc SQL queries, time segmentation, and comparing distributions of nominal behavior.

The Metric Anomaly Investigator fixes that using agentic AI via iterative multi-step reasoning.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MetricAnomalyAgent                           │
│                      (Orchestrator)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────────┐         ┌─────────────────┐               │
│   │  Step Decision  │         │    Insights     │               │
│   │     Agent       │         │    Generator    │               │
│   │                 │         │      Agent      │               │
│   │ Decides next    │         │                 │               │
│   │ investigation   │         │ Synthesizes     │               │
│   │ action          │         │ findings into   │               │
│   └────────┬────────┘         │ final report    │               │
│            │                  └────────▲────────┘               │
│            │                           │                        │
│            ▼                           │                        │
│   ┌─────────────────┐                  │                        │
│   │  Tool Executor  │                  │                        │
│   │                 │──────────────────┘                        │
│   │ query_metric    │   (when ready)                            │
│   │ segment_by_dim  │                                           │
│   │ check_deploys   │                                           │
│   │ analyze_retain  │                                           │
│   │ statistical_test│                                           │
│   └────────┬────────┘                                           │
│            │                                                    │
│            ▼                                                    │
│   ┌─────────────────┐                                           │
│   │ Mock Warehouse  │                                           │
│   │    (SQLite)     │                                           │
│   └─────────────────┘                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Components

1. **MetricAnomalyAgent** - Main orchestrator that coordinates the investigation loop
2. **Step Decision Agent** - AI agent that decides the next investigation action based on current findings
3. **Tool Executor** - Executes investigation actions against the data warehouse
4. **Insights Generator Agent** - AI agent that synthesizes all findings into a final report
5. **Mock Warehouse** - SQLite-based data store with synthetic metrics, deployments, and user data

### Investigation Flow

```
User Query
    │
    ▼
┌─────────────────────────────────────┐
│  Step Decision Agent decides next   │◄──────┐
│  action based on findings so far    │       │
└─────────────────┬───────────────────┘       │
                  │                           │
                  ▼                           │
         ┌───────────────────┐                │
         │ generate_insights?│                │
         └───────┬───────────┘                │
                 │                            │
        No ──────┴────── Yes                  │
        │                 │                   │
        ▼                 ▼                   │
┌───────────────┐  ┌─────────────────┐        │
│ Tool Executor │  │ Insights Agent  │        │
│ executes step │  │ generates report│        │
└───────┬───────┘  └────────┬────────┘        │
        │                   │                 │
        │                   ▼                 │
        │            Final Report             │
        │                                     │
        └─────────────────────────────────────┘
```

## Design Choices

1. **Iterative ReAct Pattern** - Instead of generating a full plan upfront, the agent decides one action at a time based on accumulated findings. This allows adaptive investigation that responds to what the data reveals.

2. **Two Sub-Agents** - Separation of concerns between step decision (what to investigate next) and insight synthesis (what does it all mean).

3. **PydanticAI Framework** - Structured outputs at every stage using Pydantic models, ensuring type safety and clear contracts between components.

4. **Synthetic Data** - Generated realistic data to focus on the agentic workflow. The data patterns and schemas mirror real-world analytics scenarios.

## Installation

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Anthropic API key

### Setup

1. Clone the repository:
```bash
git clone https://github.com/xyz010/metric-anomaly-investigator.git
cd metric-anomaly-investigator
```

2. Install dependencies:
```bash
uv sync --all-groups
```

3. Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY=your-api-key
```

## Usage

### Running the CLI

Run the interactive CLI to investigate metric anomalies:
```bash
uv run metric-anomaly-investigator
```

### Example Questions

Once the CLI is running, you can ask questions like:
- "DAU dropped significantly after January 28th. What's causing it?"
- "Android engagement seems down this week. Can you investigate?"
- "Is there a problem with the Android app after the recent deployment?"

Type `exit` to quit the CLI.

### Running Evaluations

Run the evaluation suite to test agent performance:
```bash
uv run python evals/eval.py
```

## Development

Install development dependencies:
```bash
uv sync --all-groups
```

Run tests:
```bash
uv run pytest
```

## Project Structure

```
metric-anomaly-investigator/
├── src/metric_anomaly_investigator/
│   ├── cli.py                 # CLI entry point
│   ├── agent/
│   │   ├── metric_anomaly_agent.py  # Main orchestrator
│   │   ├── tool_executor.py         # Action execution
│   │   └── prompts.py               # System prompts
│   ├── mock_warehouse/        # Mock data warehouse
│   ├── schemas/               # Pydantic models
│   └── settings.py            # Configuration
├── evals/                     # Evaluation suite
└── pyproject.toml
```
