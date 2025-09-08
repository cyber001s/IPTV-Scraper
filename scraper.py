#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INDIA IPTV Scraper
==================
Scrapes IPTV links from multiple sources:
- streamtest.in logs
- iptv-org India master list
- iptv-org Movies / News / Entertainment / Sports categories
Outputs:
- Category-wise .m3u files
- One merged ALL.m3u
"""

import requests
from bs4 import BeautifulSoup
import datetime
import re
import os
from art import text2art
from colorama import init
from termcolor import colored

# Store links by category
Scraped_Links = {
    "Movies": set(),
    "News": set(),
    "Entertainment": set(),
    "Sports": set(),
    "General": set()
}

init(autoreset=True)


def ensure_output_dir():
    """Ensure output folder exists"""
    os.makedirs("playlists", exist_ok=True)


def save_m3u(category, links, base_name="INDIA"):
    """Save category-wise m3u file"""
    if not links:
        return
    filename = f"playlists/{base_name}-{category}.m3u"
    with open(filename, "w", encoding="utf-8") as f:
        for l in sorted(links):
            f.write(f"{l}\n")
    print(f"[✓] Saved {len(links)} links → {filename}")


def save_merged(base_name="INDIA"):
    """Save all collected links into one merged m3u"""
    merged = set()
    for cat_links in Scraped_Links.values():
        merged |= cat_links

    if not merged:
        return
    filename = f"playlists/{base_name}-ALL.m3u"
    with open(filename, "w", encoding="utf-8") as f:
        for l in sorted(merged):
            f.write(f"{l}\n")
    print(f"[✓] Saved merged playlist ({len(merged)} links) → {filename}")


def scrape_streamtest(channel, pages=5):
    """Scrape from streamtest.in"""
    for p in range(1, pages + 1):
        url = f"https://streamtest.in/logs/page/{p}?filter={channel}&is_public=true"
        try:
            r = requests.get(url, timeout=10).text
            soup = BeautifulSoup(r, "html.parser")
            links = soup.select("div.url.is-size-6")
            for link in links:
                Scraped_Links["General"].add(link.get_text(strip=True))
            print(f"[+] Streamtest Page {p}: {len(links)} links found")
        except Exception as e:
            print("[-] Streamtest error:", e)


def scrape_iptv_org(url, category, keyword=""):
    """Generic scraper for iptv-org lists"""
    try:
        r = requests.get(url, timeout=10).text
        matches = re.findall(r"http[^\s]+", r)
        for m in matches:
            if keyword.lower() in m.lower() or keyword == "":
                Scraped_Links[category].add(m)
        print(f"[+] {category}: {len(Scraped_Links[category])} links collected")
    except Exception as e:
        print(f"[-] {category} error:", e)


def main():
    # 🎨 Fancy banner
    art = text2art("IPTV Scraper")
    print(colored(art, "cyan"))
    print(colored("Developed By Henry Surya", "blue"))

    channel_name = input("Channel keyword (or leave empty for all India): ").strip()
    pages = int(input("How many pages to scrape from streamtest.in? "))

    ensure_output_dir()

    # Streamtest logs
    scrape_streamtest(channel_name, pages)

    # iptv-org India categories
    scrape_iptv_org("https://raw.githubusercontent.com/iptv-org/iptv/master/channels/in.m3u", "General", channel_name)
    scrape_iptv_org("https://raw.githubusercontent.com/iptv-org/iptv/master/channels/movies.m3u", "Movies", channel_name)
    scrape_iptv_org("https://raw.githubusercontent.com/iptv-org/iptv/master/channels/news.m3u", "News", channel_name)
    scrape_iptv_org("https://raw.githubusercontent.com/iptv-org/iptv/master/channels/entertainment.m3u", "Entertainment", channel_name)
    scrape_iptv_org("https://raw.githubusercontent.com/iptv-org/iptv/master/channels/sports.m3u", "Sports", channel_name)

    # Save category-wise files
    for category, links in Scraped_Links.items():
        save_m3u(category, links, base_name=channel_name if channel_name else "INDIA")

    # Save merged file
    save_merged(base_name=channel_name if channel_name else "INDIA")

    print(colored("✅ Scraping finished.", "green"))


if __name__ == "__main__":
    main()
