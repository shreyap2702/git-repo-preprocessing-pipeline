# main_pipeline.py
import os
import json
from src.pipeline import cloner         
from src.pipeline import file_processing 
import shutil
from datetime import datetime

def run_pipeline():
    """
    Orchestrates the entire process:
    1. Prompts the user for a GitHub repository URL.
    2. Clones the repository.
    3. Analyzes the cloned repository.
    4. Saves the analysis results as JSON file.
    5. Prints the analysis results.
    6. Cleans up the cloned repository (based on user preference).
    """
    github_url = input("Enter the GitHub repository URL (e.g., https://github.com/username/repo): ").strip()
    
    save_input = input("Do you want to save the repository locally? (Default: Yes) [y/N]: ").strip().lower()
    save = not (save_input in ['n', 'no', 'false', '0'])
    
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
            
            # Step 4: Save analysis results to JSON file
            repo_name = os.path.basename(github_url.rstrip('/').replace('.git', ''))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{repo_name}_analysis_{timestamp}.json"
            
            # Create output directory if it doesn't exist
            output_dir = "analysis_results"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, output_filename)
            
            # Write JSON to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(analysis_json)
            
            print(f"\n--- Analysis saved to: {output_path} ---")
            
            # Step 5: Print summary statistics
            print("\n--- Analysis Summary ---")
            analysis_data = json.loads(analysis_json)
            print(f"Total files analyzed: {len(analysis_data)}")
            
            total_functions = sum(len(file_data.get('functions', [])) for file_data in analysis_data)
            print(f"Total functions found: {total_functions}")
            
            # Count files by language
            language_counts = {}
            for file_data in analysis_data:
                lang = file_data.get('language', 'Unknown')
                language_counts[lang] = language_counts.get(lang, 0) + 1
            
            print("\nFiles by language:")
            for lang, count in sorted(language_counts.items()):
                print(f"  {lang}: {count}")
            
            # Print external libraries summary
            all_external_libs = set()
            for file_data in analysis_data:
                all_external_libs.update(file_data.get('external_libraries', []))
            
            if all_external_libs:
                print(f"\nExternal libraries used: {len(all_external_libs)}")
                print("  " + ", ".join(sorted(list(all_external_libs))[:10]))
                if len(all_external_libs) > 10:
                    print(f"  ... and {len(all_external_libs) - 10} more")
            
            # Ask if user wants to see full JSON output
            show_full = input("\nDo you want to see the full JSON output in console? [y/N]: ").strip().lower()
            if show_full in ['y', 'yes']:
                print("\n--- Full Analysis Results (JSON Output) ---")
                print(analysis_json)
            else:
                print(f"\nFull analysis is available in: {output_path}")
                
        else:
            print(f"\n--- Failed to clone repository: {github_url}. Analysis skipped. ---")

    except Exception as e:
        print(f"\n--- An unexpected error occurred during the pipeline execution: {e} ---")
        import traceback
        traceback.print_exc()
    finally:
        # Step 6: Clean up the cloned repository (based on user choice)
        if cloned_repo_path and os.path.exists(cloned_repo_path):
            print(f"\n--- Cleaning up cloned repository at: {cloned_repo_path} ---")
            cloner.cleanup_repo(cloned_repo_path, save)
            if not save:
                print("--- Cleanup complete ---")
            else:
                print(f"\n--- Repository Saved Locally at path --- {cloned_repo_path}")
        elif cloned_repo_path:
            print(f"\n--- No repository found at {cloned_repo_path} to clean up (might have failed cloning early). ---")

if __name__ == "__main__":
    run_pipeline()