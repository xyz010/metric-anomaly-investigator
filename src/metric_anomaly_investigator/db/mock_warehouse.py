from datetime import datetime
from sqlite3 import connect
from typing import Any, Tuple, Literal

from scipy import stats

from metric_anomaly_investigator.schemas import (
    MetricDataPoint,
    DimensionalBreakdown,
    Deployment,
)
from metric_anomaly_investigator.settings import settings

SUPPORTED_METRICS = Literal["dau", "wau", "events_per_user"]
ALLOWED_COLUMNS = ["platform", "country", "device_type", "app_version", "event_type"]
MIN_DROP_THRESHOLD = 0.10  # 10%


class MockDataWarehouse:
    def __init__(self, db_path: str = settings.DB_URL):
        self.db_path = db_path

    def _build_query(
        self,
        metric_name: str,
        time_range: Tuple[str, str],
        dimensions: list[str],
        filters: dict[str, str],
    ) -> str:
        start_date, end_date = time_range
        params = [start_date, end_date]

        dims_for_select = ""
        dims_for_groupby = ""

        if dimensions:
            dims_for_select = ", " + ", ".join(dimensions)
            dims_for_groupby = ", " + ", ".join(dimensions)

        filter_clauses = ""
        if filters:
            for col, val in filters.items():
                filter_clauses += f" AND {col} = ?"
                params.append(val)

        match metric_name:
            case "dau":
                query = f"""
                    SELECT DATE(event_timestamp) as date,
                    COUNT(DISTINCT user_id) as value
                    {dims_for_select}
                    FROM event_stream
                    WHERE DATE(event_timestamp) >= ? AND DATE(event_timestamp) <= ?
                    {filter_clauses}
                    GROUP BY DATE(event_timestamp) {dims_for_groupby}
                    ORDER BY DATE(event_timestamp)
                    """
            case "wau":
                query = f"""
                    SELECT STRFTIME('%Y-%W', event_timestamp) as week,
                    COUNT(DISTINCT user_id) as value
                    {dims_for_select}
                    FROM event_stream
                    WHERE DATE(event_timestamp) >= ? AND DATE(event_timestamp) <= ?
                    {filter_clauses}
                    GROUP BY STRFTIME('%Y-%W', event_timestamp) {dims_for_groupby}
                    ORDER BY week
                    """
            case "events_per_user":
                query = f"""
                    SELECT DATE(event_timestamp) as date,
                    CAST(COUNT(*) AS FLOAT) / NULLIF(COUNT(DISTINCT user_id), 0) as value
                    {dims_for_select}
                    FROM event_stream
                    WHERE DATE(event_timestamp) >= ? AND DATE(event_timestamp) <= ?
                    {filter_clauses}
                    GROUP BY DATE(event_timestamp) {dims_for_groupby}
                    ORDER BY DATE(event_timestamp)
                    """
            case _:
                raise ValueError(
                    f"Unsupported metric: {metric_name}. Supported: {SUPPORTED_METRICS}"
                )

        return query, params

    def _parse_timestamp(
        self, metric_name: SUPPORTED_METRICS, row_dict: dict
    ) -> datetime:
        match metric_name:
            case "dau" | "events_per_user":  # "YYYY-MM-DD"
                return datetime.strptime(row_dict["date"], "%Y-%m-%d")
            case "wau":  # "YYYY-WW"
                week_on_year = row_dict["week"]
                year = int(week_on_year[:4])
                week = int(week_on_year[5:])
                return datetime.strptime(f"{year}-W{week:02d}-1", "%G-W%V-%u")
            case _:
                raise ValueError(
                    f"Unsupported metric for timestamp parsing: {metric_name}"
                )

    def query_metric(
        self,
        metric_name: str,
        time_range: Tuple[str, str],
        dimensions: list[str] | None = [],
        filters: dict[str, str] | None = {},
    ) -> list[MetricDataPoint]:
        """
        Query aggregated metric over time

        Args:
            metric_name: 'dau', 'wau', 'events_per_user', etc.
            time_range: ('2026-01-25', '2026-02-01')
            dimensions: ['platform', 'country'] - group by these
            filters: {'platform': 'android'} - filter rows

        Returns:
            list of MetricDataPoint with values over time
        """
        # strategy:
        # TODO - validate inputs
        # TODO - check for column validation
        # build query + execute
        # parse results

        query, params = self._build_query(metric_name, time_range, dimensions, filters)

        with connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            cols = [d[0] for d in cursor.description]
            rows = cursor.fetchall()

        # parse results into MetricDataPoint list
        results = []
        for row in rows:
            row_dict = dict(zip(cols, row))
            dim_values = {}
            if dimensions:
                for dim in dimensions:
                    dim_values[dim] = str(row_dict.get(dim, ""))

            results.append(
                MetricDataPoint(
                    timestamp=self._parse_timestamp(metric_name, row_dict),
                    value=float(row_dict["value"]),
                    dimensions=dim_values,
                )
            )

        return results

    def _aggregate_metric_by_dimension(
        self,
        metric_data: list[MetricDataPoint],
        dimension: str,
    ) -> dict[str, list[float]]:
        agg: dict[str, list[float]] = {}
        for point in metric_data:
            dim_value = point.dimensions.get(dimension, "unknown")
            if dim_value not in agg:
                agg[dim_value] = [0.0, 0]  # sum, count
            agg[dim_value][0] += point.value
            agg[dim_value][1] += 1
        return agg

    def get_dimensional_breakdown(
        self,
        metric_name: str,
        dimension: str,
        time_range: Tuple[str, str],
        baseline_range: Tuple[str, str],
        min_drop_threshold: float = MIN_DROP_THRESHOLD,
    ) -> list[DimensionalBreakdown]:
        """
        Compares two time periods baseline vs current across a dimension.
        Useful guide: https://dashthis.com/blog/metrics-and-dimensions/#metrics-vs-dimensions
        """
        # strategy:
        # get metric per dimension -> baseline
        # get metric per dimension -> current period
        # calculate percentage change
        # filter by min_drop_threshold

        baseline = self.query_metric(
            metric_name=metric_name,
            time_range=baseline_range,
            dimensions=[dimension],
        )
        current = self.query_metric(
            metric_name=metric_name,
            time_range=time_range,
            dimensions=[dimension],
        )

        baseline_agg = self._aggregate_metric_by_dimension(baseline, dimension)
        current_agg = self._aggregate_metric_by_dimension(current, dimension)

        breakdowns = []
        for dim_value, (curr_sum, curr_count) in current_agg.items():
            curr_avg = curr_sum / curr_count if curr_count > 0 else 0.0
            base_sum, base_count = baseline_agg.get(dim_value, [0.0, 0])
            base_avg = base_sum / base_count if base_count > 0 else 0.0

            if base_avg == 0:
                pct_change = 0.0
            else:
                pct_change = (curr_avg - base_avg) / base_avg

            if pct_change <= -min_drop_threshold:
                breakdowns.append(
                    DimensionalBreakdown(
                        dimension_name=dimension,
                        dimension_value=dim_value,
                        before_value=base_avg,
                        after_value=curr_avg,
                        pct_change=pct_change,
                        sample_size=curr_count,
                    )
                )
        return breakdowns

    def check_deployments(
        self, time_range: Tuple[str, str], platform: str | None = None
    ) -> list[Deployment]:
        """
        Gets deployemnts in time range and platform
        """

        # strategy:
        # build query + execute
        # parse results

        query = """
            SELECT deployment_id, deployment_date, app_version, platform, regions, rollout_percentage
            FROM deployments
            WHERE DATE(deployment_date) >= ? AND DATE(deployment_date) <= ?
        """
        params = [time_range[0], time_range[1]]
        if platform:
            query += " AND platform = ?"
            params.append(platform)

        with connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            cols = [d[0] for d in cursor.description]
            rows = cursor.fetchall()
        results = []
        for row in rows:
            row_dict = dict(zip(cols, row))
            results.append(
                Deployment(
                    deployment_id=row_dict["deployment_id"],
                    deployment_date=datetime.strptime(
                        row_dict["deployment_date"], "%Y-%m-%d %H:%M:%S"
                    ),
                    app_version=row_dict["app_version"],
                    platform=row_dict["platform"],
                    regions=row_dict["regions"].split(","),
                    rollout_percentage=float(row_dict["rollout_percentage"]),
                )
            )
        return results

    def analyze_cohort_retention(
        self,
        cohort_date: str,
        retention_days: list[int] = [1, 7, 30],
        filters: dict[str, str] | None = None,
    ) -> dict[str, float]:
        """
        Calculate retention rates for cohort

        Returns: {'day_1': 0.65, 'day_7': 0.42, 'day_30': 0.28}
        Inspired by https://www.moesif.com/docs/user-analytics/cohort-retention-analysis/
        """
        # find total pool of users
        # for each retention day:
        #   find users active on that day
        #   calculate rate

        cohort_size_query = """
            SELECT COUNT(*)
            FROM user_profiles
            WHERE DATE(signup_date) = ?
            """
        params = [cohort_date]
        if filters:
            for col, val in filters.items():
                cohort_size_query += f" AND {col} = ?"
                params.append(val)

        with connect(self.db_path) as conn:
            cohort_size = conn.execute(cohort_size_query, params).fetchone()[0]

        if cohort_size == 0:
            return {f"day_{day}": 0.0 for day in retention_days}

        retention_rates = {}
        for day in retention_days:
            retention_query = """
                SELECT COUNT(DISTINCT event_stream.user_id)
                FROM event_stream
                JOIN user_profiles ON event_stream.user_id = user_profiles.user_id
                WHERE DATE(user_profiles.signup_date) = ?
                AND DATE(event_stream.event_timestamp) = DATE(?, '+' || ? || ' days')
            """
            retention_params = [cohort_date, cohort_date, day]

            if filters:
                for col, val in filters.items():
                    retention_query += f" AND user_profiles.{col} = ?"
                    retention_params.append(val)

            with connect(self.db_path) as conn:
                retained_users = conn.execute(
                    retention_query, retention_params
                ).fetchone()[0]

            retention_rates[f"day_{day}"] = retained_users / cohort_size

        return retention_rates

    def run_statistical_test(
        self,
        metric_name: str,
        control_filters: dict[str, str],
        treatment_filters: dict[str, str],
        time_range: Tuple[str, str],
    ) -> dict[str, Any]:
        """
        Compare two segments statistically

        Returns: {
            'control_mean': 4.5,
            'treatment_mean': 3.2,
            'p_value': 0.003,
            'significant': True
        }
        """

        # strategy:
        # get metrics for both segments
        # perform t-test

        control_data = self.query_metric(
            metric_name=metric_name,
            time_range=time_range,
            filters=control_filters,
        )
        treatment_data = self.query_metric(
            metric_name=metric_name,
            time_range=time_range,
            filters=treatment_filters,
        )
        control_values = [point.value for point in control_data]
        treatment_values = [point.value for point in treatment_data]
        _, p_value = stats.ttest_ind(control_values, treatment_values, equal_var=False)
        control_mean = (
            sum(control_values) / len(control_values) if control_values else 0.0
        )
        treatment_mean = (
            sum(treatment_values) / len(treatment_values) if treatment_values else 0.0
        )
        significant = p_value < 0.05
        return {
            "control_mean": control_mean,
            "treatment_mean": treatment_mean,
            "p_value": p_value,
            "significant": significant,
        }
