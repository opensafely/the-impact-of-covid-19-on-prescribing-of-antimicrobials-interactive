import json
import re
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


BASE_DIR = Path(__file__).parents[1]
OUTPUT_DIR = BASE_DIR / "output"
ANALYSIS_DIR = BASE_DIR / "analysis"
CODELIST_DIR = BASE_DIR / "codelists"


def calculate_rate(df, value_col, population_col, rate_per=1000, round_rate=False):
    """Calculates the number of events per 1,000 or passed rate_per variable of the population.
    This function operates on the given measure table in-place, adding
    a `rate` column.
    Args:
        df: A measure table.
        value_col: The name of the numerator column in the measure table.
        population_col: The name of the denominator column in the measure table.
        rate_per: Value to calculate rate per
        round: Bool indicating whether to round rate to 2dp.
    """
    if round_rate:
        rate = round(df[value_col] / (df[population_col] / rate_per), 4)

    else:
        rate = df[value_col] / (df[population_col] / rate_per)

    return rate


def relabel_sex(df):
    sex_codes = {
        "F": "Female",
        "M": "Male",
    }

    df = df.replace({"sex": sex_codes})
    return df


def generate_expectations_codes(codelist, incidence=0.5):
    if len(codelist) >= 10:
        expectations = {str(x): (1 - incidence) / 10 for x in codelist[0:10]}
    else:
        expectations = {str(x): (1 - incidence) / len(codelist) for x in codelist}

    expectations[None] = incidence
    return expectations


def save_to_json(d, filename: str):
    """Saves dictionary to json file"""
    with open(filename, "w") as f:
        json.dump(d, f)


def match_input_files(file: str, weekly=False) -> bool:
    """Checks if file name has format outputted by cohort extractor"""
    if weekly:
        pattern = (
            r"^input_weekly_20\d\d-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01])\.feather"
        )
    else:
        pattern = r"^input_20\d\d-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01])\.feather"
    return True if re.match(pattern, file) else False


def get_date_input_file(file: str, weekly=False) -> str:
    """Gets the date in format YYYY-MM-DD from input file name string"""
    # check format
    if not match_input_files(file, weekly=weekly):
        raise Exception("Not valid input file format")

    else:
        if weekly:
            date = re.search(r"input_weekly_(.*).feather", file)
        else:
            date = re.search(r"input_(.*).feather", file)
        return date.group(1)


def plot_measures(
    df,
    filename: str,
    column_to_plot: str,
    y_label: str,
    category: str = None,
    category_order: list = None,
):
    """Produce time series plot from measures table. If category is provided, one line is plotted for each sub
    category within the category column. Saves output in 'output' dir as png file.
    Args:
        df: A measure table
        column_to_plot: Column name for y-axis values
        y_label: Label to use for y-axis
        category: Name of column indicating different categories, optional
        category_order: List of categories in order to plot, optional
    """
    if category:
        df[category] = df[category].fillna("Missing")

    _, ax = plt.subplots(figsize=(15, 8))
    palette = sns.color_palette("tab10")

    if category:
        if category_order:
            for unique_category in category_order:
                df_subset = df[df[category] == unique_category].sort_values("date")

                sns.lineplot(
                    x="date",
                    y=column_to_plot,
                    data=df_subset,
                    palette=palette,
                    ax=ax,
                    label=unique_category,
                )

        else:
            for unique_category in df[category].unique():
                df_subset = df[df[category] == unique_category].sort_values("date")

                sns.lineplot(
                    x="date",
                    y=column_to_plot,
                    data=df_subset,
                    palette=palette,
                    ax=ax,
                    label=unique_category,
                )

    else:
        ax.plot(df["date"], df[column_to_plot])

    ax.set(
        ylabel=y_label,
        xlabel="Date",
        ylim=(
            0,
            1000
            if df[column_to_plot].isnull().values.all()
            else df[column_to_plot].max(),
        ),
    )

    month_locator = mdates.MonthLocator()
    ax.xaxis.set_major_locator(month_locator)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%B %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.xticks(rotation="vertical")

    if category:
        ax.legend(
            bbox_to_anchor=(1.04, 1),
            loc="upper left",
            fontsize=20,
        )

    ax.margins(x=0)
    ax.yaxis.label.set_size(25)
    ax.xaxis.label.set_size(25)
    ax.tick_params(axis="both", which="major", labelsize=20)
    plt.tight_layout()
    plt.savefig(f"{filename}.png")
    plt.close()


def calculate_variable_windows_codelist_1(
    codelist_1_frequency,
):
    """
    Calculates the date range to use for the variables based on codelist 1 and 2.
    """
    if codelist_1_frequency == "weekly":
        codelist_1_date_range = ["index_date", "index_date + 7 days"]
    else:
        codelist_1_date_range = ["index_date", "last_day_of_month(index_date)"]

    return codelist_1_date_range


def calculate_variable_windows_codelist_2(
    codelist_1_date_range,
    codelist_2_comparison_date,
    codelist_2_period_start,
    codelist_2_period_end,
):
    """
    Calculates the date range to use for the variables based on codelist 2.
    """
    if codelist_2_comparison_date == "start_date":
        codelist_2_date_range = [
            f"index_date {codelist_2_period_start} days",
            f"index_date {codelist_2_period_end} days",
        ]
    elif codelist_2_comparison_date == "end_date":
        if codelist_1_date_range[1] == "index_date + 7 days":
            codelist_2_date_range = [
                f"{codelist_1_date_range[0]} {codelist_2_period_start}",
                f"{codelist_1_date_range[1]}",
            ]
        else:
            codelist_2_date_range = [
                f"{codelist_1_date_range[0]} {codelist_2_period_start}",
                f"{codelist_1_date_range[1]}",
            ]
    else:
        codelist_2_date_range = [
            f"event_1_date {codelist_2_period_start}",
            f"event_1_date {codelist_2_period_end}",
        ]

    return codelist_2_date_range


def compute_deciles(measure_table, groupby_col, value_col, has_outer_percentiles=True):
    """
    Computes deciles and other percentiles from a measure table.

    Args:
        measure_table: the measure table to compute the percentiles from
        groupby_col: the name of the column to group by
        value_col: the name of the column to compute the percentiles for
        has_outer_percentiles: whether to compute the nine largest and nine smallest percentiles

    Returns:
    A dataframe with columns for the grouping column, the value column, and the percentile.
    """
    quantiles = np.arange(0.1, 1, 0.1)
    if has_outer_percentiles:
        quantiles = np.concatenate(
            [quantiles, np.arange(0.01, 0.1, 0.01), np.arange(0.91, 1, 0.01)]
        )

    percentiles = (
        measure_table.groupby(groupby_col)[value_col]
        .quantile(pd.Series(quantiles))
        .reset_index()
    )
    percentiles["percentile"] = round(percentiles["level_1"] * 100)
    percentiles = percentiles.rename(columns={value_col: "value"})

    return percentiles[[groupby_col, "value", "percentile"]]


def deciles_chart(df, filename, period_column=None, column=None, title="", ylabel=""):
    """
    Create a deciles chart from a dataframe and save it to a file.

    Args:
        df: the dataframe to plot
        filename: the name of the file to save the chart to
        period_column: the name of the column containing the date or datetime values
        column: the name of the column to plot the deciles of
        title: the title of the chart
        ylabel: the label of the y-axis of the chart
    """

    fig, ax = plt.subplots(figsize=(15, 8))

    linestyles = {
        "decile": {"line": "b--", "linewidth": 1, "label": "Decile"},
        "median": {"line": "b-", "linewidth": 1.5, "label": "Median"},
        "percentile": {
            "line": "b:",
            "linewidth": 0.8,
            "label": "1st-9th, 91st-99th percentile",
        },
    }

    df = compute_deciles(
        measure_table=df,
        groupby_col=period_column,
        value_col=column,
        has_outer_percentiles=True,
    )

    label_seen = []
    for percentile in range(1, 100):
        data = df[df["percentile"] == percentile]
        add_label = False

        if percentile == 50:
            style = linestyles["median"]
            add_label = True
        elif percentile < 10 or percentile > 90:
            style = linestyles["percentile"]
            if "percentile" not in label_seen:
                label_seen.append("percentile")
                add_label = True
        else:
            style = linestyles["decile"]
            if "decile" not in label_seen:
                label_seen.append("decile")
                add_label = True
        if add_label:
            label = style["label"]
        else:
            label = "_nolegend_"

        ax.plot(
            data[period_column],
            data[column],
            style["line"],
            linewidth=style["linewidth"],
            label=label,
        )

    ax.set_ylabel(ylabel, size=20, alpha=1)
    ax.set_title(title, size=14, wrap=True)
    ax.set_ylim(
        [0, 100 if df[column].isnull().values.all() else df[column].max() * 1.05]
    )
    ax.tick_params(labelsize=20)
    ax.set_xlim([df[period_column].min(), df[period_column].max()])
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=90)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%B %Y"))
    plt.xticks(sorted(df[period_column].unique()), rotation=90)
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.legend(
        bbox_to_anchor=(1.1, 0.8),
        loc="center left",
        ncol=1,
        fontsize=20,
        borderaxespad=0.0,
    )
    plt.tight_layout()
    plt.savefig(filename)
    plt.clf()


def drop_zero_practices(df, measure_count_column):
    """
    Drops practices which have had zero events for a measure
    of interest for the whole period of interest.

    Args:
        df: A measure table.
        measure_count_column: The name of the column in the measure table

    Returns:
        A measure table with practices with zero events removed.
    """

    non_zero = df.groupby("practice")[measure_count_column].any()
    return df[df["practice"].isin(non_zero[non_zero].index)]
