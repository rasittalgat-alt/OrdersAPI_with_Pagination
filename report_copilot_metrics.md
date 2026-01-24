# Copilot Metrics Report — Orders API with Pagination

**Project:** Orders Management API (FastAPI + SQLite + SQLModel)  
**Date:** 2026-01-24  
**AI tools used:** ChatGPT Codex (initial repo scaffolding) + GitHub Copilot (VS Code inline completions)

## Copilot contribution (estimate)
- Overall AI-generated code (Codex + Copilot): ~75–85%
- Manual coding, review, and fixes: ~15–25%

## Copilot usage metrics (self-tracked)
- Suggestions shown: 12
- Suggestions accepted: 8
- Acceptance rate: 67%
- Estimated time saved: ~1–2 hours

## What Copilot generated
- README improvements: added filtering examples with ready-to-run curl commands
- Testing improvement: generated an edge-case test for pagination behavior (out-of-range page)
- Small refinements during editing (syntax, assertions)

## Manual fixes and verification
- Fixed test discovery by adding `pytest.ini` (pythonpath)
- Verified API behavior using Swagger UI (POST /orders, GET /orders with pagination)
- Seeded 50 orders and confirmed `/orders` returns `total=50` and `pages=5`
- Ran pytest and ensured 80%+ coverage (achieved 97%)

## 3 key learnings
1. Copilot is excellent for boilerplate (docs/examples/tests) when prompts are specific and constrained.
2. You must still validate outputs by running tests and checking runtime behavior (Swagger + seeded DB).
3. Best workflow: generate → run tests/coverage → adjust manually → commit small increments.
