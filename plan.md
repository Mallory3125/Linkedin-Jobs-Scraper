
## ✅ Week 1: Data Collection & Preprocessing

### Must Do
- [x] Finalize Linkedin job scraping script 
- [ ] Store job data with fields: `title`, `company`, `location`, `description`, `date`
- [ ] Clean job descriptions (strip HTML, normalize whitespace, lowercase, etc.)
- [ ] Split description into sections:
  - [ ] About Company
  - [ ] Responsibilities
  - [ ] Requirements / Qualifications

### Nice to Have
- [ ] Add automatic retry or proxy handling to scraper
- [ ] Store both raw and cleaned descriptions for reference

### Avoid (Time Sink)
- ❌ Making the scraper handle every possible HTML variation
- ❌ Scraping more than ~1000 posts for initial analysis

---

## ✅ Week 2: Skill & Info Extraction

### Must Do
- [ ] Extract technical skills from requirements section (using regex or NLP)
- [ ] Normalize similar terms (e.g., “Python 3” → “Python”)
- [ ] Create structured job records with:
  - [ ] Title
  - [ ] Required skills
  - [ ] Key responsibilities

### Nice to Have
- [ ] Extract soft skills (e.g., teamwork, communication)
- [ ] Try tagging job level (Junior/Mid/Senior) based on text heuristics

### Avoid (Time Sink)
- ❌ Building a perfect skill extractor — aim for 80% accuracy
- ❌ Manually curating a huge tech skill dictionary

---

## ✅ Week 3: Analysis & Visualization

### Must Do
- [ ] Identify top skills per role (e.g., Data Analyst vs. ML Engineer)
- [ ] Compare role expectations (tools, verbs used, qualifications)
- [ ] Visualize findings (bar charts, word clouds, etc.)

### Nice to Have
- [ ] Cluster job descriptions using sentence embeddings (e.g., BERT)
- [ ] Visualize clusters with UMAP/t-SNE

### Avoid (Time Sink)
- ❌ Over-optimizing clustering or tuning models
- ❌ Spending too long polishing chart aesthetics

---

## ✅ Week 4: Personal Matching & Polish

### Must Do
- [ ] Match user skill profile (manual input or resume) to job posts
- [ ] Highlight missing skills for each match
- [ ] Write clear README:
  - [ ] Project goal & motivation
  - [ ] Pipeline overview
  - [ ] Key findings and visualizations
- [ ] Push final code & results to GitHub

### Nice to Have
- [ ] Create a simple Streamlit dashboard demo
- [ ] Add job export (e.g., top matching jobs to CSV)

### Avoid (Time Sink)
- ❌ Spending too long tweaking frontend styling
- ❌ Writing a full blog post unless you finish early

---

## 🧠 Outcome

- End-to-end DS/ML pipeline from web scraping → NLP → analysis → visualization
- Useful for personal job tracking
- Conversation-starter project for interviews
