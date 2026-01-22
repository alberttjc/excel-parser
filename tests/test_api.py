import io
import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": "Excel Schedule Parser API",
        "version": "1.0.0",
    }


def test_root_returns_html(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_parse_rejects_non_excel(client: TestClient):
    response = client.post(
        "/parse", files={"file": ("test.txt", io.BytesIO(b"not excel"), "text/plain")}
    )
    assert response.status_code == 400
    assert "Only Excel files are supported" in response.json()["detail"]


def test_parse_accepts_excel(client: TestClient, sample_excel_file):
    filename, buffer, content_type = sample_excel_file
    response = client.post("/parse", files={"file": (filename, buffer, content_type)})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    schedules = response.json()
    assert len(schedules) == 1
    assert "schedule_name" in schedules[0]
    assert "products" in schedules[0]
    assert isinstance(schedules[0]["products"], list)


def test_parse_empty_excel(client: TestClient):
    buffer = io.BytesIO()
    import pandas as pd

    pd.DataFrame().to_excel(buffer, index=False)
    buffer.seek(0)
    response = client.post(
        "/parse",
        files={
            "file": (
                "empty.xlsx",
                buffer,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200
