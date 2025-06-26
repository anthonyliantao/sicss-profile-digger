from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin
import requests
import re
import os
import csv
from pathlib import Path

from src.utils.helper import ensure_dir, sanitize_filename, write_text_data


def fetch_html(url: str, headless: bool = True) -> str:
    """scarpe html content from a url"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")
        html = page.content()
        browser.close()
    return html


def parse_profile_block(block, base_url: str, save_photo: bool, image_dir: str | Path) -> dict[str, str | None]:
    """parse person data from profile block in the html content"""
    # name
    name_tag = block.select_one("h5.font-weight-bold")
    name = name_tag.get_text(strip=True) if name_tag else None

    # bio
    body_div = block.select_one("div.media-body")
    for h5 in body_div.select("h5"):
        h5.decompose()
    bio = body_div.get_text(separator=" ", strip=True)

    # photo path
    img_tag = block.select_one("img")
    photo_url = urljoin(base_url, img_tag["src"]) if img_tag else None
    photo_path = None
    
    # download photo from photo path
    if photo_url and save_photo and name:
        safe_name = sanitize_filename(name)
        photo_path = os.path.join(image_dir, f"{safe_name}.jpg")
        try:
            r = requests.get(photo_url, timeout=10)
            r.raise_for_status()
            with open(photo_path, "wb") as f:
                f.write(r.content)
        except Exception as e:
            print(f"⚠️ Failed to download image: {photo_url} → {e}")
            photo_path = None

    return {
        "name": name,
        "bio": bio,
        "photo_path": photo_path
    }


def parse_profiles(html: str, base_url: str, save_photo: bool, image_dir: str | Path) -> list[dict]:
    """Extract information from the html content"""
    
    soup = BeautifulSoup(html, "html.parser")
    all_profiles = []
    
    # date and location
    info_tag = soup.select_one("p.h4.text-light")
    date, location = None, None
    if info_tag:
        text = info_tag.get_text(strip=True)
        if "|" in text:
            date, location = map(str.strip, text.split("|", maxsplit=1))
        else:
            date = text  # fallback situation 

    # Find role blocks and profile blocks between them
    for h3 in soup.select("h3.h3.mb-4"):
        role = h3.get_text(strip=True)

        profile_blocks = []
        for sibling in h3.find_next_siblings():
            if not isinstance(sibling, Tag):
                continue # skip non-html tag, e.g.: NavigableString
            
            classes = sibling.get("class")
            
            if sibling.name == "h3" and classes and "mb-4" in classes:
                break  # stop collecting if run into the next h3
            
            if sibling.name == "div" and classes and "media" in classes and "mb-5" in classes:
                profile_blocks.append(sibling)

        # Parse each profile blocks
        for block in profile_blocks:
            profile = parse_profile_block(block, base_url, save_photo, image_dir)
            profile["role"] = role
            profile["date"] = date
            profile["location"] = location
            all_profiles.append(profile)

    return all_profiles

    
# 主调度函数
def scrape_profiles(
    url: str,
    image_dir: str | Path = "data/raw/images",
    output_file: str | Path = "data/raw/profiles.csv",
    headless: bool = True,
    save_photo: bool = True
) -> list[dict]:
    if save_photo:
        ensure_dir(image_dir)

    html = fetch_html(url, headless=headless)
    profiles = parse_profiles(html, url, save_photo, image_dir)

    if output_file:
        write_text_data(profiles, output_file)

    return profiles