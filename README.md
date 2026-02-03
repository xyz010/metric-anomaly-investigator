# Metric Anomaly Investigator

An AI agent that analyzes metric anomalies and allows users to ask questions about a synthetic database of event streams.

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
