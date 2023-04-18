from cohortextractor import patients
from report_utils import generate_expectations_codes


def clinical_event(codelist, date_range, event_name, ever=False):
    """
    Returns a dictionary of event variables using `with_these_clinical_events` for a given codelist and date range.

    Args:
        codelist (Codelist): A codelist object.
        date_range (tuple): A list of two dates in the format YYYY-MM-DD.
        event_name (str): The name of the event.
        ever (bool): Whether to overwrite the date range to be on_or_before the end date.
    """
    if ever:
        date_kwargs = {"on_or_before": date_range[1]}

    else:
        date_kwargs = {"between": date_range}

    events = {
        f"{event_name}": (
            patients.with_these_clinical_events(
                codelist=codelist,
                **date_kwargs,
                returning="binary_flag",
                return_expectations={"incidence": 0.5},
            )
        ),
        f"{event_name}_code": (
            patients.with_these_clinical_events(
                codelist=codelist,
                **date_kwargs,
                returning="code",
                return_expectations={
                    "rate": "universal",
                    "category": {"ratios": generate_expectations_codes(codelist)},
                },
            )
        ),
        f"{event_name}_date": (
            patients.with_these_clinical_events(
                codelist=codelist,
                **date_kwargs,
                returning="date",
                date_format="YYYY-MM-DD",
                return_expectations={
                    "date": {
                        "earliest": "index_date",
                        "latest": "last_day_of_month(index_date)",
                    }
                },
            )
        ),
    }

    return events


def medication_event(codelist, date_range, event_name, ever=False):
    """
    Returns a dictionary of event variables using `with_these_medications` for a given codelist and date range.

    Args:
        codelist (Codelist): A codelist object.
        date_range (tuple): A list of two dates in the format YYYY-MM-DD.
        event_name (str): The name of the event.
        ever (bool): Whether to overwrite the date range to be on_or_before the end date.
    """
    if ever:
        date_kwargs = {"on_or_before": date_range[1]}

    else:
        date_kwargs = {"between": date_range}

    events = {
        f"{event_name}": (
            patients.with_these_medications(
                codelist=codelist,
                **date_kwargs,
                returning="binary_flag",
                return_expectations={"incidence": 0.5},
            )
        ),
        f"{event_name}_code": (
            patients.with_these_medications(
                codelist=codelist,
                **date_kwargs,
                returning="code",
                return_expectations={
                    "rate": "universal",
                    "category": {"ratios": generate_expectations_codes(codelist)},
                },
            )
        ),
        f"{event_name}_date": (
            patients.with_these_medications(
                codelist=codelist,
                **date_kwargs,
                returning="date",
                date_format="YYYY-MM-DD",
                return_expectations={
                    "date": {
                        "earliest": "index_date",
                        "latest": "last_day_of_month(index_date)",
                    }
                },
            )
        ),
    }

    return events


def generate_event_variables(
    codelist_1_type,
    codelist_1,
    codelist_1_date_range,
    codelist_2_type,
    codelist_2,
    codelist_2_date_range,
    ever=False,
):
    if codelist_1_type == "event":
        event_1 = clinical_event(codelist_1, codelist_1_date_range, "event_1")
    elif codelist_1_type == "medication":
        event_1 = medication_event(codelist_1, codelist_1_date_range, "event_1")
    else:
        raise Exception(f"unknown codelist_1_type: {codelist_1_type}")

    if codelist_2_type == "event":
        event_2 = clinical_event(
            codelist_2, codelist_2_date_range, "event_2", ever=ever
        )
    elif codelist_2_type == "medication":
        event_2 = medication_event(
            codelist_2, codelist_2_date_range, "event_2", ever=ever
        )
    else:
        raise Exception(f"unknown codelist_2_type: {codelist_2_type}")

    measure_variable = {
        "event_measure": (
            patients.satisfying(
                " event_1 = 1 AND event_2 = 1",
                return_expectations={"incidence": 0.5},
            )
        ),
    }

    return {**event_1, **event_2, **measure_variable}
