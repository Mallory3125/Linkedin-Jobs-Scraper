import numpy as np
import json
from transformers import pipeline
from collections import Counter

# Load models for skill and knowledge extraction
token_skill_classifier = pipeline(model="jjzha/jobbert_skill_extraction", aggregation_strategy="first")
token_knowledge_classifier = pipeline(model="jjzha/jobbert_knowledge_extraction", aggregation_strategy="first")

# Example sentences
examples = [
    "Knowing Python is a plus",
    "Recommend changes, develop and implement processes to ensure compliance with IFRS standards"
]

# Function to aggregate consecutive spans (skills/knowledge)
def aggregate_span(results):
    new_results = []
    current_result = results[0]

    for result in results[1:]:
        if result["start"] == current_result["end"] + 1:
            current_result["word"] += " " + result["word"]
            current_result["end"] = result["end"]
        else:
            new_results.append(current_result)
            current_result = result

    new_results.append(current_result)
    return new_results

# Function to process text and extract skills and knowledge
def ner(text, skill_counter, knowledge_counter):
    # Get skill predictions
    output_skills = token_skill_classifier(text)
    for result in output_skills:
        if result.get("entity_group"):
            result["entity"] = "Skill"
            del result["entity_group"]
            skill_counter[result["word"]] += 1  # Count frequency of skills

    # Get knowledge predictions
    output_knowledge = token_knowledge_classifier(text)
    for result in output_knowledge:
        if result.get("entity_group"):
            result["entity"] = "Knowledge"
            del result["entity_group"]
            knowledge_counter[result["word"]] += 1  # Count frequency of knowledge

    # Aggregate consecutive spans
    if len(output_skills) > 0:
        output_skills = aggregate_span(output_skills)
    if len(output_knowledge) > 0:
        output_knowledge = aggregate_span(output_knowledge)

    # Collect results
    results = {"text": text, "skills": output_skills, "knowledge": output_knowledge}
    return results

# Custom function to handle float32 serialization
def custom_serializer(obj):
    if isinstance(obj, np.float32):
        return float(obj)  # Convert float32 to Python float
    raise TypeError(f"Type {type(obj)} not serializable")

# Main processing function
if __name__ == '__main__':
    input_file = "job_data_0414_classify.json"
    output_file = "extracted_skills_knowledge.json"

    with open(input_file, "r", encoding="utf-8") as f:
        job_data = json.load(f)

    combined_lines = []
    for job in job_data:
        reqs = job.get("Requirements", [])
        combined_lines.extend(reqs)


    # Counters for skill and knowledge frequency
    skill_counter = Counter()
    knowledge_counter = Counter()

    
    # Process each example and collect results
    all_results = []
    for example in combined_lines:
        result = ner(example, skill_counter, knowledge_counter)
        all_results.append(result)
        if (len(all_results) % 100 == 0):
            print(len(all_results))

    # Save extracted results to a JSON file using custom serializer
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=4, default=custom_serializer)

    # Save frequency counts to a separate file using custom serializer
    frequency_data = {
        "skills_frequency": skill_counter.most_common(),
        "knowledge_frequency": knowledge_counter.most_common()
    }
    
    # Save frequencies to a JSON file
    with open("frequency_counts.json", "w", encoding="utf-8") as f:
        json.dump(frequency_data, f, ensure_ascii=False, indent=4, default=custom_serializer)

    # Print the most common skills and knowledge for verification
    print("Most Common Skills:")
    print(skill_counter.most_common(10))  # Top 10 skills
    print("\nMost Common Knowledge:")
    print(knowledge_counter.most_common(10))  # Top 10 knowledge
