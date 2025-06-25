from src.scraping.profile_scraper import scrape_profiles
from src.scraping.location_fetcher import get_all_location_urls
from pathlib import Path
from urllib.parse import urlparse

def extract_slug_from_url(url: str) -> str:
    # 从 URL 中提取 2025/bogota → 2025_bogota
    path = urlparse(url).path.strip("/")
    return path.replace("/", "_")

home_url = 'https://sicss.io/locations'

location_urls = get_all_location_urls(home_url=home_url, headless=False)
for url in location_urls:
    slug = extract_slug_from_url(url)  # eg: "2025_bogota"
    output_file = Path(f"data/raw/profiles_{slug}.csv")
    img_dir = Path(f"data/raw/images/{slug}")
    result = scrape_profiles(
        url,
        image_dir=img_dir,
        output_file=output_file,
        headless=False,
        save_photo=False
    )