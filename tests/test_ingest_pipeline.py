import json
from datetime import datetime

import pytest

from hybrid_search.ingest import pipeline


def test_load_files_finds_text_and_markdown_recursively(tmp_path):
    (tmp_path / "root.txt").write_text("root", encoding="utf-8")
    (tmp_path / "notes.md").write_text("notes", encoding="utf-8")
    (tmp_path / "ignored.json").write_text("{}", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "child.txt").write_text("child", encoding="utf-8")

    files = {path.relative_to(tmp_path) for path in pipeline.load_files(tmp_path)}

    assert files == {
        tmp_path.joinpath("root.txt").relative_to(tmp_path),
        tmp_path.joinpath("notes.md").relative_to(tmp_path),
        tmp_path.joinpath("nested", "child.txt").relative_to(tmp_path),
    }


def test_clean_text_normalizes_whitespace_and_truncates_long_text():
    raw_text = "  hello\n\n\tworld   " + ("x" * 6000)

    cleaned = pipeline.clean_text(raw_text)

    assert cleaned.startswith("hello world")
    assert "\n" not in cleaned
    assert "\t" not in cleaned
    assert len(cleaned) == 5000


def test_build_record_reads_file_and_adds_metadata(tmp_path):
    source_file = tmp_path / "example_doc.txt"
    source_file.write_text("  Example\ntext  ", encoding="utf-8")

    record = pipeline.build_record(source_file, doc_id=7)

    assert record is not None
    assert record["doc_id"] == "doc_7"
    assert record["title"] == "example_doc"
    assert record["text"] == "Example text"
    assert record["source"] == str(source_file)
    datetime.fromisoformat(record["created_at"])


def test_build_record_returns_none_for_empty_file(tmp_path):
    source_file = tmp_path / "empty.txt"
    source_file.write_text("", encoding="utf-8")

    assert pipeline.build_record(source_file, doc_id=1) is None


def test_build_record_rejects_missing_path(tmp_path):
    with pytest.raises(FileNotFoundError):
        pipeline.build_record(tmp_path / "missing.txt", doc_id=1)


def test_build_record_rejects_directory(tmp_path):
    with pytest.raises(ValueError):
        pipeline.build_record(tmp_path, doc_id=1)


def test_write_jsonl_creates_parent_directory_and_writes_records(tmp_path):
    output_path = tmp_path / "processed" / "docs.jsonl"
    records = [
        {"doc_id": "doc_0", "text": "first"},
        {"doc_id": "doc_1", "text": "second"},
    ]

    pipeline.write_jsonl(records, output_path)

    lines = output_path.read_text(encoding="utf-8").splitlines()
    assert [json.loads(line) for line in lines] == records


def test_main_ingests_files_to_jsonl(tmp_path, monkeypatch, capsys):
    input_dir = tmp_path / "raw"
    input_dir.mkdir()
    (input_dir / "first.txt").write_text("First   document", encoding="utf-8")
    (input_dir / "second.md").write_text("Second\n document", encoding="utf-8")
    output_path = tmp_path / "processed" / "docs.jsonl"
    monkeypatch.setattr(
        "sys.argv",
        ["pipeline", "--input", str(input_dir), "--out", str(output_path)],
    )

    pipeline.main()

    records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert [record["doc_id"] for record in records] == ["doc_0", "doc_1"]
    assert {record["text"] for record in records} == {"First document", "Second document"}
    assert f"Ingested 2 documents" in capsys.readouterr().out


def test_main_raises_when_input_directory_does_not_exist(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["pipeline", "--input", str(tmp_path / "missing"), "--out", str(tmp_path / "docs.jsonl")],
    )

    with pytest.raises(ValueError, match="Input directory"):
        pipeline.main()


def test_main_raises_when_no_supported_files_found(tmp_path, monkeypatch):
    input_dir = tmp_path / "raw"
    input_dir.mkdir()
    (input_dir / "ignored.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        ["pipeline", "--input", str(input_dir), "--out", str(tmp_path / "docs.jsonl")],
    )

    with pytest.raises(ValueError, match="No .txt or .md files"):
        pipeline.main()
