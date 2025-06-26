from src.scraping.profile_scraper import scrape_profiles
from src.scraping.location_fetcher import get_all_location_urls
from src.utils.helper import extract_slug_from_url
from pathlib import Path


home_url = 'https://sicss.io/locations'


location_urls = get_all_location_urls(home_url=home_url, headless=False)
for url in location_urls:
    try:
        slug = extract_slug_from_url(url)
        output_file = Path(f"data/raw/profiles_{slug}.csv")
        img_dir = Path(f"data/raw/images/{slug}")
        result = scrape_profiles(
            url,
            image_dir=img_dir,
            output_file=output_file,
            headless=False,
            save_photo=False
        )
    except Exception as e:
        print(f"❌ Skipping {url} after 3 failed attempts.")