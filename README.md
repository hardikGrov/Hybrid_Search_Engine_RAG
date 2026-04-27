# Hybrid Search Engine RAG

Python project scaffold for a hybrid search system with:

- FastAPI backend
- Streamlit frontend
- Separate packages for ingest, index, search, and eval workflows

This repository currently contains structure only. Business logic should be added inside the relevant package modules as the system is implemented.

## Layout

```text
.
├── backend/
│   └── app/
│       └── main.py
├── frontend/
│   └── app.py
├── hybrid_search/
│   ├── eval/
│   ├── ingest/
│   ├── index/
│   └── search/
└── tests/
```

## Run

```bash
uvicorn backend.app.main:app --reload
```

```bash
streamlit run frontend/app.py
```
