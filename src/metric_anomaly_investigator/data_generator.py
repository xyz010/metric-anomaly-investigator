import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json
import uuid
import logging
import sqlite3

logger = logging.getLogger(__name__)
START_DATE = datetime(2026, 1, 25)
END_DATE = datetime(2026, 2, 1)
TOTAL_USERS = 50_000


PLATFORMS = {"ios": 0.45, "android": 0.40, "web": 0.15}
COUNTRIES = {"US": 0.40, "IN": 0.25, "BR": 0.15, "UK": 0.10, "DE": 0.05, "FR": 0.05}
CHANNELS = {"organic": 0.50, "paid_social": 0.25, "referral": 0.15, "paid_search": 0.10}
TIERS = {"free": 0.80, "pro": 0.18, "enterprise": 0.02}
APP_VERSIONS = {
    "ios": ["2.2.0", "2.2.1", "2.3.0"],
    "android": ["2.2.0", "2.3.0"],  # 2.3.0 is the buggy version
    "web": ["2.2.0"],
}


def generate_user_profiles(n_users: int = TOTAL_USERS) -> pd.DataFrame:
    user_ids = [str(uuid.uuid4()) for _ in range(n_users)]
    signup_dates = [
        (START_DATE - timedelta(days=random.randint(1, 365))).date()
        for _ in range(n_users)
    ]
    signup_platforms = np.random.choice(
        list(PLATFORMS.keys()), size=n_users, p=list(PLATFORMS.values())
    )
    signup_countries = np.random.choice(
        list(COUNTRIES.keys()), size=n_users, p=list(COUNTRIES.values())
    )
    acquisition_channels = np.random.choice(
        list(CHANNELS.keys()), size=n_users, p=list(CHANNELS.values())
    )
    signup_cohorts = [
        (START_DATE - timedelta(days=random.randint(1, 365))).date().strftime("%Y-W%U")
        for _ in range(n_users)
    ]
    user_tiers = np.random.choice(
        list(TIERS.keys()), size=n_users, p=list(TIERS.values())
    )

    user_profiles = pd.DataFrame(
        {
            "user_id": user_ids,
            "signup_date": signup_dates,
            "signup_platform": signup_platforms,
            "signup_country": signup_countries,
            "user_cohort": signup_cohorts,
            "acquisition_channel": acquisition_channels,
            "user_tier": user_tiers,
        }
    )

    return user_profiles


def generate_events(
    users_df: pd.DataFrame,
    start_date: datetime = START_DATE,
    end_date: datetime = END_DATE,
):
    """Generate event stream with planted anomaly"""
    events = []
    event_types = ["session_start", "page_view", "feature_used", "search", "share"]

    current_date = start_date

    while current_date <= end_date:
        # Day-of-week seasonality
        day_of_week = current_date.weekday()
        if day_of_week in [5, 6]:  # Weekend
            activity_multiplier = 0.80
        elif day_of_week == 0:  # Monday
            activity_multiplier = 1.15
        else:
            activity_multiplier = 1.0

        # Active users for this day (~70% of total user base)
        daily_active_rate = 0.70 * activity_multiplier
        active_users = users_df.sample(frac=daily_active_rate)

        for _, user in active_users.iterrows():
            if user["user_tier"] == "pro":
                events_per_user = np.random.poisson(12)  # Pro users more active
            elif user["user_tier"] == "enterprise":
                events_per_user = np.random.poisson(15)
            else:
                events_per_user = np.random.poisson(4)

            platform = user["signup_platform"]
            country = user["signup_country"]

            # APP VERSION LOGIC - Key for anomaly
            # ANOMALY: Android users in India on v2.3.0 have 60% drop rate after Jan 28
            # 60% of India Android users experience the bug (drop out)
            if platform == "android":
                if country == "IN" and current_date >= datetime(2026, 1, 28):
                    app_version = "2.3.0"
                    if random.random() < 0.60:
                        continue  # Skip this user (simulates crash/poor UX)
                else:
                    app_version = random.choice(APP_VERSIONS["android"])
            else:
                app_version = random.choice(APP_VERSIONS[platform])

            session_id = str(uuid.uuid4())

            for _ in range(events_per_user):
                event_time = current_date + timedelta(
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59),
                    seconds=random.randint(0, 59),
                )

                events.append(
                    {
                        "event_id": str(uuid.uuid4()),
                        "user_id": user["user_id"],
                        "event_type": random.choice(event_types),
                        "event_timestamp": event_time,
                        "platform": platform,
                        "country": country,
                        "device_type": "mobile"
                        if platform in ["ios", "android"]
                        else "desktop",
                        "app_version": app_version,
                        "session_id": session_id,
                        "properties": json.dumps(
                            {
                                "page": random.choice(
                                    ["home", "feed", "profile", "settings"]
                                )
                            }
                        ),
                    }
                )

        current_date += timedelta(days=1)

    return pd.DataFrame(events)


def generate_deployments():
    return pd.DataFrame(
        [
            {
                "deployment_id": "deployment_1",
                "deployment_date": datetime(2026, 1, 20, 10, 0, 0),
                "app_version": "2.2.1",
                "platform": "ios",
                "rollout_percentage": 1.0,
                "regions": "all",
                "deployment_type": "app_release",
            },
            {
                "deployment_id": "deploy_002",
                "deployment_date": datetime(2026, 1, 25, 14, 30),
                "app_version": "2.3.0",
                "platform": "ios",
                "rollout_percentage": 1.0,
                "regions": "all",
                "deployment_type": "app_release",
            },
            {
                "deployment_id": "deploy_003",
                "deployment_date": datetime(
                    2026, 1, 28, 9, 0
                ),  # THE PROBLEMATIC DEPLOYMENT
                "app_version": "2.3.0",
                "platform": "android",
                "rollout_percentage": 1.0,
                "regions": json.dumps(["IN", "BR"]),  # Rolled out to India and Brazil
                "deployment_type": "app_release",
            },
            {
                "deployment_id": "deploy_004",
                "deployment_date": datetime(2026, 1, 30, 16, 0),
                "app_version": "2.2.0",
                "platform": "web",
                "rollout_percentage": 1.0,
                "regions": "all",
                "deployment_type": "app_release",
            },
        ]
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting data generation...")
    users_df = generate_user_profiles()
    events_df = generate_events(users_df)
    deployments_df = generate_deployments()
    logger.info("Data generation complete.")
    logger.info(f"Generated {len(users_df)} users.")
    logger.info(f"Generated {len(events_df)} events.")
    logger.info(f"Generated {len(deployments_df)} deployments.")

    users_df.to_csv("user_profiles.csv", index=False)
    events_df.to_csv("event_stream.csv", index=False)
    deployments_df.to_csv("deployments.csv", index=False)
    logger.info("CSVs saved.")

    connection = sqlite3.connect("data/analytics.db")
    users_df.to_sql("user_profiles", connection, if_exists="replace", index=False)
    events_df.to_sql("event_stream", connection, if_exists="replace", index=False)
    deployments_df.to_sql("deployments", connection, if_exists="replace", index=False)
    connection.close()
    logger.info("Data saved to SQLite database.")
