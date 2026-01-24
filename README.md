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
<!-- Copilot: add a "Filtering examples" section with 4-5 concise GET examples for status, amount range, date range, and combined with pagination. Use markdown code formatting. -->

## Filtering examples
<!-- Copilot: add 4 concise curl examples for filtering by status, amount range, date range, and combined with pagination -->
- Status:

```bash
curl "http://localhost:8000/orders?status=shipped"
```

- Amount Range:
```bash
curl "http://localhost:8000/orders?min_amount=100&max_amount=500"
```
- Date Range:
```bash
curl "http://localhost:8000/orders?start_date=2024-01-01T00:00:00&end_date=2024-01-31T23:59:59"

- Combined with Pagination:
```bash

curl "http://localhost:8000/orders?page=2&limit=10&status=paid&min_amount=50&max_amount=300&start_date=2024-01-01T00:00:00&end_date=2024-01-31T23:59:59"


---

## Шаг 3 — Copilot-правка №2: добавим 1 edge-case test (без изменения API)
В `tests/test_orders.py` в самый конец добавь комментарий:

```python
# Copilot: add an edge-case test that requesting a very large page returns 200 and empty items

def test_list_orders_page_out_of_range_returns_empty(test_app):


    client = test_app
    response = client.get("/orders", params={"page": 1000, "limit": 10})
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["page"] == 1000
    assert data["limit"] == 10
    
```


