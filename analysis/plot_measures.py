import argparse

import pandas as pd
from report_utils import plot_measures


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--breakdowns", help="codelist to use")
    parser.add_argument("--output-dir", help="output directory", required=True)
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    if args.breakdowns != "":
        breakdowns = args.breakdowns.split(",")
    else:
        breakdowns = []

    df = pd.read_csv(
        f"{ args.output_dir }/joined/measure_total_rate.csv", parse_dates=["date"]
    )
    df = df.loc[df["value"] != "[Redacted]", :]

    plot_measures(
        df,
        filename=f"{ args.output_dir }/plot_measures",
        column_to_plot="value",
        y_label="Rate per 1000",
        category=None,
    )

    for breakdown in breakdowns:
        df = pd.read_csv(
            f"{ args.output_dir }/joined/measure_{breakdown}_rate.csv",
            parse_dates=["date"],
        )
        df = df.loc[df["value"] != "[Redacted]", :]
        df["value"] = df["value"].astype(float)
        df = df.sort_values(by=["date"])

        plot_measures(
            df,
            filename=f"{ args.output_dir }/plot_measures_{breakdown}",
            column_to_plot="value",
            y_label="Rate per 1000",
            category=breakdown,
        )


if __name__ == "__main__":
    main()
