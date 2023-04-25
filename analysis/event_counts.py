# load each input file and count the number of unique patients and number of events
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from report_utils import (
    drop_zero_practices,
    get_date_input_file,
    match_input_files,
    save_to_json,
)


def round_to_nearest_100(x):
    return int(round(x, -2))


def round_to_nearest_10(x):
    return int(round(x, -1))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=str, required=True)
    parser.add_argument("--output-dir", type=str, required=True)
    return parser.parse_args()


def get_unique_patients(df):
    return df.loc[:, "patient_id"].unique()


def get_number_of_events(df):
    return df.loc[:, "event_measure"].sum()


def get_unique_practices(df):
    return df.loc[:, "practice"].unique()


def get_patients_with_events(df):
    df_subset = df.loc[df["event_measure"] == 1, ["patient_id", "event_measure"]]
    return df_subset.loc[:, "patient_id"].unique()


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
            df = pd.read_csv(file)
            df["date"] = date
            num_events = get_number_of_events(df)
            events[date] = num_events
            unique_patients = get_unique_patients(df)
            unique_patients_with_events = get_patients_with_events(df)
            patients.extend(unique_patients)
            patients_with_events.extend(unique_patients_with_events)
            unique_practices = get_unique_practices(df)

            df_practices_dropped = drop_zero_practices(df, "event_measure")
            unique_practices_with_events = get_unique_practices(df_practices_dropped)

            practices.extend(unique_practices)
            practice_with_events.extend(unique_practices_with_events)

        if match_input_files(file.name, weekly=True):
            date = get_date_input_file(file.name, weekly=True)
            df = pd.read_csv(file)
            df["date"] = date
            num_events = get_number_of_events(df)
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
