# Install project

Install dependencies:
```(bash)
uv lock --upgrade && uv sync --all-groups
```
Requires an `ANTHROPIC_API_KEY`

Create the database:
```(bash)
uv run python src/metric_anomaly_investigator/data_generator.py
```

Run the metrics anomaly agent:
```(bash)
uv run python scripts/cli.py
```

# Example questions:
1. DAU dropped significantly after January 28th. What's causing it?
2. Android engagement seems down this week. Can you investigate?
3. Is there a problem with the Android app after the recent deployment?


# Next steps
1. implement Insights agent
2. tests
3. documentation and architecture
