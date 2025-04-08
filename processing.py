import re
import spacy
import pandas as pd
from collections import defaultdict, Counter

nlp = spacy.load("en_core_web_sm")
df = pd.read_csv("jobs.csv")

# Define section headers you're looking for
SECTION_HEADERS = [
    "responsibilities", "requirements", "qualifications", "skills",
    "what you will do", "what we're looking for", "who you are"
]

# Normalize section headers
def normalize(text):
    return re.sub(r"[^a-zA-Z0-9 ]", "", text).lower().strip()

# Create regex pattern to split sections
section_pattern = re.compile(rf"(?i)\b({'|'.join(SECTION_HEADERS)})\b")

MAX_HEADER_LENGTH = 8  # Max number of words in a valid section header line

def split_into_sections(text):
    sections = defaultdict(str)
    current_section = "general"

    for line in text.splitlines():
        stripped_line = line.strip()
        normalized_line = normalize(stripped_line)
        word_count = len(stripped_line.split())

        # Check if it's a real section header: short and matches known headers
        if any(normalized_line.startswith(normalize(header)) for header in SECTION_HEADERS) and word_count <= MAX_HEADER_LENGTH:
            current_section = normalized_line
        else:
            sections[current_section] += " " + normalized_line

    return sections


def clean_noun_chunk(text):
    words = text.lower().strip().split()
    # Remove determiners at the start
    stop_starts = {"this", "that", "your", "our", "a", "an", "the"}
    if words and words[0] in stop_starts:
        words = words[1:]
    # Rejoin, remove if now too short
    cleaned = " ".join(words)
    if len(cleaned.split()) < 2 or cleaned in {"role", "plus", "journey"}:
        return None
    return cleaned


# Frequency counters
word_counter = Counter()
phrase_counter = Counter()
entity_counter = Counter()
custom_skill_counter = Counter()

# Section selection
TARGET_SECTIONS = {"requirements", "qualifications", "skills"}
TECH_KEYWORDS = {
    "python", "java", "c++", "c#", "sql", "mysql", "postgresql", "mongodb",
    "pandas", "numpy", "tensorflow", "pytorch", "aws", "azure", "gcp",
    "docker", "kubernetes", "git", "linux", "react", "node.js", "spark"
}

for desc in df['Description'].dropna():
    sections = split_into_sections(desc)
    for section_name, content in sections.items():
        if any(key in section_name for key in TARGET_SECTIONS):
            doc = nlp(content.lower())


            # ✅ NEW: Noun chunks (phrases)
            noun_chunks = [
                cleaned for chunk in doc.noun_chunks
                if (cleaned := clean_noun_chunk(chunk.text))
            ]
            phrase_counter.update(noun_chunks)

            # ✅ NEW: Named entities (NER)
            named_ents = [
                ent.text.lower().strip()
                for ent in doc.ents
                if len(ent.text.split()) > 1 and ent.label_ in {"ORG", "PRODUCT", "SKILL", "WORK_OF_ART", "TECHNOLOGY", "LANGUAGE"}
            ]
            entity_counter.update(named_ents)

            for token in doc:
                if token.text.lower() in TECH_KEYWORDS:
                    custom_skill_counter[token.text.lower()] += 1    


print("\n🧩 Top noun phrase keywords:")
for phrase, count in phrase_counter.most_common(30):
    print(f"{phrase}: {count}")

print("\n🧠 Top named entities (multi-word):")
for entity, count in entity_counter.most_common(30):
    print(f"{entity}: {count}")


print("\n🧠 Custom detected tech keywords:")
for kw, count in custom_skill_counter.most_common(30):
    print(f"{kw}: {count}")
