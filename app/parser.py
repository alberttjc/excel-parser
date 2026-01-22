"""Product data parser for architectural schedules using AI enrichment."""

import re
import asyncio
import pandas as pd
from typing import List, Dict, Any

from app.config import HEADER_ALIASES
from app.models import Product
from app.logger import get_logger
from app.llm import extract_header_mapping, extract_product_details_ai

logger = get_logger(__name__)


# Header Detection
def make_unique(headers: List[str]) -> List[str]:
    """Ensure duplicate headers are made unique by appending suffixes."""
    seen = {}
    result = []
    for h in headers:
        clean_h = str(h).strip() if pd.notna(h) else "nan"
        if not clean_h:
            clean_h = "nan"
        count = seen.get(clean_h, 0)
        if count == 0:
            result.append(clean_h)
        else:
            result.append(f"{clean_h}_{count}")
        seen[clean_h] = count + 1
    return result


def find_header_row(df: pd.DataFrame, threshold: float = 0.7) -> int | None:
    """Find header row using completeness heuristic."""
    if df.empty:
        return None

    row_completeness = df.notnull().mean(axis=1)
    candidates = row_completeness[row_completeness >= threshold]

    if len(candidates) == 0:
        logger.warning(f"No header row found above threshold {threshold}")
        return None

    header_idx = candidates.index[0]
    logger.info(
        f"Header row found at index {header_idx} (density: {row_completeness[header_idx]:.2%})"
    )
    return header_idx


def normalise_headers(df: pd.DataFrame) -> Dict[str, str]:
    """Map raw headers to canonical Product fields using stable heuristic."""
    mapping = {}
    cols = [str(c).strip().lower() for c in df.columns]

    # Pass 1: Exact matches
    for canonical, aliases in HEADER_ALIASES.items():
        for alias in aliases:
            if alias.lower() in cols:
                idx = cols.index(alias.lower())
                mapping[canonical] = df.columns[idx]
                break

    # Pass 2: Substring matches (min 3 chars)
    for col in df.columns:
        c = str(col).strip().lower()
        if any(c == str(v).lower() for v in mapping.values()):
            continue

        for canonical, aliases in HEADER_ALIASES.items():
            if canonical in mapping:
                continue
            if any(len(a) >= 3 and a.lower() in c for a in aliases):
                mapping[canonical] = col
                break

    logger.info(f"Heuristic mapping: matched {len(mapping)} fields")
    return mapping


def prepare_data_frame(df: pd.DataFrame, header_row_idx: int) -> pd.DataFrame:
    """Extract data rows and filter out completely empty rows."""
    headers = make_unique(df.iloc[header_row_idx].tolist())
    df_data = df.iloc[header_row_idx + 1 :].copy()
    # Lower threshold to keep sparse vertical rows (brand, desc rows)
    df_data = df_data[df_data.notnull().any(axis=1)]
    df_data.columns = headers
    return df_data.reset_index(drop=True)


# Data Enrichment
async def _extract_batch(unique_texts: List[str]) -> Dict[str, Dict[str, Any]]:
    """Extract product data from unique text blocks with concurrency control."""
    semaphore = asyncio.Semaphore(5)

    async def extract_with_semaphore(text: str):
        async with semaphore:
            specs = await extract_product_details_ai(text)
            return text, specs.model_dump(exclude_none=True)

    results = await asyncio.gather(*[extract_with_semaphore(t) for t in unique_texts])
    return dict(results)


def _merge_extracted_data(
    df: pd.DataFrame, extracted_df: pd.DataFrame, force_fields: List[str]
) -> pd.DataFrame:
    """Merge extracted results: force overwrite for key fields, placeholder check for others."""
    for col in extracted_df.columns:
        if col not in df.columns:
            continue

        is_placeholder = (
            df[col].astype(str).str.upper().isin(["TBD", "", "NONE", "0", "0.0", "NAN"])
            | df[col].isna()
        )
        has_match = extracted_df[col].notna() & (extracted_df[col] != "")
        mask = (is_placeholder | (col in force_fields)) & has_match

        if df[col].dtype != object:
            df[col] = df[col].astype(object)

        df.loc[mask, col] = extracted_df.loc[mask, col]

    return df


async def extract_product_data(df: pd.DataFrame) -> pd.DataFrame:
    """Extract and fill product data from text fields (batched and deduplicated)."""
    # Combine text sources with labels for better extraction context
    search_text = (
        df[["product_name", "product_description", "product_details", "brand"]]
        .apply(
            lambda row: "\n".join(
                f"{col}: {val}"
                for col, val in row.items()
                if pd.notna(val) and str(val).strip()
            ),
            axis=1,
        )
        .str.strip()
    )

    unique_texts = search_text[search_text != ""].unique().tolist()
    if not unique_texts:
        logger.info("No text data to extract, skipping data extraction")
        return df

    logger.info(
        f"Extracting data from {len(df)} rows ({len(unique_texts)} unique text blocks)"
    )

    # Extract and map results
    results = await _extract_batch(unique_texts)
    extracted_df = pd.DataFrame(
        [results.get(t, {}) for t in search_text], index=df.index
    )

    # Merge with intelligent overwrite logic
    force_fields = ["product_name", "brand", "product_description", "product_details"]
    return _merge_extracted_data(df, extracted_df, force_fields)


# Normalization
def clean_numeric_string(value: Any) -> int:
    """Extract numeric value and convert metres to mm."""
    if pd.isna(value) or value == "" or value == "TBD":
        return 0

    s = str(value).strip().upper()
    match = re.search(r"(\d+(?:\.\d+)?)", s)
    if not match:
        return 0

    num = float(match.group(1))

    # Convert metres to mm
    if "METRE" in s or (re.search(r"\bM\b", s) and "MM" not in s):
        return int(num * 1000)

    return int(num)


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Final cleaning: strip text, normalize dimensions, clean currency/qty."""
    # Text fields
    text_cols = [
        f for f, t in Product.model_fields.items() if "str" in str(t.annotation).lower()
    ]
    # Fields to keep in original case
    preserve_case = ["product_description", "product_details", "feature_image"]

    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()
            df[col] = df[col].replace("nan", "", regex=False)
            # Uppercase all text fields except descriptions and details
            if col not in preserve_case:
                df[col] = df[col].str.upper()

    # Dimensions
    for dim in ["width", "height", "length"]:
        if dim in df.columns:
            df[dim] = df[dim].apply(clean_numeric_string)

    # Currency
    if "rrp" in df.columns:
        df["rrp"] = pd.to_numeric(
            df["rrp"].astype(str).str.replace(r"[^\d.]", "", regex=True),
            errors="coerce",
        ).fillna(0.0)

    # Quantity
    if "qty" in df.columns:
        df["qty"] = df["qty"].astype(str).str.extract(r"(\d+)").fillna(1).astype(int)

    return df


def is_meaningful(row: Dict[str, Any]) -> bool:
    """Heuristic to exclude metadata, footers, and mostly empty rows."""
    # 1. doc_code sanity
    code = str(row.get("doc_code", "")).strip()
    if not code or code.lower() in ["nan", "none", "*", "-", "."]:
        return False

    # 2. Content check: must have identity (name/brand/desc) OR multiple attributes
    id_fields = ["product_name", "brand", "product_description"]
    attr_fields = ["colour", "finish", "material", "product_details"]

    has_identity = any(str(row.get(f, "")).strip() for f in id_fields)
    attr_count = sum(1 for f in attr_fields if str(row.get(f, "")).strip())

    return has_identity or attr_count >= 2


# Main Pipeline
async def extract_products_from_sheet(
    df: pd.DataFrame, sheet_name: str
) -> List[Product]:
    """
    Main extraction pipeline: Header detection → Mapping → Grouping → Enrichment → Validation.

    Returns list of validated Product objects.
    """
    logger.info(f"Starting extraction pipeline for sheet: {sheet_name}")

    # 1. Find header row
    header_idx = find_header_row(df)
    if header_idx is None:
        logger.error(f"Failed to find header row in sheet '{sheet_name}'")
        return []

    # 2. Prepare data
    df_data = prepare_data_frame(df, header_idx)

    # 3. Map headers (heuristic + automated)
    mapping = normalise_headers(df_data)
    try:
        auto_map = await extract_header_mapping(list(df_data.columns))
        mapping.update(
            {
                k: v
                for k, v in auto_map.items()
                if k not in mapping and v in df_data.columns
            }
        )
    except Exception as e:
        logger.warning(f"Automated header mapping failed: {e}")

    logger.info(f"Final mapping: {mapping}")
    logger.info(f"Total mapped fields: {len(mapping)}")

    # 4. Group by doc_code
    doc_col = mapping.get("doc_code")
    if not doc_col:
        logger.error(
            f"No doc_code column found in sheet '{sheet_name}' - cannot group products"
        )
        return []
    df_data["group_id"] = df_data[doc_col].notna().cumsum()
    num_groups = df_data["group_id"].max()
    logger.info(f"Grouped data into {num_groups} products")

    # 5. Aggregate multi-row products
    agg_logic = {
        c: (
            (lambda x: "\n".join(x.dropna().astype(str).str.strip()).strip())
            if df_data[c].dtype == "object"
            else "first"
        )
        for c in df_data.columns
        if c != "group_id"
    }
    product_df = (
        df_data.groupby("group_id")
        .agg(agg_logic)
        .rename(columns={v: k for k, v in mapping.items()})
    )

    # 6. Catch-all for unmapped columns
    unmapped = [
        c for c in product_df.columns if c not in Product.model_fields and c != doc_col
    ]
    if unmapped:
        product_df["product_details"] = product_df[unmapped].apply(
            lambda r: "\n".join(
                f"{c}: {v}" for c, v in r.items() if pd.notna(v) and str(v).strip()
            ),
            axis=1,
        )

    # 7. Extract & normalize product data
    product_df = product_df.reindex(columns=list(Product.model_fields.keys()))
    logger.info("Starting product data extraction...")
    product_df = await extract_product_data(product_df)
    product_df = normalize_dataframe(product_df)
    logger.info("Product data extraction and normalization complete")

    # 8. Apply filtering
    mask = product_df.apply(is_meaningful, axis=1)
    product_df = product_df[mask].reset_index(drop=True)
    logger.info(f"Filtered to {len(product_df)} meaningful products")

    # Save dataframe for debugging
    product_df.to_csv("./data/products_df.csv", index=False)

    # 9. Validate and return products
    products = []
    for r in product_df.to_dict("records"):
        try:
            products.append(Product.model_validate(r))
        except Exception as e:
            logger.warning(f"Validation failed for product {r.get('doc_code')}: {e}")

    logger.info(
        f"Successfully extracted {len(products)} products from sheet '{sheet_name}'"
    )
    return products


if __name__ == "__main__":
    # used mainly for testing and debugging
    async def main():
        excel_file = "./data/schedule_sample1.xlsx"
        xls = pd.ExcelFile(excel_file)

        total_products = 0
        for sheet_name in xls.sheet_names:
            try:
                logger.info(f"Extracting products from sheet: {sheet_name}")
                df = pd.read_excel(io=excel_file, sheet_name=sheet_name)
                products, warnings = await extract_products_from_sheet(
                    df=df, sheet_name=sheet_name
                )
                total_products += len(products)
                logger.info(f"Extraction completed from sheet: {sheet_name}")
            except Exception as e:
                import traceback

                logger.error(f"Sheet processing error: {e}")
                logger.error(traceback.format_exc())

        logger.info(f"Total products extracted: {total_products}")

    asyncio.run(main())
