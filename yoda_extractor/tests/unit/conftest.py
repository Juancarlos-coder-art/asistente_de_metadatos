import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture
def simple_df():
    return pd.DataFrame({
        "name": ["Alice", "Bob", None],
        "age": [30, 25, 40],
        "city": ["Madrid", "Barcelona", "Seville"],
    })


@pytest.fixture
def date_df():
    return pd.DataFrame({
        "date": ["2020-01-15", "2021-06-30", "2022-12-01"],
        "year": ["2020", "2021", "2022"],
        "month": ["01", "06", "12"],
        "day": ["15", "30", "01"],
    })
