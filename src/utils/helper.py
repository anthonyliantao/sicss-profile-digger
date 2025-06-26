import re
import csv
from pathlib import Path
from urllib.parse import urlparse


def sanitize_filename(name: str) -> str:
    """return a save file name"""
    return re.sub(r"[^\w\-]+", "_", name).strip("_")


def ensure_dir(path: str | Path):
    """save set directory"""
    Path(path).mkdir(parents=True, exist_ok=True)


def write_text_data(data: list[dict], output_file: str | Path):
    """write text data, now only support csv"""
    ensure_dir(Path(output_file).parent)
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "bio", "photo_path", "role", "date", "location"])
        writer.writeheader()
        writer.writerows(data)
    print(f"[✅] CSV saved to {output_file}")


def extract_slug_from_url(url: str) -> str:
    """Extract unique slug used in naming files ..."""
    path = urlparse(url).path.strip("/")
    return path.replace("/", "_")
