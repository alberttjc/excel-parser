import pytest
import pandas as pd
import numpy as np
from app.parser import (
    make_unique,
    find_header_row,
    normalise_headers,
    clean_numeric_string,
    normalize_dataframe,
    prepare_data_frame,
    is_meaningful,
)


def test_make_unique():
    # Only one test for unique headers covers all cases
    headers = ["name", "name", "", np.nan]
    result = make_unique(headers)
    assert result == ["name", "name_1", "nan", "nan_1"]


def test_find_header_row():
    df = pd.DataFrame({
        "a": [np.nan, "H1", "V1"],
        "b": [np.nan, "H2", "V2"],
        "c": [np.nan, np.nan, np.nan]
    })
    # Row 1 has 66% density, Row 2 has 66%. If threshold is 0.5, Row 1 wins.
    assert find_header_row(df, threshold=0.5) == 1
    assert find_header_row(df, threshold=0.8) is None


def test_normalise_headers_logic():
    # Pass 1: Exact matches (priority)
    df1 = pd.DataFrame({"doc_code": [1], "w": [1]})
    result1 = normalise_headers(df1)
    assert result1["doc_code"] == "doc_code"
    assert result1["width"] == "w"

    # Pass 2: Substring matches (min 3 chars)
    df2 = pd.DataFrame({"width_mm": [1]})
    result2 = normalise_headers(df2)
    assert result2["width"] == "width_mm"
    
    # Negative: Substring too short (< 3 chars)
    df3 = pd.DataFrame({"w_mm": [1]})
    result3 = normalise_headers(df3)
    assert "width" not in result3


def test_clean_numeric_string():
    # Focused test on conversion and edge cases
    assert clean_numeric_string("1.5 metres") == 1500
    assert clean_numeric_string("600 mm") == 600
    assert clean_numeric_string("$299.99") == 299
    assert clean_numeric_string("TBD") == 0


def test_normalize_dataframe():
    # Single test for full normalization logic
    df = pd.DataFrame({
        "doc_code": ["  f64  "],
        "product_name": ["  Chair  "],
        "rrp": ["$299.99"],
        "qty": ["2 pieces"],
        "product_description": [" Preserve Case "]
    })
    result = normalize_dataframe(df)
    assert result["doc_code"].iloc[0] == "F64"
    assert result["product_name"].iloc[0] == "CHAIR"
    assert result["rrp"].iloc[0] == 299.99
    assert result["qty"].iloc[0] == 2
    assert result["product_description"].iloc[0] == "Preserve Case"


def test_prepare_data_frame():
    df = pd.DataFrame([["h1", "h2"], ["v1", "v2"], [np.nan, np.nan]])
    result = prepare_data_frame(df, header_row_idx=0)
    assert len(result) == 1 # Only one non-empty row
    assert list(result.columns) == ["h1", "h2"]


def test_is_meaningful_logic():
    # Test core filtering heuristics
    assert is_meaningful({"doc_code": "F64", "product_name": "Chair"}) is True
    assert is_meaningful({"doc_code": "F64", "colour": "Red", "material": "Wood"}) is True # 2 attributes
    
    # Invalid/Metadata
    assert is_meaningful({"doc_code": "CLIENT SIGNATURE"}) is False
    assert is_meaningful({"doc_code": "*"}) is False
    assert is_meaningful({"doc_code": "F64", "product_details": "Too sparse"}) is False
