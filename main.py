import io
import uvicorn
import pandas as pd
from typing import List
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# import local modules
from app.models import ProductSchedule
from app.parser import extract_products_from_sheet
from app.logger import get_logger

# init logger
logger = get_logger(__name__)

# FastAPI App
app = FastAPI(title="Excel Schedule Parser", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Default: show index.html
@app.get("/")
async def root():
    return FileResponse("static/index.html")


# API: /health
@app.get("/health")
def health_check():
    logger.info("Health check endpoint hit")
    return {"status": "ok", "message": "Excel Schedule Parser API", "version": "1.0.0"}


# API: /parse url
@app.post("/parse", response_model=List[ProductSchedule])
async def parse_excel(file: UploadFile = File(...)):
    """Parse Excel file and extract product schedules (one per sheet)."""
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only Excel files are supported")

    try:
        content = await file.read()
        excel_file = io.BytesIO(content)

        # Read all sheets
        xls = pd.ExcelFile(excel_file)
        schedules = []

        for sheet_name in xls.sheet_names:
            try:
                df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
                products = await extract_products_from_sheet(df, sheet_name)
                
                # Create a ProductSchedule for each sheet
                schedules.append(
                    ProductSchedule(
                        schedule_name=sheet_name,
                        products=products,
                    )
                )
                logger.info(f"Processed sheet '{sheet_name}': {len(products)} products")
            except Exception as e:
                logger.error(f"Sheet '{sheet_name}' processing error: {e}")

        logger.info(f"Successfully processed {len(schedules)} sheets from '{file.filename}'")
        return schedules

    except Exception as e:
        logger.error(f"File processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


if __name__ == "__main__":
    logger.info("Starting Interior Schedule Extraction Server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)
