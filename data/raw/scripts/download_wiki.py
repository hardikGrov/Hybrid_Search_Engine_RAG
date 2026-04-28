from datasets import load_dataset
import os

OUTPUT_DIR = "data/raw"
MAX_DOCS = 500

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("Downloading WikiText dataset...")

ds = load_dataset("wikitext", "wikitext-2-raw-v1", split="train")

count = 0
skipped = 0

for i, item in enumerate(ds):
    if count >= MAX_DOCS:
        break

    text = item["text"].strip()

    # Skip empty / very small text chunks
    if not text or len(text) < 50:
        skipped += 1
        continue

    file_path = os.path.join(OUTPUT_DIR, f"doc_{count}.txt")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)

    count += 1

print("======================================")
print(f"✅ Saved documents: {count}")
print(f"⚠️ Skipped documents: {skipped}")
print(f"📁 Output directory: {OUTPUT_DIR}")
print("======================================")