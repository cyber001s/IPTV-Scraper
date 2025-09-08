import os
import re
import sys
import datetime
import requests
from bs4 import BeautifulSoup
from art import text2art
from colorama import init
from termcolor import colored

init()

# Store scraped links by category
Scraped_Links = {}


def ensure_output_dir():
    if not os.path.exists("playlists"):
        os.makedirs("playlists")


def save_m3u(category, links, base_name="output"):
    """Save links into a category-specific m3u file"""
    if not links:
        print(colored(f"[!] No links found for {category}", "red"))
        return
    x = datetime.datetime.now()
    fname = f"playlists/{category}_{base_name}_{x.strftime('%d-%m-%y_%H-%M-%S')}.m3u"
    with open(fname, "w", encoding="utf-8") as f:
        for link in links:
            f.write(f"{link}\n")
    print(colored(f"[*] Saved {len(links)} links → {fname}", "green"))


def save_merged(base_name="output"):
    """Save all links into one merged m3u file"""
    all_links = []
    for cat_links in Scraped_Links.values():
        all_links.extend(cat_links)
    all_links = list(set(all_links))  # deduplicate

    if not all_links:
        print(colored("[!] No links collected in total", "red"))
        return
    x = datetime.datetime.now()
    fname = f"playlists/ALL_{base_name}_{x.strftime('%d-%m-%y_%H-%M-%S')}.m3u"
    with open(fname, "w", encoding="utf-8") as f:
        for link in all_links:
            f.write(f"{link}\n")
    print(colored(f"[*] Saved {len(all_links)} total links → {fname}", "cyan"))


def scrape_streamtest(channel, pages=1):
    """Scrape tested IPTV links from streamtest.in"""
    print(colored("[*] Scraping streamtest.in ...", "yellow"))
    Scraped_Links["Streamtest"] = []
    for page in range(1, pages + 1):
        url = f"https://streamtest.in/logs/page/{page}?filter={channel}&is_public=true"
        try:
            result = requests.get(url, timeout=15).text
            scraped_links = re.findall(r'http[s]?://\S+?\.m3u8', result)
            Scraped_Links["Streamtest"].extend(scraped_links)
            print(f"  Page {page}: {len(scraped_links)} links")
        except Exception as e:
            print(colored(f"  [Error page {page}] {e}", "red"))
    Scraped_Links["Streamtest"] = list(set(Scraped_Links["Streamtest"]))


def scrape_iptv_org(url, category, keyword=None):
    """Scrape links from iptv-org GitHub playlists"""
    print(colored(f"[*] Scraping iptv-org ({category}) ...", "yellow"))
    Scraped_Links[category] = []
    try:
        result = requests.get(url, timeout=15).text.splitlines()
        for line in result:
            if line.startswith("http"):
                if not keyword or keyword.lower() in line.lower():
                    Scraped_Links[category].append(line)
        Scraped_Links[category] = list(set(Scraped_Links[category]))
        print(f"  Found {len(Scraped_Links[category])} links in {category}")
    except Exception as e:
        print(colored(f"  [Error {category}] {e}", "red"))


def main():
    # 🎨 Fancy banner
    art = text2art("IPTV Scraper")
    print(colored(art, "cyan"))
    print(colored("Developed By Surya...!!!", "blue"))

    # If running in CI (GitHub Actions)
    if len(sys.argv) > 1 and sys.argv[1] == "--ci":
        channel_name = ""
        pages = 3
    else:
        channel_name = input("Channel keyword (leave empty for all): ").strip()
        try:
            pages = int(input("How many pages to scrape from streamtest.in? "))
        except:
            pages = 1

    ensure_output_dir()

    # Scrape sources
    scrape_streamtest(channel_name, pages)
    scrape_iptv_org("https://raw.githubusercontent.com/iptv-org/iptv/master/channels/in.m3u", "General", channel_name)
    scrape_iptv_org("https://raw.githubusercontent.com/iptv-org/iptv/master/channels/movies.m3u", "Movies", channel_name)
    scrape_iptv_org("https://raw.githubusercontent.com/iptv-org/iptv/master/channels/news.m3u", "News", channel_name)
    scrape_iptv_org("https://raw.githubusercontent.com/iptv-org/iptv/master/channels/entertainment.m3u", "Entertainment", channel_name)
    scrape_iptv_org("https://raw.githubusercontent.com/iptv-org/iptv/master/channels/sports.m3u", "Sports", channel_name)

    # Save results
    base = channel_name if channel_name else "INDIA"
    for category, links in Scraped_Links.items():
        save_m3u(category, links, base_name=base)
    save_merged(base_name=base)

    print(colored("✅ Scraping finished.", "green"))


if __name__ == "__main__":
    main()
