import io
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_excel_file():
    """Create a minimal in-memory Excel file for testing"""
    buffer = io.BytesIO()
    df = pd.DataFrame(
        {
            "doc_code": ["F64", "F65"],
            "product_name": ["Study Chair", "Office Desk"],
            "brand": ["Example Brand", "Another Brand"],
            "width": [600, 1200],
            "qty": [4, 1],
            "rrp": [299.99, 599.99],
        }
    )
    df.to_excel(buffer, index=False, sheet_name="Sheet1")
    buffer.seek(0)
    return (
        "test.xlsx",
        buffer,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@pytest.fixture
def sample_dataframe():
    """Sample pandas DataFrame for parser tests"""
    return pd.DataFrame(
        {
            "doc_code": ["F64", "F65", "F66"],
            "product_name": ["Chair", "Desk", "Table"],
            "width": [600, 1200, 800],
            "qty": [4, 1, 2],
            "rrp": [299.99, 599.99, 199.99],
        }
    )
