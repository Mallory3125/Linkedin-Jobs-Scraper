from playwright.sync_api import sync_playwright
import json
import os
from dotenv import load_dotenv
import pandas as pd
from urllib.parse import urlparse
import re
from datetime import datetime, timedelta
from collections import defaultdict

# Load environment variables
load_dotenv()
EMAIL = os.getenv("LINKEDIN_EMAIL")
PASSWORD = os.getenv("LINKEDIN_PASSWORD")

COOKIES_FILE = "cookies.json"

# Function to load cookies from file
def load_cookies(page):
    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "r") as f:
            cookies = json.load(f)
            page.context.add_cookies(cookies)
        print("✅ Cookies loaded successfully.")
    else:
        print("❌ Cookies file not found.")

# Function to save cookies to file
def save_cookies(context):
    cookies = context.cookies()
    with open(COOKIES_FILE, "w") as f:
        json.dump(cookies, f)
    print("✅ Cookies saved successfully.")

# Function to check login status
def login_check(page):
    return not page.is_visible("div.sign-in-modal")

# Function to click the pagination button and go to the next page
def go_to_next_page(page):
    next_button = page.query_selector("li.artdeco-pagination__indicator--number + li")
    if next_button and next_button.is_visible():
        next_button.click()
        page.wait_for_timeout(2000)  # Wait for the next page to load
        print("click!")
        return True
    return False


def get_exact_post_date(number, unit):
    today = datetime.today()

    if unit == "minute":
        delta = timedelta(minutes=number)
    elif unit == "hour":
        delta = timedelta(hours=number)
    elif unit == "day":
        delta = timedelta(days=number)
    elif unit == "week":
        delta = timedelta(weeks=number)
    elif unit == "month":
        delta = timedelta(days=30 * number)  # approximation
    elif unit == "year":
        delta = timedelta(days=365 * number)  # approximation
    else:
        delta = timedelta(0)

    post_date = today - delta
    return post_date.strftime('%Y-%m-%d')    

# Main function to login and scrape jobs
def login_and_scrape_with_descriptions(job_dict={},query="data analyst", location="Singapore", max_jobs=25):
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir="./profile",
            headless=True,
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            permissions=["geolocation"],
            timezone_id="Asia/Singapore",
            geolocation={"longitude": 103.8198, "latitude": 1.3521},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-dev-shm-usage",
                "--no-sandbox"
            ]
        )

        page = context.pages[0] if context.pages else context.new_page()
        load_cookies(page)

        search_url = f"https://www.linkedin.com/jobs/search/?keywords={query}&location={location}&f_E=1&sortBy=DD"
        print(f"🔍 Navigating to: {search_url}")
        page.goto(search_url, wait_until="networkidle")

        if not login_check(page):
            print("❌ Need login!")
            return None

        page.mouse.wheel(0, 1000)
        page.wait_for_selector('.job-card-container')

        job_count = 0
        results = []
        seen_job_ids = set()

        while job_count < max_jobs:
            job_cards = page.query_selector_all('.job-card-container')
            for i, card in enumerate(job_cards):
                if job_count >= max_jobs:
                    break
                try:
                    card.click()
                    page.wait_for_timeout(2000)

                    job_title_elem = page.query_selector("h1.t-24.t-bold")
                    job_title = job_title_elem.inner_text().strip() if job_title_elem else "N/A"

                    link_elem = page.query_selector("div.job-details-jobs-unified-top-card__job-title a")
                    raw_link = link_elem.get_attribute("href") if link_elem else None
                    clean_link = urlparse(raw_link).path if raw_link else "N/A"
                    job_id_match = re.search(r"/jobs/view/(\d+)", raw_link)
                    job_id = job_id_match.group(1) if job_id_match else clean_link  # fallback
                    # Skip if we've already seen this job in any previous run
                    if job_id in seen_job_ids:
                        print(f"⚠️ Already seen job, skipping: {job_title} (job_id: {job_id})")
                        continue

                    # Add to seen list for this run
                    seen_job_ids.add(job_id)



                    company_elem = page.query_selector(".job-details-jobs-unified-top-card__company-name")
                    company = company_elem.inner_text().strip() if company_elem else "N/A"

                    meta_elem = page.query_selector(".job-details-jobs-unified-top-card__tertiary-description-container")
                    meta_text = meta_elem.inner_text() if meta_elem else ""
                    date_match = re.search(r"(Reposted\s+)?(\d+)\s+(minute|hour|day|week|month|year)s?\s+ago", meta_text)
                    if date_match:
                        number = int(date_match.group(2))
                        unit = date_match.group(3)
                        exact_date = get_exact_post_date(number, unit)
                    else:
                        exact_date = "N/A"

                    # Extract raw applicants info like "55 applicants" or "Over 100 applicants"
                    applicants_match = re.search(r"(Over\s+)?\d+\s+applicants", meta_text)
                    applicants = applicants_match.group(0) if applicants_match else "N/A"

                    desc_elem = page.query_selector(".jobs-description-content__text--stretch")
                    description = desc_elem.inner_html().strip() if desc_elem else "No description found"

                    snapshot = {
                        "scraped_at": datetime.now().isoformat(),
                        "applicants": applicants
                    }
                    print(f"\n--- Job {job_count + 1} ---")
                    print("Title:", job_title)
                    if job_id in job_dict:
                        # Job seen before → add new snapshot
                        job_dict[job_id]["snapshots"].append(snapshot)
                    else:
                        job_dict[job_id] = {
                            "job_id": job_id,
                            "Title": job_title,
                            "Link": clean_link,
                            "Company": company,
                            "Post Date": exact_date,
                            "Description": description,
                            "snapshots": [snapshot]
                        }
                    job_count += 1

                except Exception as e:
                    print(f"⚠️ Error scraping job {job_count + 1}: {e}")

            if job_count < max_jobs and not go_to_next_page(page):
                print("⚠️ No more pages to scrape.")
                break

    return job_dict


def load_job_data(file_path):
    """Load job data from JSON file if it exists, otherwise return empty dict."""
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            print(f"Loaded jobs from previous run.")
            job_dict = json.load(f)
            seen_job_ids = set(job_dict.keys())
            return job_dict, seen_job_ids
    else:
        print("No previous data found.")        
    return {},set()

def save_job_data(file_path, job_dict):
    """Save job data to JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(job_dict, f, indent=4, ensure_ascii=False)
        print(f"Jobs saved to {file_path}")

if __name__ == '__main__':
    JSON_FILE = "job_data_dup.json"

    job_dict,seen_job_ids = load_job_data(JSON_FILE)
    login_and_scrape_with_descriptions(job_dict,query="data analyst", location="Singapore", max_jobs=5)
    save_job_data(JSON_FILE, job_dict)

