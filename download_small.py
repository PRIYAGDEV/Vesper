"""Download Systran/faster-whisper-small with progress reporting into models/small."""

import os
from pathlib import Path
from huggingface_hub import hf_hub_download

os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

target_dir = Path("models") / "small"
target_dir.mkdir(parents=True, exist_ok=True)

files = ["config.json", "vocabulary.txt", "tokenizer.json", "model.bin"]
repo_id = "Systran/faster-whisper-small"

print(f"Downloading {repo_id} files into {target_dir.resolve()}...")

for f in files:
    out_file = target_dir / f
    if out_file.exists() and out_file.stat().st_size > 1000:
        if f == "model.bin" and out_file.stat().st_size > 400_000_000:
            print(f"File {f} already exists ({out_file.stat().st_size / 1_000_000:.1f} MB). Skipping.")
            continue
        elif f != "model.bin":
            print(f"File {f} already exists. Skipping.")
            continue

    print(f"Downloading {f}...")
    cached_path = hf_hub_download(repo_id=repo_id, filename=f, local_dir=str(target_dir))
    print(f"Downloaded {f} to {cached_path}")

print("\n[SUCCESS] 'small' model is completely downloaded and ready for use!")
