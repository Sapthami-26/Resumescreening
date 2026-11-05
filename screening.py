import json
import os
import re
from typing import Any, Dict, List
from docx import Document
import pandas as pd
from pypdf import PdfReader

SKILL_ALIASES = {
    "python": ["python"],
    "sql": ["sql", "mysql", "postgresql", "postgres", "sqlite"],
    "excel": ["excel", "ms excel", "microsoft excel"],
    "communication": [
        "communication",
        "communicating",
        "presentation",
        "presentations",
    ],
    "dashboard": ["dashboard", "dashboards", "reporting"],
    "data visualization": [
        "data visualization",
        "visualization",
        "power bi charts",
        "charts",
        "graphing",
    ],
    "tableau": ["tableau"],
    "power bi": ["power bi", "powerbi"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "machine learning": ["machine learning", "ml", "predictive modeling"],
}

EDU_LEVELS = {
    "unknown": 0,
    "high school": 1,
    "diploma": 2,
    "bachelor": 3,
    "master": 4,
    "phd": 5,
}


def read_text_file(file_path: str) -> str:
  with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
    return f.read()


def read_pdf_file(file_path: str) -> str:
  reader = PdfReader(file_path)
  text = ""
  for page in reader.pages:
    text += page.extract_text() or ""
  return text


def read_docx_file(file_path: str) -> str:
  doc = Document(file_path)
  text = []
  for para in doc.paragraphs:
    text.append(para.text)
  return "\n".join(text)


def normalize_text(text: str) -> str:
  return text.lower()


def find_years_experience(text: str) -> int:
  text = normalize_text(text)
  matches = re.findall(r"(\d+)\+?\s*years?", text)
  if matches:
    return max(int(m) for m in matches)
  return 0


def detect_education(text: str) -> str:
  text = normalize_text(text)
  if "phd" in text or "doctorate" in text:
    return "phd"
  if "master" in text or "m.tech" in text or "mca" in text:
    return "master"
  if (
      "bachelor" in text
      or "b.tech" in text
      or "b.e." in text
      or "be" in text
      or "bsc" in text
      or "b.sc" in text
  ):
    return "bachelor"
  if "diploma" in text:
    return "diploma"
  if "school" in text:
    return "high school"
  return "unknown"


def extract_skills_from_text(
    text: str, skill_map: Dict[str, List[str]]
) -> List[str]:
  text = normalize_text(text)
  found = []
  for canonical_skill, aliases in skill_map.items():
    for alias in aliases:
      if alias in text:
        found.append(canonical_skill)
        break
  return list(dict.fromkeys(found))


def parse_job_description(jd_text: str) -> Dict[str, Any]:
  jd = normalize_text(jd_text)

  required_skills = []
  preferred_skills = []

  required_candidates = [
      "python",
      "sql",
      "excel",
      "communication",
      "dashboard",
      "data visualization",
  ]
  preferred_candidates = [
      "tableau",
      "power bi",
      "pandas",
      "numpy",
      "machine learning",
  ]

  for skill in required_candidates:
    if skill in jd:
      required_skills.append(skill)

  for skill in preferred_candidates:
    if skill in jd:
      preferred_skills.append(skill)

  years_match = re.search(r"(\d+)\s*to\s*(\d+)\s*years", jd)
  if years_match:
    min_years = int(years_match.group(1))
  else:
    year_match = re.search(r"(\d+)\s*years", jd)
    min_years = int(year_match.group(1)) if year_match else 0

  required_education = "bachelor"
  if "master" in jd:
    required_education = "master"
  elif "phd" in jd:
    required_education = "phd"

  return {
      "required_skills": list(dict.fromkeys(required_skills)),
      "preferred_skills": list(dict.fromkeys(preferred_skills)),
      "min_years": min_years,
      "required_education": required_education,
  }


def parse_resume(resume_text: str) -> Dict[str, Any]:
  text = normalize_text(resume_text)

  name_match = re.search(r"name:\s*(.+)", text)
  email_match = re.search(r"email:\s*(.+)", text)

  years = find_years_experience(text)
  education_level = detect_education(text)

  skills = extract_skills_from_text(text, SKILL_ALIASES)

  return {
      "name": name_match.group(1).strip().title() if name_match else "Unknown",
      "email": email_match.group(1).strip() if email_match else "",
      "skills": skills,
      "years_experience": years,
      "education_level": education_level,
      "raw_text": resume_text,
  }


def score_candidate(
    candidate: Dict[str, Any], criteria: Dict[str, Any]
) -> Dict[str, Any]:
  required_skills = criteria["required_skills"]
  preferred_skills = criteria["preferred_skills"]
  min_years = criteria["min_years"]
  required_education = criteria["required_education"]

  candidate_skills = set(candidate["skills"])

  matched_required = [s for s in required_skills if s in candidate_skills]
  matched_preferred = [s for s in preferred_skills if s in candidate_skills]

  if required_skills:
    skills_score = round((len(matched_required) / len(required_skills)) * 50)
  else:
    skills_score = 0

  if min_years > 0:
    if candidate["years_experience"] >= min_years:
      experience_score = 25
    else:
      experience_score = round(
          (candidate["years_experience"] / min_years) * 25
      )
  else:
    experience_score = 0

  if EDU_LEVELS.get(candidate["education_level"], 0) >= EDU_LEVELS.get(
      required_education, 0
  ):
    education_score = 15
  else:
    education_score = 0

  if preferred_skills:
    preferred_score = round(
        (len(matched_preferred) / len(preferred_skills)) * 10
    )
  else:
    preferred_score = 0

  total_score = min(
      100, skills_score + experience_score + education_score + preferred_score
  )

  strengths = []
  if matched_required:
    strengths.append(f"matches required skills: {', '.join(matched_required)}")
  if matched_preferred:
    strengths.append(f"knows preferred skills: {', '.join(matched_preferred)}")
  if candidate["years_experience"] >= min_years and min_years > 0:
    strengths.append(
        f"meets experience requirement with {candidate['years_experience']}"
        " years"
    )
  if EDU_LEVELS.get(candidate["education_level"], 0) >= EDU_LEVELS.get(
      required_education, 0
  ):
    strengths.append(
        f"meets education requirement ({candidate['education_level']})"
    )

  gaps = []
  missing_required = [s for s in required_skills if s not in candidate_skills]
  if missing_required:
    gaps.append(f"missing required skills: {', '.join(missing_required)}")
  missing_preferred = [
      s for s in preferred_skills if s not in candidate_skills
  ]
  if missing_preferred:
    gaps.append(f"missing preferred skills: {', '.join(missing_preferred)}")
  if candidate["years_experience"] < min_years:
    gaps.append(
        f"below required experience: has {candidate['years_experience']}"
        f" years, needs {min_years}"
    )
  if EDU_LEVELS.get(candidate["education_level"], 0) < EDU_LEVELS.get(
      required_education, 0
  ):
    gaps.append(
        f"below required education: {candidate['education_level']}"
    )

  reasoning = ""
  if strengths:
    reasoning += "Strengths: " + "; ".join(strengths) + ". "
  if gaps:
    reasoning += "Gaps: " + "; ".join(gaps) + "."

  return {
      "name": candidate["name"],
      "email": candidate["email"],
      "score": total_score,
      "skills_score": skills_score,
      "experience_score": experience_score,
      "education_score": education_score,
      "preferred_score": preferred_score,
      "matched_required_skills": matched_required,
      "matched_preferred_skills": matched_preferred,
      "reasoning": reasoning.strip(),
  }


def rank_candidates(
    candidates: List[Dict[str, Any]], criteria: Dict[str, Any]
) -> List[Dict[str, Any]]:
  scored = [score_candidate(candidate, criteria) for candidate in candidates]
  scored.sort(key=lambda x: x["score"], reverse=True)
  return scored


def save_results_csv(results: List[Dict[str, Any]], output_path: str):
  df = pd.DataFrame(results)
  if not df.empty:
    df.insert(0, "rank", range(1, len(df) + 1))
  df.to_csv(output_path, index=False)


def save_results_json(results: List[Dict[str, Any]], output_path: str):
  with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)