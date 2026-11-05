import json
import os
import tempfile
import pandas as pd
import streamlit as st
from screening import (
    parse_job_description,
    parse_resume,
    rank_candidates,
    read_docx_file,
    read_pdf_file,
    read_text_file,
)

# Page Configuration
st.set_page_config(
    page_title="AI Resume Screening Agent", page_icon="📄", layout="wide"
)

st.title("📄 AI Resume Screening Agent")
st.markdown(
    "Automate candidate evaluation by matching resumes against job requirements."
)

# --- Sidebar Controls ---
st.sidebar.header("Configuration")

# Job Description Input
default_jd = """Data Analyst Requirements:
- Required Skills: Python, SQL, Excel, Communication, Dashboard, Data Visualization
- Preferred Skills: Tableau, Power BI, Pandas, NumPy, Machine Learning
- Experience: 2 years
- Education: Bachelor degree or higher"""

jd_text = st.sidebar.text_area(
    "Job Description", value=default_jd, height=220
)

# Resume File Upload
uploaded_files = st.sidebar.file_uploader(
    "Upload Candidate Resumes",
    type=["txt", "pdf", "docx"],
    accept_multiple_files=True,
    help="Upload single or multiple resumes in .txt, .pdf, or .docx format.",
)

# Run Button
run_screening = st.sidebar.button("Screen Candidates", type="primary")

# --- Main Dashboard Section ---
if run_screening:
    if not jd_text.strip():
        st.error("Please provide a valid Job Description.")
    elif not uploaded_files:
        st.warning("Please upload at least one resume file to screen.")
    else:
        # Progress Tracking setup for multi-file processing
        progress_bar = st.progress(0)
        status_text = st.empty()

        # 1. Parse JD
        status_text.text("Analyzing job description requirements...")
        criteria = parse_job_description(jd_text)

        # 2. Extract and parse uploaded files
        candidates = []
        total_files = len(uploaded_files)

        for idx, file in enumerate(uploaded_files):
            status_text.text(f"Processing candidate {idx + 1}/{total_files}: {file.name}...")
            file_ext = os.path.splitext(file.name)[1].lower()

            # Save to temporary file to allow standard reader functions
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=file_ext
            ) as tmp_file:
                tmp_file.write(file.read())
                tmp_path = tmp_file.name

            try:
                if file_ext == ".txt":
                    raw_text = read_text_file(tmp_path)
                elif file_ext == ".pdf":
                    raw_text = read_pdf_file(tmp_path)
                elif file_ext == ".docx":
                    raw_text = read_docx_file(tmp_path)
                else:
                    raw_text = ""

                if raw_text.strip():
                    candidate = parse_resume(raw_text)

                    # Clean candidate name if fallback is triggered
                    if candidate.get("name") in ["Unknown", "Unknown Candidate", "", None]:
                        clean_name = (
                            os.path.splitext(file.name)[0]
                            .replace("_", " ")
                            .replace("-", " ")
                            .strip()
                            .title()
                        )
                        candidate["name"] = clean_name

                    candidates.append(candidate)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

            progress_bar.progress((idx + 1) / total_files)

        # Clear progress indicators
        status_text.empty()
        progress_bar.empty()

        if not candidates:
            st.error("Failed to extract readable text from the uploaded files.")
        else:
            # 3. Rank Candidates
            ranked_results = rank_candidates(candidates, criteria)

            # Build DataFrame with Rank column
            df_results = pd.DataFrame(ranked_results)
            df_results.insert(0, "Rank", range(1, len(df_results) + 1))

            # --- Summary Metrics Section ---
            st.subheader("📊 Candidate Overview")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Candidates", len(ranked_results))

            avg_score = sum(r["score"] for r in ranked_results) / len(
                ranked_results
            )
            col2.metric("Average Score", f"{avg_score:.1f} / 100")

            top_candidate = ranked_results[0]["name"]
            col3.metric("Top Candidate", top_candidate)

            st.divider()

            # --- Visual Score Comparison Charts ---
            st.subheader("📈 Score Breakdown & Comparison")

            chart_data = df_results[["name", "skills_score", "experience_score", "education_score"]].copy()
            chart_data = chart_data.rename(columns={
                "name": "Candidate",
                "skills_score": "Skills Score (Max 50)",
                "experience_score": "Experience Score (Max 25)",
                "education_score": "Education Score (Max 15)"
            })

            tab1, tab2 = st.tabs(["📊 Skills vs Experience", "🥞 Stacked Score Breakdown"])

            with tab1:
                st.markdown("##### Direct Side-by-Side Comparison")
                st.bar_chart(
                    chart_data,
                    x="Candidate",
                    y=["Skills Score (Max 50)", "Experience Score (Max 25)"],
                    stack=False,
                    height=360
                )

            with tab2:
                st.markdown("##### Total Cumulative Score Composition")
                st.bar_chart(
                    chart_data,
                    x="Candidate",
                    y=["Skills Score (Max 50)", "Experience Score (Max 25)", "Education Score (Max 15)"],
                    stack=True,
                    height=360
                )

            st.divider()

            # --- Detailed Results Table ---
            st.subheader("🏆 Ranked Candidates")

            display_cols = [
                "Rank",
                "name",
                "score",
                "skills_score",
                "experience_score",
                "education_score",
                "reasoning",
            ]
            available_cols = [c for c in display_cols if c in df_results.columns]

            st.dataframe(
                df_results[available_cols].rename(
                    columns={
                        "name": "Name",
                        "score": "Total Score",
                        "skills_score": "Skills",
                        "experience_score": "Experience",
                        "education_score": "Education",
                        "reasoning": "Strengths & Gaps",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

            # --- Candidate Detail Expanders ---
            st.subheader("🔍 Breakdown by Candidate")
            for idx, result in enumerate(ranked_results, 1):
                with st.expander(
                    f"#{idx} - {result['name']} (Score: {result['score']}/100)"
                ):
                    st.write(f"**Email:** {result.get('email', 'N/A')}")
                    st.write(f"**Reasoning:** {result['reasoning']}")

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown("**Matched Required Skills:**")
                        st.write(
                            ", ".join(result.get("matched_required_skills", []))
                            or "None"
                        )
                    with col_b:
                        st.markdown("**Matched Preferred Skills:**")
                        st.write(
                            ", ".join(result.get("matched_preferred_skills", []))
                            or "None"
                        )

                    # Option to view raw text extracted from resume
                    if "raw_text" in result:
                        with st.expander("📄 View Extracted Text"):
                            st.text(result["raw_text"])

            st.divider()

            # --- Download Options ---
            st.subheader("📥 Export Results")
            d_col1, d_col2 = st.columns(2)

            # Download CSV
            csv_data = df_results.to_csv(index=False).encode("utf-8")
            d_col1.download_button(
                label="Download CSV",
                data=csv_data,
                file_name="ranked_candidates.csv",
                mime="text/csv",
            )

            # Download JSON
            json_data = json.dumps(ranked_results, indent=2)
            d_col2.download_button(
                label="Download JSON",
                data=json_data,
                file_name="ranked_candidates.json",
                mime="application/json",
            )
else:
    st.info(
        "👈 Configure the Job Description and upload resume files in the sidebar,"
        " then click **Screen Candidates** to run the agent."
    )