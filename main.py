from playwright.sync_api import sync_playwright
import json
import os
from dotenv import load_dotenv
import pandas as pd
from urllib.parse import urlparse

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
        return True
    return False

# Main function to login and scrape jobs
def login_and_scrape_with_descriptions(query="data analyst", location="Singapore", max_jobs=25):
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

        search_url = f"https://www.linkedin.com/jobs/search/?keywords={query}&location={location}&f_E=1"
        print(f"🔍 Navigating to: {search_url}")
        page.goto(search_url, wait_until="networkidle")

        # Check login status
        if not login_check(page):
            print("❌ Need login!")
            return None

        page.mouse.wheel(0, 1000)  # Scroll to load jobs
        page.wait_for_selector('.job-card-container')

        job_count = 0
        results = []

        while job_count < max_jobs:
            job_cards = page.query_selector_all('.job-card-container')
            for i, card in enumerate(job_cards):
                if job_count >= max_jobs:
                    break
                try:
                    card.click()
                    page.wait_for_timeout(2000)

                    # Get job details
                    job_title_elem = page.query_selector("h1.t-24.t-bold")
                    job_title = job_title_elem.inner_text().strip() if job_title_elem else "N/A"

                    link_elem = page.query_selector("div.job-details-jobs-unified-top-card__job-title a")
                    raw_link = link_elem.get_attribute("href") if link_elem else None
                    clean_link = urlparse(raw_link).path if raw_link else "N/A"

                    company_elem = page.query_selector(".job-details-jobs-unified-top-card__company-name")
                    company = company_elem.inner_text().strip() if company_elem else "N/A"

                    posted_elem = page.query_selector(".jobs-unified-top-card__posted-date")
                    posted_time = posted_elem.inner_text().strip() if posted_elem else "N/A"

                    applicants_elem = page.query_selector(".jobs-unified-top-card__applicant-count")
                    applicants = applicants_elem.inner_text().strip() if applicants_elem else "N/A"

                    desc_elem = page.query_selector(".jobs-description-content__text--stretch")
                    description = desc_elem.inner_text().strip() if desc_elem else "No description found"

                    print(f"\n--- Job {job_count + 1} ---")
                    print("Title:", job_title)

                    results.append({
                        "Title": job_title,
                        "Company": company,
                        "Job Link": clean_link,
                        "Description": description
                    })

                    job_count += 1

                except Exception as e:
                    print(f"⚠️ Error scraping job {job_count + 1}: {e}")

            # Check if we should continue to the next page
            if job_count < max_jobs and not go_to_next_page(page):
                print("⚠️ No more pages to scrape.")
                break

        # Convert results to DataFrame and return
        df = pd.DataFrame(results)
        return df


if __name__ == '__main__':
    df = login_and_scrape_with_descriptions(query="data analyst", location="Singapore", max_jobs=35)
    if df is not None:
        df.to_csv("jobs.csv", index=False)
        print("✅ Jobs saved to jobs.csv")

