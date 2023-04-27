from cohortextractor import patients


def get_demographics(children=False):
    demographic_variables = {
        "sex": (
            patients.sex(
                return_expectations={
                    "rate": "universal",
                    "category": {"ratios": {"M": 0.49, "F": 0.5, "U": 0.01}},
                }
            )
        ),
        "region": (
            patients.registered_practice_as_of(
                "index_date",
                returning="nuts1_region_name",
                return_expectations={
                    "category": {
                        "ratios": {
                            "North East": 0.1,
                            "North West": 0.1,
                            "Yorkshire and the Humber": 0.1,
                            "East Midlands": 0.1,
                            "West Midlands": 0.1,
                            "East of England": 0.1,
                            "London": 0.2,
                            "South East": 0.2,
                        }
                    }
                },
            )
        ),
        "imd": (
            patients.categorised_as(
                {
                    "Missing": "DEFAULT",
                    "Most deprived": """index_of_multiple_deprivation >=0 AND index_of_multiple_deprivation < 32844*1/5""",
                    "2": """index_of_multiple_deprivation >= 32844*1/5 AND index_of_multiple_deprivation < 32844*2/5""",
                    "3": """index_of_multiple_deprivation >= 32844*2/5 AND index_of_multiple_deprivation < 32844*3/5""",
                    "4": """index_of_multiple_deprivation >= 32844*3/5 AND index_of_multiple_deprivation < 32844*4/5""",
                    "Least deprived": """index_of_multiple_deprivation >= 32844*4/5 AND index_of_multiple_deprivation < 32844""",
                },
                index_of_multiple_deprivation=patients.address_as_of(
                    "index_date",
                    returning="index_of_multiple_deprivation",
                    round_to_nearest=100,
                ),
                return_expectations={
                    "rate": "universal",
                    "category": {
                        "ratios": {
                            "Missing": 0.05,
                            "Most deprived": 0.19,
                            "2": 0.19,
                            "3": 0.19,
                            "4": 0.19,
                            "Least deprived": 0.19,
                        }
                    },
                },
            )
        ),
    }
    if children:
        demographic_variables["age"] = patients.categorised_as(
            {
                "missing": "DEFAULT",
                "0-5": """ age_years >= 0 AND age_years < 6""",
                "6-10": """ age_years >=  6 AND age_years < 11""",
                "11-17": """ age_years >=  11 AND age_years < 18""",
            },
            return_expectations={
                "rate": "universal",
                "category": {
                    "ratios": {
                        "missing": 0.001,
                        "0-5": 0.333,
                        "6-10": 0.333,
                        "11-17": 0.333,
                    }
                },
            },
        )
    else:
        demographic_variables["age"] = patients.categorised_as(
            {
                "missing": "DEFAULT",
                "0-17": """ age_years >= 0 AND age_years < 18""",
                "18-29": """ age_years >=  18 AND age_years < 30""",
                "30-39": """ age_years >=  30 AND age_years < 40""",
                "40-49": """ age_years >=  40 AND age_years < 50""",
                "50-59": """ age_years >=  50 AND age_years < 60""",
                "60-69": """ age_years >=  60 AND age_years < 70""",
                "70-79": """ age_years >=  70 AND age_years < 80""",
                "80+": """ age_years >=  80 AND age_years < 120""",
            },
            return_expectations={
                "rate": "universal",
                "category": {
                    "ratios": {
                        "missing": 0.005,
                        "0-17": 0.125,
                        "18-29": 0.125,
                        "30-39": 0.125,
                        "40-49": 0.125,
                        "50-59": 0.125,
                        "60-69": 0.125,
                        "70-79": 0.125,
                        "80+": 0.12,
                    }
                },
            },
        )
    return demographic_variables
