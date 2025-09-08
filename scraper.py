import os
import re
import sys
import datetime
import requests
from art import text2art
from colorama import init
from termcolor import colored

init()

Scraped_Links = {}

# -----------------------------
# Folder management
# -----------------------------
def clear_playlists_dir():
    """Clear only files inside playlists folder, keep folder itself"""
    if not os.path.exists("playlists"):
        os.makedirs("playlists")
    else:
        # Remove all files inside
        for filename in os.listdir("playlists"):
            file_path = os.path.join("playlists", filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
    print(colored("[*] playlists/ directory cleaned.", "yellow"))

# -----------------------------
# Save functions
# -----------------------------
def save_m3u(category, links, base_name="output"):
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
    all_links = []
    for cat_links in Scraped_Links.values():
        all_links.extend(cat_links)
    all_links = list(set(all_links))
    if not all_links:
        print(colored("[!] No links collected in total", "red"))
        return
    x = datetime.datetime.now()
    fname = f"playlists/ALL_{base_name}_{x.strftime('%d-%m-%y_%H-%M-%S')}.m3u"
    with open(fname, "w", encoding="utf-8") as f:
        for link in all_links:
            f.write(f"{link}\n")
    print(colored(f"[*] Saved {len(all_links)} total links → {fname}", "cyan"))

# -----------------------------
# Scrapers
# -----------------------------
def scrape_streamtest(channel, pages=1):
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
    print(colored(f"[*] Scraping iptv-org (auto-categorized) ...", "yellow"))
    try:
        result = requests.get(url, timeout=15).text.splitlines()
        category_links = {}
        current_group = "Unknown"

        for line in result:
            line = line.strip()
            if line.startswith("#EXTINF"):
                match = re.search(r'group-title="([^"]+)"', line)
                current_group = match.group(1) if match else "Unknown"
            elif line.startswith("http"):
                if current_group not in category_links:
                    category_links[current_group] = []
                category_links[current_group].append(line)

        for cat, links in category_links.items():
            if cat not in Scraped_Links:
                Scraped_Links[cat] = []
            Scraped_Links[cat].extend(links)

        for cat in Scraped_Links:
            Scraped_Links[cat] = list(set(Scraped_Links[cat]))

        for cat in category_links:
            print(f"  Found {len(category_links[cat])} links in {cat}")

    except Exception as e:
        print(colored(f"  [Error] {e}", "red"))

# -----------------------------
# Main
# -----------------------------
def main():
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

    # Clear old playlist files but keep directory
    clear_playlists_dir()

    # Scrape sources
    try:
        scrape_streamtest(channel_name, pages)
    except Exception as e:
        print(colored(f"[!] Streamtest scrape failed: {e}", "red"))

    try:
        scrape_iptv_org_categorized(
            "https://raw.githubusercontent.com/iptv-org/iptv/master/channels/in.m3u"
        )
    except Exception as e:
        print(colored(f"[!] IPTV-org scrape failed: {e}", "red"))

    base = channel_name if channel_name else "INDIA"
    for category, links in Scraped_Links.items():
        save_m3u(category, links, base_name=base)
    save_merged(base_name=base)

    print(colored("✅ Scraping finished.", "green"))

if __name__ == "__main__":
    main()
