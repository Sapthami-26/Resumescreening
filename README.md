# Resume Screening Agent

This project is an AI-style resume screening agent that takes a job description and a folder of resumes, then ranks candidates from best to worst with scores and reasoning.

## What it does
- Reads a job description
- Reads 10+ resume text files
- Extracts key skills, experience, and education
- Scores each resume against the job criteria
- Produces a ranked shortlist
- Saves results as CSV and JSON

## Folder Structure
```bash
resume-screening-agent/
├── main.py
├── screening.py
├── requirements.txt
├── README.md
├── data/
│   ├── job_description.txt
│   └── resumes/
│       ├── candidate1.txt
│       ├── candidate2.txt
│       └── ...
└── output/
```

## Setup Instructions

### 1. Install Python
Make sure Python 3.10 or above is installed.

### 2. Create a virtual environment
```bash
python -m venv .venv
```

Activate it:

**Windows**
```bash
.venv\Scripts\activate
```

**Mac/Linux**
```bash
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

## Input Files
- `data/job_description.txt` contains the job description
- `data/resumes/` contains sample resumes in `.txt` format

## How to Run
```bash
python main.py --jd data/job_description.txt --resumes data/resumes
```

## Output Files
The agent creates:
- `output/ranked_candidates.csv`
- `output/ranked_candidates.json`

## Scoring Method
The scoring is based on a 100-point system:

- Required skills match: 50 points
- Experience match: 25 points
- Education match: 15 points
- Preferred skills match: 10 points

The agent compares resume text against job criteria and assigns a final score out of 100.

## Sample Job Criteria
Example:
- Required skills: Python, SQL, Excel, Communication, Dashboard, Data Visualization
- Preferred skills: Tableau, Power BI, Pandas, NumPy, Machine Learning
- Minimum experience: 1 year
- Education: Bachelor’s degree

## Tradeoffs and Limitations
- This version uses rule-based parsing, which is simple and easy to explain.
- It works best with clean text resumes.
- PDF/DOCX support can be added later.
- More advanced NLP or embeddings could improve matching accuracy.
- Some resume wording may not be detected if it uses unusual phrasing.

## Sample Result
The output ranks candidates by score and shows a short reasoning summary for each candidate.

## Future Improvements
- Add PDF and DOCX resume support
- Use LLM extraction for stronger resume parsing
- Add semantic similarity with embeddings
- Add a CLI interface with custom input paths
- Improve skill synonym detection