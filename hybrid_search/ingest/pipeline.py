import json
import argparse
from pathlib import Path
from datetime import datetime


# Argument Parser
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input directory")
    parser.add_argument("--out", required=True, help="Output JSONL file")
    return parser.parse_args()

# Load files from input directory
def load_files(input_dir: Path):
    files = list(input_dir.glob("**/*.txt")) + list(input_dir.glob("**/*.md"))
    return files

# Preprocess files (whitespace cleanup, truncation)
def clean_text(text: str) -> str:
    text = text.strip()
    text = " ".join(text.split())
    return text[:5000]  # safeguard for long docs

# Build record for each document
def build_record(file_path: Path, doc_id: int):
    text = file_path.read_text(encoding="utf-8", errors="ignore")

    return {
        "doc_id": f"doc_{doc_id}",
        "title": file_path.stem,
        "text": clean_text(text),
        "source": str(file_path),
        "created_at": datetime.utcnow().isoformat()
    }

# Write records to JSONL file
def write_jsonl(records, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")

# Main function to orchestrate the pipeline
def main():
    args = parse_args()

    input_dir = Path(args.input)
    output_path = Path(args.out)

    files = load_files(input_dir)

    records = []
    for i, file_path in enumerate(files):
        try:
            record = build_record(file_path, i)
            records.append(record)
        except Exception as e:
            print(f"Skipping {file_path}: {e}")

    write_jsonl(records, output_path)

    print(f"Ingested {len(records)} documents → {output_path}")


if __name__ == "__main__":
    main()