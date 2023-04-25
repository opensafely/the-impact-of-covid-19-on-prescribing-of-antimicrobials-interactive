import argparse
import csv
import json
import mimetypes
from base64 import b64encode
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Markup, StrictUndefined


ENVIRONMENT = Environment(
    loader=FileSystemLoader("."),
    undefined=StrictUndefined,
)


def display_image(src, data):
    src = Path(src)

    encoded = b64encode(src.read_bytes()).decode("utf8")
    mtype, _ = mimetypes.guess_type(str(src))

    return Markup(
        f'<img src="data:{mtype};base64,{encoded}" title="Image generated from file: {data}">'
    )


ENVIRONMENT.globals["display_image"] = display_image


def data_from_csv(path):
    """
    Read data from a csv file
    Args:
        path: path to the csv file
    Reuturns:
        list of lists (rows) containing the data
    """
    with open(path, "r") as f:
        reader = csv.reader(f)
        return [row for row in reader]


def data_from_json(path):
    """
    Read data from a json file
    Args:
        path: path to the json file
    Reuturns:
        dict containing the data
    """
    with open(path, "r") as f:
        return json.load(f)


def get_data(
    output_dir,
    population="all",
    breakdowns=[],
    codelist_1_name="",
    codelist_1_link="",
    codelist_2_name="",
    codelist_2_link="",
    time_value="",
    time_scale="",
    time_event="",
    start_date="",
    end_date="",
):
    """
    Get data to render the report
    Args:
        output_dir (str): the output directory all the files are in
        population (str): population of the report
        breakdowns (list): list of demographic breakdowns
        codelist_1_name (str): name of the first codelist
        codelist_1_link (str): link to the first codelist (OpenCodelists)
        codelist_2_name (str): name of the second codelist
        codelist_2_link (str): link to the second codelist (OpenCodelists)
        time_value (str): time value for the report
        time_scale (str): time scale for the report
        time_event (str): time event for the report
        start_date (str): start date for the report
        end_date (str): end date for the report
    Returns:
        dict containing the data
    """

    codelist_url_root = "https://opencodelists.org/codelist/"
    codelist_1_link = codelist_url_root + codelist_1_link
    codelist_2_link = codelist_url_root + codelist_2_link

    top_5_1_path = output_dir / "joined/top_5_code_table_1.csv"
    top_5_2_path = output_dir / "joined/top_5_code_table_2.csv"
    summary_table_path = output_dir / "event_counts.json"

    top_5_1_data = data_from_csv(top_5_1_path)
    top_5_2_data = data_from_csv(top_5_2_path)
    summary_table_data = data_from_json(summary_table_path)

    figures = {
        "decile": {
            "path": output_dir / "deciles_chart.png",
            "data": output_dir / "joined/measure_practice_rate_deciles.csv",
        },
        "population": {
            "path": output_dir / "plot_measures.png",
            "data": output_dir / "joined/measure_total_rate.csv",
        },
        "sex": {
            "path": output_dir / "plot_measures_sex.png",
            "data": output_dir / "joined/measure_sex_rate.csv",
        },
        "age": {
            "path": output_dir / "plot_measures_age.png",
            "data": output_dir / "joined/measure_age_rate.csv",
        },
        "imd": {
            "path": output_dir / "plot_measures_imd.png",
            "data": output_dir / "joined/measure_imd_rate.csv",
        },
        "region": {
            "path": output_dir / "plot_measures_region.png",
            "data": output_dir / "joined/measure_region_rate.csv",
        },
        "ethnicity": {
            "path": output_dir / "plot_measures_ethnicity.png",
            "data": output_dir / "joined/measure_ethnicity_rate.csv",
        },
    }

    breakdowns_options = {
        "age": {
            "title": "Age",
            "link": None,
            "description": "Age is divided into 10 year age bands.",
            "figure": figures["age"],
        },
        "ethnicity": {
            "title": "Ethnicity",
            "description": "Ethnicity is categorised into 6 high-level groups, as defined by the codelist below.",
            "link": "https://www.opencodelists.org/codelist/opensafely/ethnicity-snomed-0removed/2e641f61/",
            "link_description": "Ethnicity codelist",
            "figure": figures["ethnicity"],
        },
        "sex": {
            "title": "Sex",
            "link": None,
            "description": "Sex is grouped by 'M' and 'F'. Patients whose sex is not recorded as either 'M' or 'F' are not included in this analysis to prevent disclosure concerns resulting from low event counts.",
            "figure": figures["sex"],
        },
        "imd": {
            "title": "Index of Multiple Deprivation",
            "description": "Index of Multiple Deprivation breakdown is presented as quintiles, based on English indices of deprivation 2019. These quintile range from 1 (most deprived) to 5 (least deprived) See the link below for more details.",
            "link": "https://www.gov.uk/government/statistics/english-indices-of-deprivation-2019",
            "link_description": "English Indices of Deprivation 2019",
            "figure": figures["imd"],
        },
        "region": {
            "title": "Region",
            "link": None,
            "description": "Region is categorised into 9 regions in England. A patients' region is determined as the region of the practice they are registered at.",
            "figure": figures["region"],
        },
    }
    # open file from root directory
    breakdowns = [breakdowns_options[breakdown] for breakdown in breakdowns]

    # population logic

    if population == "adults":
        population_definition = "all patients aged 18 and over, who are registered with a general practice at the start of each month"

    elif population == "children":
        population_definition = "all patients aged under 18, who are registered with a general practice at the start of each month"

    else:
        population_definition = (
            "all patients registered with a general practice at the start of each month"
        )

    report_data = {
        "population": population_definition,
        "decile": figures["decile"],
        "population_plot": figures["population"],
        "breakdowns": breakdowns,
        "top_5_1_data": top_5_1_data,
        "top_5_2_data": top_5_2_data,
        "summary_table_data": summary_table_data,
        "figures": figures,
        "codelist_1_link": codelist_1_link,
        "codelist_2_link": codelist_2_link,
        "codelist_1_name": codelist_1_name,
        "codelist_2_name": codelist_2_name,
        "start_date": start_date,
        "end_date": end_date,
        "time_value": time_value,
        "time_scale": time_scale,
        "time_event": time_event,
    }
    return report_data


def render_report(report_path, data):
    """
    Render the report template with data
    Args:
        report_path: path to the report template
        data: data to render

    """
    template = ENVIRONMENT.get_template("analysis/report_template.html")
    return template.render(data)


def write_html(html, output_dir):
    """
    Write the html to a file in the output directory
    Args:
        html: html to write
        output_dir: directory to write to
    """
    with open(output_dir + "/report.html", "w") as f:
        f.write(html)


def render(output_dir, **kwargs):
    report_data = get_data(output_dir=output_dir, **kwargs)
    template = ENVIRONMENT.get_template("analysis/report_template.html")
    report = args.output_dir / "report.html"
    report.write_text(template.render(report_data))


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--population", type=str, default="all")
    parser.add_argument("--breakdowns", action="append", default=[])
    parser.add_argument("--start-date", type=str, default="")
    parser.add_argument("--end-date", type=str, default="")
    parser.add_argument("--codelist-1-name", type=str, default="")
    parser.add_argument("--codelist-2-name", type=str, default="")
    parser.add_argument("--codelist-1-link", type=str, default="")
    parser.add_argument("--codelist-2-link", type=str, default="")
    parser.add_argument("--time-value", type=str, default="")
    parser.add_argument("--time-scale", type=str, default="")
    parser.add_argument("--time-event", type=str, default="")
    return parser


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    render(**vars(args))
