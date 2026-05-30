"""Shared fixtures for the SaaS KPI dashboard test suite."""

import pandas as pd
import pytest


@pytest.fixture(scope="session")
def customers_df() -> pd.DataFrame:
    return pd.read_csv("customers.csv", parse_dates=["signup_date"])


@pytest.fixture(scope="session")
def payments_df() -> pd.DataFrame:
    return pd.read_csv("payments.csv", parse_dates=["payment_date"])


@pytest.fixture(scope="session")
def subscriptions_df() -> pd.DataFrame:
    return pd.read_csv(
        "subscriptions.csv",
        parse_dates=["start_date", "end_date"],
    )


@pytest.fixture(scope="session")
def costs_df() -> pd.DataFrame:
    return pd.read_csv("costs.csv")
