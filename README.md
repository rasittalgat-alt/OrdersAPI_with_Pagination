# Orders Management API

Orders Management API provides a FastAPI service for creating and listing orders with pagination and filtering.

## Tech Stack
- Python + FastAPI
- SQLite + SQLModel
- pytest + coverage

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the API
```bash
uvicorn app.main:app --reload
```

## Seed Sample Data
```bash
python -m app.seed
```

## Endpoints
### POST /orders
Create a new order.

**Body**
```json
{
  "customer_name": "Ada Lovelace",
  "amount": 125.50,
  "status": "paid"
}
```

**Validation**
- `customer_name` must not be empty
- `amount` must be greater than 0
- `status` must be `pending`, `paid`, `shipped`, or `cancelled`

### GET /orders
List orders with pagination and filtering.

**Query parameters**
- `page` (default 1, minimum 1)
- `limit` (default 10, range 1-100)
- `status` (pending | paid | shipped | cancelled)
- `min_amount`, `max_amount` (min <= max)
- `start_date`, `end_date` (ISO-8601 datetimes, start <= end)

**Response**
```json
{
  "items": [],
  "page": 1,
  "limit": 10,
  "total": 0,
  "pages": 0
}
```

**Examples**
```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_name": "Ada", "amount": 99.99, "status": "paid"}'

curl "http://localhost:8000/orders?page=1&limit=5&status=paid&min_amount=50"
```

## Tests
```bash
pytest
```

## Coverage
Run coverage locally and ensure at least 80%:
```bash
coverage run -m pytest
coverage report -m
```
