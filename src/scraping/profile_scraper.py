from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
import re
import os
import csv
from pathlib import Path

def sanitize_filename(name: str) -> str:
    # 替换非字母数字为下划线
    return re.sub(r"[^\w\-]+", "_", name).strip("_")

# 创建目录
def ensure_dir(path: str | Path):
    Path(path).mkdir(parents=True, exist_ok=True)

# 获取网页 HTML 内容
def fetch_html(url: str, headless: bool = True) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")
        html = page.content()
        browser.close()
    return html

# 解析单个人员区块
def parse_profile_block(block, base_url: str, save_photo: bool, image_dir: str | Path):
    # 姓名
    name_tag = block.select_one("h5.font-weight-bold")
    name = name_tag.get_text(strip=True) if name_tag else None

    # 简介
    body_div = block.select_one("div.media-body")
    for h5 in body_div.select("h5"):
        h5.decompose()
    bio = body_div.get_text(separator=" ", strip=True)

    # 图片
    img_tag = block.select_one("img")
    photo_url = urljoin(base_url, img_tag["src"]) if img_tag else None
    photo_path = None

    if photo_url and save_photo:
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

# 解析整个页面中的 profile 块
def parse_profiles(html: str, base_url: str, save_photo: bool, image_dir: str | Path) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    all_profiles = []
    
    # 🔍 提取日期与地点（只提取第一个匹配）
    info_tag = soup.select_one("p.h4.text-light")
    date, location = None, None
    if info_tag:
        text = info_tag.get_text(strip=True)
        if "|" in text:
            date, location = map(str.strip, text.split("|", maxsplit=1))
        else:
            date = text  # fallback 情况    

    # 遍历每个 role 块
    for h3 in soup.select("h3.h3.mb-4"):
        role = h3.get_text(strip=True)

        # 收集该 h3 到下一个 h3 之间的所有 profile 块
        profile_blocks = []
        for sibling in h3.find_next_siblings():
            if sibling.name == "h3" and "mb-4" in sibling.get("class", []):
                break  # 遇到下一个 role 区块，结束当前收集
            if sibling.name == "div" and "media" in sibling.get("class", []) and "mb-5" in sibling.get("class", []):
                profile_blocks.append(sibling)

        # 解析每一个块并加入 role 字段
        for block in profile_blocks:
            profile = parse_profile_block(block, base_url, save_photo, image_dir)
            profile["role"] = role
            profile["date"] = date
            profile["location"] = location
            all_profiles.append(profile)

    return all_profiles

# 保存为 CSV
def save_to_csv(data: list[dict], output_file: str | Path):
    ensure_dir(Path(output_file).parent)
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "bio", "photo_path", "role", "date", "location"])
        writer.writeheader()
        writer.writerows(data)
    print(f"[✅] CSV saved to {output_file}")
    
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
        save_to_csv(profiles, output_file)

    return profiles