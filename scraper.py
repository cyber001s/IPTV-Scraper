import os
import re
import sys
import datetime
import requests
from art import text2art
from colorama import init
from termcolor import colored

init()

# Global dictionary for all categories
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


def scrape_iptv_org_categorized(url):
    """Scrape iptv-org streams and auto-categorize by group-title"""
    print(colored(f"[*] Scraping iptv-org (auto-categorized) ...", "yellow"))
    try:
        result = requests.get(url, timeout=15).text.splitlines()
        category_links = {}
        current_group = "Unknown"

        for line in result:
            line = line.strip()
            if line.startswith("#EXTINF"):
                match = re.search(r'group-title="([^"]+)"', line)
                if match:
                    current_group = match.group(1)
            elif line.startswith("http"):
                if current_group not in category_links:
                    category_links[current_group] = []
                category_links[current_group].append(line)

        # Merge into global dictionary
        for cat, links in category_links.items():
            if cat not in Scraped_Links:
                Scraped_Links[cat] = []
            Scraped_Links[cat].extend(links)

        # Deduplicate per category
        for cat in Scraped_Links:
            Scraped_Links[cat] = list(set(Scraped_Links[cat]))

        for cat in category_links:
            print(f"  Found {len(category_links[cat])} links in {cat}")

    except Exception as e:
        print(colored(f"  [Error] {e}", "red"))


def main():
    # Banner
    art = text2art("IPTV Scraper")
    print(colored(art, "cyan"))
    print(colored("Developed By Surya...!!!", "blue"))

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

    iptv_urls = [
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/in.m3u",
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/movies.m3u",
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/news.m3u",
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/entertainment.m3u",
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/sports.m3u",
    ]
    for url in iptv_urls:
        scrape_iptv_org_categorized(url)

    base = channel_name if channel_name else "INDIA"
    for category, links in Scraped_Links.items():
        save_m3u(category, links, base_name=base)
    save_merged(base_name=base)

    print(colored("✅ Scraping finished.", "green"))


if __name__ == "__main__":
    main()
