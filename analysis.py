import json
from collections import Counter
import re
import spacy
from spacy.matcher import PhraseMatcher

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk.tokenize import word_tokenize


import matplotlib.pyplot as plt

def plot_skill_distribution(counter, filename='skill_distribution.png'):
    values = sorted(counter.values(), reverse=True)
    plt.figure(figsize=(10,5))
    plt.plot(values)
    plt.yscale('log')
    plt.xlabel("Rank")
    plt.ylabel("Frequency (log scale)")
    plt.title("Skill Phrase Frequency Distribution")
    plt.grid(True)
    plt.tight_layout()  # Ensures labels don't get cut off
    plt.savefig(filename, dpi=300)  # Save to file with high resolution
    plt.close() 


def clean_sentence(sentence):
    sentence = sentence.lower()
    sentence = re.sub(r'[\/&\-]', ' ', sentence) #remian "+" for C++
    sentence = re.sub(r'[()\[\]{}]', '', sentence)
    sentence = re.sub(r'\s+', ' ', sentence).strip()
    return sentence


def extract_skill_keywords(sentence, min_words=1, max_words=4):
    sentence = clean_sentence(sentence)
    doc = nlp(sentence)
    skills = []

    for chunk in doc.noun_chunks:
        tokens = [token for token in chunk if token.text.lower() not in stop_words]

        if not tokens or len(tokens) < min_words:
            continue

        if tokens[0].pos_ == "ADJ":
            tokens = tokens[1:]

        if not (min_words <= len(tokens) <= max_words):
            continue
        if not any(t.pos_ in {"NOUN", "PROPN"} for t in tokens):
            continue

        phrase = " ".join(token.lemma_.lower() for token in tokens)
        skills.append(phrase)

    return list(set(skills))



def simple_extraction(combined_lines):
    all_phrases = []
    for line in combined_lines:
        all_phrases.extend(extract_skill_keywords(line))

    phrase_counts = Counter(all_phrases)

    # Filter out noise (optional stop phrases or manual cleanup)
    stop_phrases = {"experience", "skills", "knowledge", "understanding", "ability"}
    filtered_counts = {
        phrase: count
        for phrase, count in phrase_counts.items()
        if phrase not in stop_phrases and len(phrase) > 2 and count>=2
    }

    return filtered_counts



if __name__ == '__main__':
    
    inpu_file="job_data_0414_classify.json"

    with open(inpu_file, "r", encoding="utf-8") as f:
        job_data = json.load(f)
    nlp = spacy.load("en_core_web_lg")
    stop_words = set(stopwords.words('english'))

    # Combine "Requirements" and "Preferred / Nice to Have" from all jobs
    combined_lines = []
    for job in job_data:
        reqs = job.get("Requirements", [])
        prefs = job.get("Preferred / Nice to Have", [])
        combined_lines.extend(reqs)
        combined_lines.extend(prefs)
    # extracted too many "R", so just ignore it 
    # print(len(combined_lines))
    counts = simple_extraction(combined_lines)
    plot_skill_distribution(counts,filename="skill_distribution.png")    
    # # Display top candidate skills
    # print("Top Extracted Skills / Tools / Soft Skills:")
    # with open("test2.txt","w") as file:
    #     for phrase, count in Counter(counts).most_common():
    #         file.write(f"{phrase}: {count}\n")

    # print(extract_skill_keywords("Proficient coding skills and strong algorithm & data structure using C++/Python/Java"))
