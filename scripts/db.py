from metric_anomaly_investigator.db.mock_warehouse import (
    MockDataWarehouse,
)

warehouse = MockDataWarehouse()

# print("#--------------------------------------------------------------#")
# print("Query Metric Example")
# print("#--------------------------------------------------------------#")
# results = warehouse.query_metric(
#     metric_name="dau",
#     time_range=("2026-01-25", "2026-02-05"),
#     dimensions=["platform", "country"],
#     filters={
#         "platform": "android",
#     },
# )
# print(f"Retrieved {len(results)} data points")
# for r in results:
#     print(r)
# print("\n---\n")

# results = warehouse.query_metric(
#     metric_name="dau",
#     time_range=("2026-01-25", "2026-02-05"),
#     dimensions=["platform", "country"],
#     filters={
#         "platform": "android",
#         "country": "US",
#     },
# )
# print(f"Retrieved {len(results)} data points")
# for r in results:
#     print(r)

# print("#--------------------------------------------------------------#")
# print("Dimensional Breakdown Example")
# print("#--------------------------------------------------------------#")
# # find dimensional breakdowns of 'dau' for 'platform' between two time ranges
# dimensional_breakdown = warehouse.get_dimensional_breakdown(
#     metric_name="dau",
#     dimension="platform",
#     time_range=("2026-02-01", "2026-02-01"),
#     baseline_range=("2026-01-25", "2026-01-27"),
#     min_drop_threshold=0.10,
# )
# print(f"Found {len(dimensional_breakdown)} dimension values with significant changes")
# for db in dimensional_breakdown:
#     print(db)


# print("#--------------------------------------------------------------#")
# print("Deployment Check Example")
# print("#--------------------------------------------------------------#")
# deployments = warehouse.check_deployments(
#     time_range=("2026-01-25", "2026-02-01"),
#     platform="android",
# )
# print(f"Found {len(deployments)} deployments in the time range")
# for d in deployments:
#     print(d)

# print("#--------------------------------------------------------------#")
# print("Cohort Retention Analysis Example")
# print("#--------------------------------------------------------------#")
# retention_data = warehouse.analyze_cohort_retention(
#     cohort_date="2026-01-24",
#     retention_days=[1, 2, 3, 4, 5, 6, 7],
#     filters={"signup_platform": "ios"},
# )
# print("Cohort Retention Data:")
# for day, retained in retention_data.items():
#     print(f"Day {day}: {retained} users retained")

print("#--------------------------------------------------------------#")
print("Statistical Test Example")
print("#--------------------------------------------------------------#")
stat_test_result = warehouse.run_statistical_test(
    metric_name="dau",
    control_filters={"platform": "ios"},
    treatment_filters={"platform": "android"},
    time_range=("2026-01-25", "2026-02-05"),
)
print("Statistical Test Result:")
print(stat_test_result)
