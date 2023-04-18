from cohortextractor import (
    Measure,
    StudyDefinition,
    codelist_from_csv,
    params,
    patients,
)
from demographics import demographics
from event_variables import generate_event_variables
from populations import population_filters
from report_utils import (
    calculate_variable_windows_codelist_1,
    calculate_variable_windows_codelist_2,
)


codelist_1_path = params["codelist_1_path"]
codelist_1_type = params["codelist_1_type"]
codelist_2_path = params["codelist_2_path"]
codelist_2_type = params["codelist_2_type"]
time_value = int(params["time_value"])
time_ever = params["time_ever"]
time_scale = params["time_scale"]
time_event = params["time_event"]
codelist_2_comparison_date = params["codelist_2_comparison_date"]
codelist_1_frequency = params["codelist_1_frequency"]
population_definition = params["population"]
breakdowns = params["breakdowns"]

# handle dates
# TODO: handle events in the same period (week, day, month). Requires form changes


if time_scale == "weeks":
    days = time_value * 7
elif time_scale == "months":
    days = time_value * 28
elif time_scale == "years":
    days = time_value * 365
else:
    raise Exception("Unsupported time scale")

if time_event == "before":
    codelist_2_period_start = f"- {days} days"
    codelist_2_period_end = ""
else:
    raise Exception("Unsupported time event")

codelist_1 = codelist_from_csv(codelist_1_path, system="snomed", column="code")

codelist_2 = codelist_from_csv(
    codelist_2_path,
    system="snomed",
    column="code",
)

codelist_1_date_range = calculate_variable_windows_codelist_1(codelist_1_frequency)
codelist_2_date_range = calculate_variable_windows_codelist_2(
    codelist_1_date_range,
    codelist_2_comparison_date,
    codelist_2_period_start,
    codelist_2_period_end,
)

selected_population = population_filters[population_definition]
selected_demographics = {k: v for k, v in demographics.items() if k in breakdowns}

study = StudyDefinition(
    index_date="2019-01-01",
    default_expectations={
        "date": {"earliest": "2020-01-01", "latest": "2022-12-01"},
        "rate": "exponential_increase",
        "incidence": 0.1,
    },
    population=selected_population,
    age_years=patients.age_as_of(
        "index_date",
        return_expectations={
            "rate": "universal",
            "int": {"distribution": "population_ages"},
        },
    ),
    **selected_demographics,
    practice=patients.registered_practice_as_of(
        "index_date",
        returning="pseudo_id",
        return_expectations={
            "int": {"distribution": "normal", "mean": 25, "stddev": 5},
            "incidence": 0.5,
        },
    ),
    **generate_event_variables(
        codelist_1_type,
        codelist_1,
        codelist_1_date_range,
        codelist_2_type,
        codelist_2,
        codelist_2_date_range,
        ever=time_ever,
    ),
)

measures = [
    Measure(
        id="event_rate",
        numerator="event_measure",
        denominator="population",
        group_by=["practice"],
    ),
    Measure(
        id="event_code_1_rate",
        numerator="event_1",
        denominator="population",
        group_by=["event_1_code"],
    ),
    Measure(
        id="event_code_2_rate",
        numerator="event_2",
        denominator="population",
        group_by=["event_2_code"],
    ),
]

if breakdowns:
    for b in breakdowns:
        measures.append(
            Measure(
                id=f"event_{b}_rate",
                numerator="event_measure",
                denominator="population",
                group_by=[b],
            ),
        )
