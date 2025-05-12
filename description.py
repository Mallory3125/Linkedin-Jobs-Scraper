import pandas as pd
import json

from bs4 import BeautifulSoup
from collections import defaultdict

import re
# extract sections from job description
def normalize_section_name(raw_header: str) -> str:
    # Normalize: lowercase + remove punctuation
    text = re.sub(r'[^\w\s]', '', raw_header.strip().lower())

    # Check Responsibilities
    if any(
        x in text for x in [
            "responsibilit",  # Catches "responsibilities", "responsibility"
            "what will you", 
            "in this role" 
        ]
    ):
        return "Responsibilities"

    # Check Requirements
    if any(
        x in text for x in [
            "requirement", 
            "qualificat",  # Catches "qualification", "qualifications", "qualification:"
            "what you need", 
            "skill",
            "minimum qualificat",
            "preferred qualificat",
            "experience",
            "certification"
        ]
    ):
        return "Requirements"

    # Other checks remain the same...
    if any(x in text for x in ["job description", "your role", "what you can expect", "what the role is", "overview"]):
        return "Job Description"
    if any(x in text for x in ["bonuses", "good to have"]):
        return "Preferred / Nice to Have"
    if any(x in text for x in ["about the job", "why join", "who are we","company"]):
        return "Company Info"

    return "Other"

def extract_sections_from_html(description_html: str):
    soup = BeautifulSoup(description_html, 'html.parser')
    sections = defaultdict(list)
    current_section = "Other"  # Default section
    original_section_name = ""

    def clean_and_get_text(tag):
        """ Clean the tag by removing non-relevant tags like span, comments, etc. """
        for unwanted_tag in tag.find_all(["span", "comment"]):  # Remove <span>, comments, etc.
            unwanted_tag.extract()
        return tag.get_text(strip=True)

    def process_tag(tag):
        nonlocal current_section,original_section_name
        # Check for header-like tags
        if tag.name in ["strong", "b", "h2", "h3", "h4"]:
            maybe_header = clean_and_get_text(tag)
            if maybe_header and (len(maybe_header)<60):  # Slightly looser check
                normalized = normalize_section_name(maybe_header)
                # print(f"Detected section header: {maybe_header} -> {normalized}")
                if normalized == "Other":
                    original_section_name = maybe_header
                current_section = normalized 

                return

        # Paragraph and span containers
        if tag.name in ["p", "div", "span"]:
            for child in tag.children:
                if isinstance(child, str):
                    text = child.strip()
                    if text:
                        if(current_section=="Other"):
                            text = f"{original_section_name}: {text}"
                        sections[current_section].append(text)

                else:
                    process_tag(child)

        # Handle list items inside <ul>
        elif tag.name == "ul":
            for li in tag.find_all("li"):
                li_text = clean_and_get_text(li)
                if li_text:
                    sections[current_section].append(li_text)

    for tag in soup.find_all(recursive=False):
        process_tag(tag)

    # Join consecutive text snippets in each section
    return {k: [line.strip() for line in v if line.strip()] for k, v in sections.items()}

input_file="job_data_0414.json"
output_file="job_data_0414_classify.json"

with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

descriptions = [
    job["Description"] 
    for job in data.values() 
    if "Description" in job and job["Description"]
]

all_results = []
for desc in descriptions:
    sections = extract_sections_from_html(desc)
    all_results.append(sections)

with open(output_file, "w", encoding='utf-8') as file:
    json.dump(all_results, file, indent=4, ensure_ascii=False)  # Fix here # Single structured file

