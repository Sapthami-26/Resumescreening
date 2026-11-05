import argparse
import os
from screening import (
    parse_job_description,
    parse_resume,
    rank_candidates,
    read_docx_file,
    read_pdf_file,
    read_text_file,
    save_results_csv,
    save_results_json,
)


def main():
  parser = argparse.ArgumentParser(description="Resume Screening Agent")
  parser.add_argument(
      "--jd",
      default="data/job_description.txt",
      help="Path to job description file",
  )
  parser.add_argument(
      "--resumes", default="data/resumes", help="Path to resume folder"
  )
  parser.add_argument(
      "--csv", default="output/ranked_candidates.csv", help="CSV output path"
  )
  parser.add_argument(
      "--json", default="output/ranked_candidates.json", help="JSON output path"
  )
  args = parser.parse_args()

  os.makedirs("output", exist_ok=True)

  if not os.path.exists(args.jd):
    print(f"Error: Job description file not found at '{args.jd}'")
    return

  if not os.path.exists(args.resumes):
    print(f"Error: Resume directory not found at '{args.resumes}'")
    return

  jd_text = read_text_file(args.jd)
  criteria = parse_job_description(jd_text)

  print("\n=== JOB CRITERIA ===")
  print(criteria)

  candidates = []

  for file_name in os.listdir(args.resumes):
    file_path = os.path.join(args.resumes, file_name)

    if os.path.isfile(file_path):
      ext = file_name.lower()
      if ext.endswith(".txt"):
        resume_text = read_text_file(file_path)
      elif ext.endswith(".pdf"):
        resume_text = read_pdf_file(file_path)
      elif ext.endswith(".docx"):
        resume_text = read_docx_file(file_path)
      else:
        continue

      candidate = parse_resume(resume_text)
      candidates.append(candidate)

  if not candidates:
    print("\nNo valid resumes (.txt, .pdf, .docx) found.")
    return

  ranked_results = rank_candidates(candidates, criteria)

  save_results_csv(ranked_results, args.csv)
  save_results_json(ranked_results, args.json)

  print("\n=== RANKED CANDIDATES ===")
  for i, r in enumerate(ranked_results, 1):
    print(f"{i}. {r['name']} - Score: {r['score']}")
    print(f"   Reason: {r['reasoning']}")

  print(f"\nSaved CSV to: {args.csv}")
  print(f"Saved JSON to: {args.json}")

  print("\n=== SUMMARY ===")
  print(f"Total candidates processed: {len(ranked_results)}")
  if ranked_results:
    avg_score = sum(r["score"] for r in ranked_results) / len(ranked_results)
    print(f"Average score: {avg_score:.2f}")
    print("Top 3 candidates:")
    for r in ranked_results[:3]:
      print(f"- {r['name']} ({r['score']})")


if __name__ == "__main__":
  main()