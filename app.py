# app.py
import streamlit as st
import os
import json
from src.pipeline import cloner, file_processing

st.set_page_config(page_title="Repo Analyzer", layout="wide")

st.title(" GitHub Repository Analyzer")

# Input box for GitHub URL
github_url = st.text_input("Enter GitHub repository URL:", "")

if st.button("Run Analysis"):
    if not github_url.strip():
        st.warning("⚠️ Please enter a valid GitHub URL")
    else:
        cloned_repo_path = None
        try:
            st.info(f"Cloning repository from: {github_url} ...")
            cloned_repo_path = cloner.process_repo_clone(github_url)

            if cloned_repo_path:
                st.success("✅ Repository successfully cloned")

                # Run analysis
                st.write("🔍 Running analysis...")
                analysis_json = file_processing.process_repository_for_json(cloned_repo_path)

                # Convert string JSON to dict if needed
                if isinstance(analysis_json, str):
                    try:
                        analysis_json = json.loads(analysis_json)
                    except:
                        st.error("Could not parse analysis output")
                        analysis_json = {}

                # Show raw JSON only
                st.subheader("📦 Analysis Results (Raw JSON)")
                st.json(analysis_json)

            else:
                st.error("❌ Failed to clone repository. Please check the URL.")

        except Exception as e:
            st.error(f"Unexpected error: {e}")

        finally:
            if cloned_repo_path and os.path.exists(cloned_repo_path):
                cloner.cleanup_repo(cloned_repo_path)
                st.info("🧹 Temporary repository cleaned up")
