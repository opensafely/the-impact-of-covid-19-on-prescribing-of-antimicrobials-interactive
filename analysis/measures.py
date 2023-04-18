import argparse
from pathlib import Path

import pandas as pd
from analysis.report_utils import calculate_rate, get_date_input_file, match_input_files


def redact_and_round_column(df, col, decimals=-1):
    """Redact values less-than or equal-to 10 and then round values to nearest 10."""
    df[col] = df[col].apply(lambda x: x if x > 10 else 0)
    # `Series.round` introduces scaling and precision errors, meaning some numbers
    # aren't rounded. This isn't the case for the `round` builtin.
    df[col] = df[col].apply(round, ndigits=decimals)
    return df


def filter_data(df, filters):
    """
    Filter a DataFrame based on specified columns and their corresponding filter values.

    Args:
        df (pd.DataFrame): The input DataFrame to be filtered.
        filters (dict): A dictionary where keys are column names and values are lists of
                        the desired values for that column.

    Returns:
        pd.DataFrame: The filtered DataFrame.
    """
    for column, filter_values in filters.items():
        if column in df.columns:
            df = df.loc[df[column].isin(filter_values), :]
    return df


def calculate_total_counts(df, date, group=None, group_value=None):
    """
    Calculate the total counts for a DataFrame.

    Args:
        df (pd.DataFrame): The input DataFrame. Should contain columns "event_measure" and "date".
        date (str): The date of the input file.
        group (str, optional): The group category. Defaults to None.
        group_value (str, optional): The group value. Defaults to None.
    Returns:
        pd.DataFrame: A DataFrame (shape: (1, 5)) containing the total counts.
    """
    if not {"event_measure", "date"}.issubset(df.columns):
        raise ValueError(
            "The input DataFrame must contain 'event measure' and 'date' columns."
        )

    count = df["event_measure"].sum()
    population = df["event_measure"].count()

    row_dict = {
        "date": date,
        "event_measure": count,
        "population": population,
        "group": group,
        "group_value": group_value,
    }
    return pd.DataFrame.from_records([row_dict])


def calculate_group_counts(df, breakdown, date):
    """
    Calculate the counts for a specified group.

    Args:
        df (pd.DataFrame): The input DataFrame. Should contain a column named "breakdown".
        breakdown (str): The name of the column to group by.
        date (str): The date of the input file.

    Returns:
        pd.DataFrame: A DataFrame containing the counts for the specified group.
    """
    counts = (
        df.groupby(by=[breakdown])["event_measure"]
        .agg(["sum", "count"])
        .reset_index()
        .rename(
            columns={
                breakdown: "group_value",
                "sum": "event_measure",
                "count": "population",
            }
        )
    )
    counts["date"] = date
    counts["group"] = breakdown

    return counts


def calculate_and_redact_values(df):
    """
    Calculate the values for each group and redact where necessary.

    Args:
        df (pd.DataFrame): The input DataFrame. Should contain columns "event_measure", "population" and "group".

    Returns:
        pd.DataFrame: A DataFrame containing the calculated values.
    """
    groups = df["group"].unique()
    result = pd.DataFrame(columns=["group", "group_value", "value"])
    for group in groups:
        group_df = df.loc[df["group"] == group, :]

        if group == "practice":
            group_df.loc[:, "value"] = calculate_rate(
                group_df, "event_measure", "population"
            )
        else:
            group_df = redact_and_round_column(group_df, "event_measure", decimals=-1)
            group_df = redact_and_round_column(group_df, "population", decimals=-1)
            group_df.loc[:, "value"] = calculate_rate(
                group_df, "event_measure", "population"
            )
            group_df.loc[
                (group_df["event_measure"] == 0) | (group_df["population"] == 0),
                "value",
            ] = "[Redacted]"

        result = pd.concat([result, group_df], ignore_index=True)

    return result


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--breakdowns", type=str, required=True)
    parser.add_argument("--input_dir", type=str, required=True)
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.breakdowns == "":
        breakdowns = [x for x in args.breakdowns.split(",")]
    else:
        breakdowns = []

    breakdowns.extend(["practice", "event_1_code", "event_2_code"])

    measure_df = pd.DataFrame(
        columns=["date", "event_measure", "population", "group", "group_value"]
    )

    for file in Path(args.input_dir).iterdir():
        if match_input_files(file.name):
            filters = {
                "sex": ["M", "F"],
                "age_band": [
                    "18-19",
                    "20-29",
                    "30-39",
                    "40-49",
                    "50-59",
                    "60-69",
                    "70-79",
                    "80+",
                ],
            }
            date = get_date_input_file(file.name)
            file_path = str(file.absolute())
            df = pd.read_csv(file_path).pipe(filter_data, filters).assign(date=date)

            total_count = calculate_total_counts(
                df, date, group="total", group_value="total"
            )

            measure_df = pd.concat([measure_df, total_count], ignore_index=True)

            for breakdown in breakdowns:
                counts = calculate_group_counts(df, breakdown, date)

                measure_df = pd.concat([measure_df, counts], ignore_index=True)

    # sort by date

    measure_df = measure_df.sort_values(by=["group", "group_value", "date"])

    measure_df = calculate_and_redact_values(measure_df)
    measure_df.to_csv(f"{args.input_dir}/measure_all.csv", index=False)
    measure_for_deciles = measure_df.loc[measure_df["group"] == "practice", :]
    measure_for_deciles.to_csv(
        f"{args.input_dir}/measure_practice_rate_deciles.csv", index=False
    )


if __name__ == "__main__":
    main()
