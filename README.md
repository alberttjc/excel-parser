# 📊 Excel Schedule Parser

**FastAPI service** that transforms inconsistent Excel product schedules into standardized, type-safe JSON.

## ✨ Key Features

- **Unified Consolidation Pipeline**: Automatically handles both horizontal and complex vertical/hierarchical schedules by merging context across multiple rows.
- **Robust Header Mapping**: Uses a two-pass heuristic (Exact then Substring) and a naming utility to ensure stable field mapping even with duplicate or ambiguous Excel columns.
- **AI-Driven Enrichment**: Leverages Gemini 2.5 Flash to accurately extract product identities, brands, and specifications from consolidated text blocks.
- **Data Resiliency**: Filters out metadata, empty rows, and footers (e.g., T&Cs) to produce clean, product-only datasets.

---

---

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- Google Gemini API key

### 1. Install `uv` (Package Manager)

**macOS/Linux:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/alberttjc/excel-parser.git
cd programa

# Sync dependencies and create virtual environment
uv sync --extra dev

# Configure API key
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 3. Running the Server

```bash
# Start the service
uv run main.py

```

_The API is now live at `http://localhost:8000`. Access the Web UI at `http://localhost:8000/` to upload files._

---

## 📡 API Usage

### Parse Excel File

**Endpoint:** `POST /parse`

**Sample Request:**

```bash
curl -X POST "http://localhost:8000/parse" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_schedule.xlsx"
```

**Sample Response:**

```json
[
  {
    "schedule_name": "Sheet1",
    "products": [
      {
        "doc_code": "F64",
        "product_name": "Study Chair",
        "brand": "Example Brand",
        "colour": "BLACK",
        "finish": "MATT",
        "material": "METAL",
        "width": 600,
        "length": 600,
        "height": 800,
        "qty": 4,
        "rrp": 299.99,
        "feature_image": null,
        "product_description": "A modern study chair",
        "product_details": "Warranty: 5 years"
      }
    ]
  }
]
```

---

## 📚 Endpoints

| Method | Path      | Description                                        |
| ------ | --------- | -------------------------------------------------- |
| GET    | `/`       | HTML upload interface                              |
| GET    | `/health` | Health check                                       |
| POST   | `/parse`  | Parse Excel file (returns `List[ProductSchedule]`) |

---

## 🧪 Testing

```bash
# Run all tests
uv run --with pytest --with pytest-cov pytest tests/ -v

# Run with coverage report
uv run --with pytest --with pytest-cov pytest tests/ --cov=app --cov-report=html
```

Tests include:

- **API Tests**: Endpoint validation, file upload handling
- **Model Tests**: Pydantic model validation
- **Parser Tests**: Header detection, data cleaning, normalization

---

## 🐳 Docker Workflow

For production or containerized environments:

| Action    | Command                                   |
| --------- | ----------------------------------------- |
| **Build** | `docker build -t programa .`              |
| **Run**   | `docker run -p 8000:8000 programa`        |
| **Test**  | `curl http://localhost:8000`              |
| **Clean** | `docker stop <id> && docker rmi programa` |
