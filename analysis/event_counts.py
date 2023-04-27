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


def round_to_nearest(x, *, base):
    return base * round(x / base)


round_to_nearest_100 = functools.partial(round_to_nearest, base=100)
round_to_nearest_10 = functools.partial(round_to_nearest, base=10)


def get_summary_stats(df):
    required_columns = {"patient_id", "event_measure", "practice"}
    assert required_columns.issubset(set(df.columns))

    unique_patients = df["patient_id"].unique()
    num_events = df["event_measure"].sum()
    unique_practices = df["practice"].unique()
    patients_with_events = df.loc[df["event_measure"] == 1, "patient_id"].unique()

    return {
        "unique_patients": unique_patients,
        "num_events": num_events,
        "unique_practices": unique_practices,
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
            # TODO: think about whether we should calculate all of the stats on the dropped data or not
            summary_stats = get_summary_stats(df_practices_dropped)
            events[date] = summary_stats["num_events"]
            patients.extend(summary_stats["unique_patients"])
            patients_with_events.extend(summary_stats["patients_with_events"])
            practices.extend(summary_stats["unique_practices"])

        if match_input_files(file.name, weekly=True):
            date = get_date_input_file(file.name, weekly=True)
            df = pd.read_feather(file)
            df["date"] = date
            num_events = df.loc[:, "event_measure"].sum()
            events_weekly[date] = num_events

    # there should only be one key in events_weekly, but we take the max anyway
    latest_week = max(events_weekly.keys())
    latest_month = max(events.keys())
    events_in_latest_week = round_to_nearest_100(events_weekly[latest_week])
    total_events = round_to_nearest_100(sum(events.values()))
    total_patients = round_to_nearest_100(len(np.unique(patients)))
    unique_patients_with_events = round_to_nearest_100(
        len(np.unique(patients_with_events))
    )
    total_practices = round_to_nearest_10(len(np.unique(practices)))
    total_practices_with_events = round_to_nearest_10(
        len(np.unique(practice_with_events))
    )
    events_in_latest_period = round_to_nearest_100(events[max(events.keys())])

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
