import os
from typing import List, Dict

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.settings import ModelSettings

# import local modules
from app.models import Product, HeaderMapping
from app.logger import get_logger
from app.config import (
    EXTRACTION_MODEL,
    PRODUCT_EXTRACTION_PROMPT,
    PRODUCT_EXTRACTION_INSTRUCTIONS,
    HEADER_MAPPING_PROMPT,
)

# setup
logger = get_logger(__name__)
load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# agents
header_mapping_agent = Agent(
    model=GoogleModel(model_name=EXTRACTION_MODEL),
    output_type=HeaderMapping,
    model_settings=ModelSettings(temperature=0.2),
    instructions=HEADER_MAPPING_PROMPT,
)

extraction_agent = Agent(
    model=GoogleModel(model_name=EXTRACTION_MODEL),
    output_type=Product,
    model_settings=ModelSettings(temperature=0.2),
    system_prompt=PRODUCT_EXTRACTION_PROMPT,
    instructions=PRODUCT_EXTRACTION_INSTRUCTIONS,
)


# functions
async def extract_header_mapping(raw_headers: List[str]) -> Dict[str, str]:
    """Uses LLM to map raw headers to canonical fields."""
    try:
        result = await header_mapping_agent.run(
            f"Raw headers: {', '.join(raw_headers)}"
        )
        return result.output.mapping
    except Exception as e:
        logger.error(f"AI Header Mapping failed: {e}")
        return {}


async def extract_product_details_ai(text: str) -> Product:
    """Uses LLM to extract full structured Product data from text."""
    try:
        result = await extraction_agent.run(f"Extract from: {text}")
        return result.output
    except Exception as e:
        logger.error(f"AI Full Product Extraction failed: {e}")
        return Product()
