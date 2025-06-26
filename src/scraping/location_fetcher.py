import re
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright


def fetch_html(url: str, headless: bool) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")
        html = page.content()
        browser.close()
    return html


def get_all_location_urls(home_url: str, headless: bool = True) -> list[str]:
    html = fetch_html(home_url, headless=headless)
    soup = BeautifulSoup(html, "html.parser")
    people_urls = set()

    # Match patterns like '/2025/shanghai/', but excludes subpaths like '/apply'
    pattern = re.compile(r"^/20\d{2}/[a-z0-9\-_]+/?$")

    for a in soup.find_all("a", href=True):
        if not isinstance(a, Tag):
            continue  # skip non-html element
        
        href = str(a["href"])
        if pattern.match(href):
            full_url = urljoin("https://sicss.io", href.rstrip("/") + "/people")
            people_urls.add(full_url)

    return sorted(people_urls)