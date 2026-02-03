from metric_anomaly_investigator.models import InvestigationStep, StepResult
from metric_anomaly_investigator.db.mock_warehouse import MockDataWarehouse
import traceback
from metric_anomaly_investigator.settings import settings


class ToolExecutor:
    def __init__(self, warehouse: MockDataWarehouse):
        self.warehouse = warehouse

    def _execute_query_metric(self, parameters: dict) -> dict:
        results = self.warehouse.query_metric(
            metric_name=parameters["metric_name"],
            time_range=tuple(parameters["time_range"]),
            dimensions=parameters["dimensions"],
            filters=parameters["filters"],
        )
        return {"metric_data": [r.model_dump() for r in results]}

    def _execute_segmentation(self, parameters: dict) -> dict:
        results = self.warehouse.get_dimensional_breakdown(
            metric_name=parameters["metric_name"],
            dimension=parameters["dimension"],
            time_range=tuple(parameters["time_range"]),
            baseline_range=tuple(parameters["baseline_range"]),
            min_drop_threshold=parameters["min_drop_threshold"],
        )
        return {"segmented_data": [r.model_dump() for r in results]}

    def _execute_deployment_check(self, parameters: dict) -> dict:
        results = self.warehouse.check_deployments(
            time_range=tuple(parameters["time_range"]),
            platform=parameters["platform"],
        )
        return {"deployments": [r.model_dump() for r in results]}

    def _execute_retention_analysis(self, parameters: dict) -> dict:
        results = self.warehouse.analyze_cohort_retention(
            cohort_date=parameters["cohort_date"],
            retention_days=parameters.get("retention_days", [1, 7, 30]),
            filters=parameters.get("filters", {}),
        )
        return {"retention_data": [results]}

    def _execute_statistical_test(self, parameters: dict) -> dict:
        result = self.warehouse.run_statistical_test(
            metric_name=parameters["metric_name"],
            control_filters=parameters["control_filters"],
            treatment_filters=parameters["treatment_filters"],
            time_range=tuple(parameters["time_range"]),
        )
        return {"statistical_test_result": result}

    def _extract_findings(self, action: str, data: dict) -> list[str]:
        findings = []
        if action == "query_metric":
            metric_data = data.get("metric_data", [])
            if metric_data:
                findings.append(
                    f"Queried {len(metric_data)} data points for the metric."
                )
        elif action == "segment_by_dimension":
            segmented_data = data.get("segmented_data", [])
            if segmented_data:
                findings.append(f"Segmented data into {len(segmented_data)} groups.")
        elif action == "check_deployments":
            deployments = data.get("deployments", [])
            if deployments:
                findings.append(
                    f"Found {len(deployments)} deployments in the specified time range."
                )
        elif action == "analyze_retention":
            retention_data = data.get("retention_data", [])
            if retention_data:
                findings.append("Cohort retention analysis completed.")
        elif action == "statistical_test":
            test_result = data.get("statistical_test_result", {})
            if test_result:
                findings.append("Statistical test executed.")
        return findings

    def _compute_confidence(self, action: str, data: dict) -> float:
        match action:
            case "segment_by_dimension":
                segments = data.get("segmented_data", [])
                if len(segments) == 0:  # low confidence
                    return 0.3

                avg_sample_size = sum(s["sample_size"] for s in segments) / len(
                    segments
                )

                if avg_sample_size > 1000:
                    return 0.9
                elif avg_sample_size > 100:
                    return 0.7
                else:
                    return 0.5
            case "check_deployments":
                deployments = data.get("deployments", [])
                if len(deployments) > 0:
                    return 0.8
                else:
                    return 0.4

        return settings.DEFAULT_MODEL_CONFIDENCE

    def execute_step(self, step: InvestigationStep) -> StepResult:
        try:
            match step.action:
                case "query_metric":
                    data = self._execute_query_metric(step.parameters)
                case "segment_by_dimension":
                    data = self._execute_segmentation(step.parameters)
                case "check_deployments":
                    data = self._execute_deployment_check(step.parameters)
                case "analyze_retention":
                    data = self._execute_retention_analysis(step.parameters)
                case "statistical_test":
                    data = self._execute_statistical_test(step.parameters)
                case _:
                    raise ValueError(f"Unknown action: {step.action}")

            findings = self._extract_findings(step.action, data)
            confidence = self._compute_confidence(step.action, data)

            return StepResult(
                step_id=step.step_id,
                success=True,
                data=data,
                key_findings=findings,
                confidence_score=confidence,
            )

        except Exception as e:
            return StepResult(
                step_id=step.step_id,
                success=False,
                error_message=str(e) + "\n" + traceback.format_exc(),
                key_findings=[],
                confidence_score=0.0,
            )
