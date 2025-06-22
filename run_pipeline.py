# main_pipeline.py
import os
import json
from src.pipeline import cloner         
from src.pipeline import file_processing 
import shutil        

def run_pipeline():
    """
    Orchestrates the entire process:
    1. Prompts the user for a GitHub repository URL.
    2. Clones the repository.
    3. Analyzes the cloned repository.
    4. Prints the analysis results as JSON.
    5. Cleans up the cloned repository.
    """
    github_url = input("Enter the GitHub repository URL (e.g., https://github.com/username/repo): ").strip()

    cloned_repo_path = None
    try:
        # Step 1 & 2: Clone the repository
        print(f"\n--- Attempting to clone repository: {github_url} ---")
        cloned_repo_path = cloner.process_repo_clone(github_url)

        if cloned_repo_path:
            print(f"\n--- Successfully cloned to: {cloned_repo_path} ---")
            
            # Step 3: Analyze the cloned repository
            print("\n--- Starting repository analysis ---")
            analysis_json = file_processing.process_repository_for_json(cloned_repo_path)
            
            # Step 4: Print the analysis results
            print("\n--- Analysis Results (JSON Output) ---")
            print(analysis_json)

        else:
            print(f"\n--- Failed to clone repository: {github_url}. Analysis skipped. ---")

    except Exception as e:
        print(f"\n--- An unexpected error occurred during the pipeline execution: {e} ---")
    finally:
        # Step 5: Clean up the cloned repository (even if errors occurred)
        if cloned_repo_path and os.path.exists(cloned_repo_path):
            print(f"\n--- Cleaning up cloned repository at: {cloned_repo_path} ---")
            cloner.cleanup_repo(cloned_repo_path)
            print("--- Cleanup complete ---")
        elif cloned_repo_path:
             print(f"\n--- No repository found at {cloned_repo_path} to clean up (might have failed cloning early). ---")

if __name__ == "__main__":
    run_pipeline()