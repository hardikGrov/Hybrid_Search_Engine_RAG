def test_project_scaffold_imports() -> None:
    import backend.app.main
    import hybrid_search.eval
    import hybrid_search.ingest
    import hybrid_search.index
    import hybrid_search.search

    assert backend.app.main.app.title == "Hybrid Search API"
