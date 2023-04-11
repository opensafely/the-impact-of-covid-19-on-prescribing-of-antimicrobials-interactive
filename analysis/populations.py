from cohortextractor import patients


population_filters = {
    "adults": (
        patients.satisfying(
            """
        registered AND
        NOT died AND
        age_years >= 18 AND
        age_years <= 120
        """,
            registered=patients.registered_as_of(
                "index_date",
                return_expectations={"incidence": 0.9},
            ),
            died=patients.died_from_any_cause(
                on_or_before="index_date",
                returning="binary_flag",
                return_expectations={"incidence": 0.1},
            ),
        )
    ),
    "children": (
        patients.satisfying(
            """
        registered AND
        NOT died AND
        age_years < 18
        """,
            registered=patients.registered_as_of(
                "index_date",
                return_expectations={"incidence": 0.9},
            ),
            died=patients.died_from_any_cause(
                on_or_before="index_date",
                returning="binary_flag",
                return_expectations={"incidence": 0.1},
            ),
        )
    ),
    "all": (
        patients.satisfying(
            """
        registered AND
        NOT died
        """,
            registered=patients.registered_as_of(
                "index_date",
                return_expectations={"incidence": 0.9},
            ),
            died=patients.died_from_any_cause(
                on_or_before="index_date",
                returning="binary_flag",
                return_expectations={"incidence": 0.1},
            ),
        )
    ),
}
