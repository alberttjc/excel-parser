# LLM model
EXTRACTION_MODEL = "gemini-3-flash-preview"

# Header Aliases
HEADER_ALIASES = {
    "doc_code": ["doc_code", "reference", "code", "ref", "sku", "item no", "model"],
    "product_name": ["item", "product", "name", "title", "description"],
    "brand": ["brand", "manufacturer", "supplier", "make", "mfr"],
    "colour": ["colour", "color", "col", "finish color"],
    "finish": ["finish", "surface", "texture", "sheen", "polished", "matt"],
    "material": ["material", "mat", "composition", "fabric", "species"],
    "width": ["width", "w", "w(mm)", "width (mm)"],
    "length": ["length", "l", "depth", "d", "l(mm)", "d(mm)"],
    "height": ["height", "h", "height (mm)", "thickness"],
    "qty": ["qty", "quantity", "count", "units", "pcs"],
    "rrp": ["price", "cost", "rrp", "unit price", "$"],
    "feature_image": ["image", "picture", "photo", "img"],
    "product_description": [
        "product description",
        "short description",
        "desc",
        "overview",
    ],
    "product_details": ["details", "specifications", "specs", "remarks", "notes"],
}

# Prompts
PRODUCT_EXTRACTION_PROMPT = """You are an expert extractor of structured product data from unstructured 
architectural schedules. Always be deterministic, schema-faithful, and explicit when inferring 
missing values. Never include PII or contact details in fields not intended for them.
"""

# run_extraction.py
PRODUCT_EXTRACTION_INSTRUCTIONS = """
Populate every field in the Product schema from the provided text block.

CRITICAL RULES:
1. BRAND: Extract ONLY the manufacturer name (e.g., 'Polytec'). Remove addresses, websites, phone numbers, and contact names.
2. PRODUCT_NAME: Identify the most accurate product name using product type, description, model prefix or code (e.g., 'Iconic Carpet 50/2833'). Details can also be found in the description.
3. PRODUCT_DESCRIPTION: A professional one-sentence summary (max 12 words). Avoid technical jargon (e.g., 'A premium wool-blend carpet designed for luxury residential spaces').
4. PRODUCT_DETAILS: Format all warranty, notes and installation info as a semicolon-separated list (e.g., 'Warranty: 15 years; Note: TO BE INSTALLED IN ACCORDANCE WITH AS/NZS 2455.1:2007').
5. COLOUR/FINISH/MATERIAL: Be specific. If it's a 'Gold Scheme' or has a 'Satin' finish, capture that accurately. Material can be about the composition of the product.
6. DIMENSIONS: Convert to millimetres (mm). '3.66m' -> 3660.
7. QTY/RRP: Extract the numbers. Remove currency symbols for RRP (e.g., '$150' -> 150.0)

If a value is missing: use empty string for text fields, 0 for numbers.

EXAMPLE OUTPUT:
{
  "doc_code": "L1",
  "product_name": "Minimalist Pendant Light",
  "brand": "Lighting Co",
  "colour": "Black",
  "finish": "Brushed Brass",
  "material": "Metal",
  "width": 300,
  "length": 300,
  "height": 600,
  "qty": 1,
  "rrp": 489.0,
  "feature_image": "blackpendantlight.jpg",
  "product_description": "A simple pendant light ideal for modern interiors.",
  "product_details": "Install at 2.4m height; supplied with dimmable bulb."
}
"""

HEADER_MAPPING_PROMPT = """You are an expert at mapping messy Excel headers to a canonical product schema.
The canonical fields are: doc_code, product_name, brand, colour, finish, material, width, length, height, qty, rrp, product_description, product_details.
Map the provided list of raw headers to these canonical names. Only include mappings you are confident about.
"""
