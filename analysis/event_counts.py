import argparse
import functools
from pathlib import Path

import numpy as np
import pandas as pd
from analysis.report_utils import (
    drop_zero_practices,
    get_date_input_file,
    match_input_files,
    save_to_json,
)


def redact_and_round(x, *, base):
    """Redact values less-than 10 and then round values to nearest specified base (either 10 or 100).
    Default behaviour is to round to nearest 10.
    """

    assert base in {10, 100}

    if base == 10:
        decimals = -1
    else:
        decimals = -2

    x = x if x >= 10 else 0
    x = round(x, ndigits=decimals)
    return int(x)


redact_and_round_to_nearest_100 = functools.partial(redact_and_round, base=100)
redact_and_round_to_nearest_10 = functools.partial(redact_and_round, base=10)


def replace_zero_with_redacted(x):
    return x if x > 0 else "[REDACTED]"


def get_summary_stats(df, df_practices_dropped):
    required_columns = {"patient_id", "event_measure", "practice"}
    assert required_columns.issubset(set(df.columns))
    assert required_columns.issubset(set(df_practices_dropped.columns))

    unique_patients = df["patient_id"].unique()
    num_events = df["event_measure"].sum()
    patients_with_events = df.loc[df["event_measure"] == 1, "patient_id"].unique()

    unique_practices = df["practice"].unique()
    unique_practices_with_events = df_practices_dropped["practice"].unique()

    return {
        "unique_patients": unique_patients,
        "num_events": num_events,
        "unique_practices": unique_practices,
        "unique_practices_with_events": unique_practices_with_events,
        "patients_with_events": patients_with_events,
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=str, required=True)
    parser.add_argument("--output-dir", type=str, required=True)
    return parser.parse_args()


def generate_latest_week_range(latest_week_start):
    latest_week_start = pd.to_datetime(latest_week_start)
    latest_week_end = latest_week_start + pd.DateOffset(6)

    latest_week_range = (
        f"{latest_week_start:%Y-%m-%d} - {latest_week_end:%Y-%m-%d} inclusive"
    )

    return latest_week_range


def main():
    args = parse_args()

    patients = []
    patients_with_events = []
    practices = []
    practice_with_events = []
    events = {}
    events_weekly = {}

    for file in Path(args.input_dir).rglob("*"):
        if match_input_files(file.name):
            date = get_date_input_file(file.name)
            df = pd.read_feather(file)
            df["date"] = date

            df_practices_dropped = drop_zero_practices(df, "event_measure")

            summary_stats = get_summary_stats(df, df_practices_dropped)
            events[date] = summary_stats["num_events"]
            patients.extend(summary_stats["unique_patients"])
            patients_with_events.extend(summary_stats["patients_with_events"])
            practices.extend(summary_stats["unique_practices"])
            practice_with_events.extend(summary_stats["unique_practices_with_events"])

        if match_input_files(file.name, weekly=True):
            date = get_date_input_file(file.name, weekly=True)
            df = pd.read_feather(file)
            df["date"] = date
            num_events = df.loc[:, "event_measure"].sum()
            events_weekly[date] = num_events

    # there should only be one key in events_weekly, but we take the max anyway
    latest_week = max(events_weekly.keys())
    latest_month = max(events.keys())
    events_in_latest_week = replace_zero_with_redacted(
        redact_and_round_to_nearest_100(events_weekly[latest_week])
    )

    total_events = replace_zero_with_redacted(
        redact_and_round_to_nearest_100(sum(events.values()))
    )
    total_patients = replace_zero_with_redacted(
        redact_and_round_to_nearest_100(len(np.unique(patients)))
    )
    unique_patients_with_events = replace_zero_with_redacted(
        redact_and_round_to_nearest_100(len(np.unique(patients_with_events)))
    )

    total_practices = redact_and_round_to_nearest_10(len(np.unique(practices)))
    total_practices_with_events = redact_and_round_to_nearest_10(
        len(np.unique(practice_with_events))
    )
    events_in_latest_period = replace_zero_with_redacted(
        redact_and_round_to_nearest_100(events[max(events.keys())])
    )

    save_to_json(
        {
            "total_events": total_events,
            "total_patients": total_patients,
            "unique_patients_with_events": unique_patients_with_events,
            "events_in_latest_period": events_in_latest_period,
            "total_practices": total_practices,
            "total_practices_with_events": total_practices_with_events,
            "events_in_latest_week": events_in_latest_week,
            "latest_week": generate_latest_week_range(latest_week),
            "latest_month": pd.to_datetime(latest_month).strftime("%Y-%m"),
        },
        f"{args.output_dir}/event_counts.json",
    )


if __name__ == "__main__":
    main()
