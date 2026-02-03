# Metric Anomaly Investigator

An autonomous AI agent that investigates metric anomalies through multi-step reasoning and planning.

## The Problem

As a platform engineer, I've spent countless of hours trying to find the source of a bug, weird behavioor and production incidents. The process would almost always look the same, manually opening up Sentry to identify key components and services involved and then manually exploring the Cloudwatch with ad-hoc SQL queris, time segmentation and comparing distributions of the nominal behavior.

The metric anomaly investigator agent fixes that using agentic AI via multi-step reasoning.

## Architecture

1. **Investigation Planner** --> An AI agent that is responsible to generate a plan to answer a user's question
2. **Tool Executor** --> The tooling necessary for the agent to perform data operations in the mock data warehouse
3. **Insights Generator** --> An AI agent that generates the insights report after the metric anomalies have been identified
4. **Metric Anomaly Agent** --> The main AI agent that executes the plan it receives from the Investigation Planner and invokes Insights Generator with its results

## Design Choices
1. I opted for using the agentic framework of PydanticAI since I am a being fan of its Pydantic models and allows us to use structure outout in every part of the agentic process.

2. For the scope of this exercise, I chose to generate synthetic data to focus more on the implementation of teh agentic workflow. However, I belive that teh generated data and tables are a good proxy of realistic patterns and schemas

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

### Running Examples

The `examples/` folder contains scripts demonstrating individual components:

```bash
# Run the investigation planner example
uv run python examples/planner_example.py

# Run the mock warehouse example
uv run python examples/warehouse_example.py
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
│   ├── cli.py              # CLI entry point
│   ├── agent/              # AI agent components
│   ├── mock_warehouse/     # Mock data warehouse
│   ├── schemas/            # Pydantic models
│   └── settings.py         # Configuration
├── examples/               # Example scripts
├── tests/                  # Test suite
└── pyproject.toml
```
