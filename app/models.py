from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class HeaderMapping(BaseModel):
    mapping: Dict[str, str] = Field(
        description="Map of canonical Product field names to raw Excel column names"
    )


class Product(BaseModel):
    doc_code: str = Field(default="", description="Drawing or reference code")
    product_name: str = Field(default="", description="Product display name")
    brand: str = Field(default="", description="Product brand")
    colour: str = Field(default="", description="Colour name")
    finish: str = Field(default="", description="Surface finish")
    material: str = Field(default="", description="Main material")

    # Use 0 or None as defaults for numbers
    width: int = Field(default=0, description="Width in mm")
    length: int = Field(default=0, description="Length in mm")
    height: int = Field(default=0, description="Height in mm")

    qty: int = Field(default=1, description="Quantity")
    rrp: float = Field(default=0.0, description="Recommended retail price")

    feature_image: Optional[str] = Field(
        default=None, description="Image filename (optional)"
    )
    product_description: str = Field(default="", description="Short description")
    product_details: str = Field(default="", description="Additional specifications")


class ProductSchedule(BaseModel):
    schedule_name: str
    products: List[Product]
    warnings: List[str] = Field(default_factory=list, description="List of validation or parsing warnings")
