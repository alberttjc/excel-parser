import pytest
from pydantic import ValidationError
from app.models import Product, ProductSchedule, HeaderMapping


def test_product_with_defaults():
    product = Product()
    assert product.doc_code == ""
    assert product.product_name == ""
    assert product.brand == ""
    assert product.width == 0
    assert product.length == 0
    assert product.height == 0
    assert product.qty == 1
    assert product.rrp == 0.0
    assert product.feature_image is None


def test_product_with_values():
    product = Product(
        doc_code="F64",
        product_name="Study Chair",
        brand="Example Brand",
        width=600,
        length=600,
        height=800,
        qty=4,
        rrp=299.99,
    )
    assert product.doc_code == "F64"
    assert product.product_name == "Study Chair"
    assert product.width == 600
    assert product.qty == 4


def test_product_optional_fields():
    product = Product(feature_image="chair.jpg", product_description="A nice chair")
    assert product.feature_image == "chair.jpg"
    assert product.product_description == "A nice chair"


def test_product_serialization():
    product = Product(doc_code="F64", product_name="Chair")
    data = product.model_dump()
    assert data["doc_code"] == "F64"
    assert data["product_name"] == "Chair"
    assert data["qty"] == 1


def test_product_schedule_structure():
    schedule = ProductSchedule(
        schedule_name="Sheet1",
        products=[
            Product(doc_code="F64", product_name="Chair"),
            Product(doc_code="F65", product_name="Desk"),
        ],
    )
    assert schedule.schedule_name == "Sheet1"
    assert len(schedule.products) == 2
    assert schedule.products[0].doc_code == "F64"


def test_header_mapping_model():
    mapping = HeaderMapping(mapping={"doc_code": "Code", "product_name": "Item"})
    assert mapping.mapping["doc_code"] == "Code"
    assert mapping.mapping["product_name"] == "Item"


def test_invalid_product_type():
    with pytest.raises(ValidationError):
        Product(width="not_a_number")
