import os
from pathlib import Path

import os

def discover_and_filter_files(repo_root_path):
    filtered_files = []
    valid_extensions = ['.py','.js','.tsx','.ts']
    
    for root, dirs, files in os.walk(repo_root_path):
        for file_name in files:
            file_extension = os.path.splitext(file_name)[1]
            if file_extension in valid_extensions:
                full_file_path = os.path.join(root, file_name)
                filtered_files.append(full_file_path)
    
    return filtered_files

def read_file_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            return content
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    
def file_metadata(file_path):
    file_dict = {}
    
    file_name = os.path.basename(file_path)
    