import numpy as np
import json
from transformers import pipeline
from collections import Counter
import os
import re
import spacy
from spacy.matcher import PhraseMatcher

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk.tokenize import word_tokenize
import gc

nlp = spacy.load("en_core_web_lg")
stop_words = set(stopwords.words('english'))
# token_skill_classifier = pipeline(model="jjzha/jobbert_skill_extraction", aggregation_strategy="first")
# token_knowledge_classifier = pipeline(model="jjzha/jobbert_knowledge_extraction", aggregation_strategy="first")


##NLP
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


## model

def ner(text):

    # Get skill predictions
    output_skills = token_skill_classifier(text)
    skill_words = [result["word"] for result in output_skills if "word" in result]

    # Get knowledge predictions
    output_knowledge = token_knowledge_classifier(text)
    knowledge_words = [result["word"] for result in output_knowledge if "word" in result]


    results  = list(set(skill_words + knowledge_words))
    return results


## rule-based
HARD_SKILL_LIST = [
    "Python", "R", "SQL", "VBA", "C++", "Java", "Tableau", "Power BI", "Excel",
    "TensorFlow", "PyTorch", "AWS", "Azure", "Docker", "Kubernetes",
    "Natural Language Processing", "Machine Learning", "Data Analysis", "Deep Learning"
]

# Build phrase matcher
phrase_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
patterns = [nlp.make_doc(skill) for skill in HARD_SKILL_LIST]
phrase_matcher.add("HARD_SKILL", patterns)

# Negation phrases
NEGATION_PATTERNS = [
    r'\bnot required\b',
    r'\bno experience\b',
    r'\bwithout knowledge\b',
    r'\bdo not need\b',
    r'\bnot necessary\b',
    r'\boptional\b',
    r'\bnice to have\b'
]

def contains_negation(sentence):
    sentence_lower = sentence.lower()
    return any(re.search(pattern, sentence_lower) for pattern in NEGATION_PATTERNS)

def extract_hard_skills(sentence):
    skills_found = set()
    doc = nlp(sentence)

    if contains_negation(sentence):
        return []  # Skip extraction in negated contexts

    matches = phrase_matcher(doc)
    for match_id, start, end in matches:
        skill = doc[start:end].text.strip()
        skills_found.add(skill)

    return list(skills_found)


def get_requirement(job_data):
    combined_lines = []
    for job in job_data:
        reqs = job.get("Requirements", [])
        prefs = job.get("Preferred / Nice to Have", [])
        combined_lines.extend(reqs)
        combined_lines.extend(prefs)
    return combined_lines    

def save_to_json(data, filename="sentences.json", length = 100):
    sentences = []
    cnt = 0
    for line in data:        
        sentences.append({
            "sentence": line,
            "hard_skill": [],
            "soft_skill": [],
            "qualification": []
        })
        cnt +=1
        if cnt > length:
            break

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(sentences, f, indent=2, ensure_ascii=False)

    print(f"Data has been saved to {filename}")
    return filename
  
def check_file_exist(filename):
    new_filename = ""
    if os.path.exists(filename):
        overwrite = input(f"The file {filename} already exists. Overwrite? (y/n): ")
        if overwrite.lower() != 'y':
            new_filename = input("Enter a new filename(with suffix): ")
    else:
        return filename
    return new_filename

def create_baseline_file(inpu_file,output_file,length=100):
    
    with open(inpu_file, "r", encoding="utf-8") as f:
        job_data = json.load(f)
    output_file = check_file_exist(output_file)
    sentences = get_requirement(job_data) 
    save_to_json(sentences,filename=output_file,length=length)   



if __name__ == '__main__':
    
    inpu_file="job_data_0414_classify.json"
    output_file="baseline_sentences.json"
    comparsion_file = "compare_rule_based.json"
    # create_baseline_file(inpu_file,output_file,length=100)
    # Force run garbage collector
    gc.collect()

    with open(output_file, "r", encoding="utf-8") as f:
        baseline_data = json.load(f)        
    print("baseline loaded")

    all_results = []

    for entry in baseline_data:
        sentence = entry["sentence"]
        ground_truth = entry["hard_skill"]
        # nlp_result = extract_skill_keywords(sentence)
        # model_result = ner(sentence )
        rule_result = extract_hard_skills(sentence)

        if(len(all_results)%10==0):
            print(len(all_results))

        all_results.append({
            "sentence": sentence,
            "ground_truth": ground_truth,
            "rule_result": rule_result
            # "nlp_result": nlp_result,
            # "model_result": model_result
        })

    with open(comparsion_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    del baseline_data, all_results
    gc.collect()
    print(f"Data has been saved to {comparsion_file}")    
            
