import os
import re
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
    
def extract_file_metadata(file_path):
    file_dict = {}
    
    file_name = os.path.basename(file_path)
    file_type = os.path.splitext(file_path)[1]
    file_size = os.path.getsize(file_path)
    
    file_dict["file_name"] = file_name
    file_dict["file_type"] = file_type
    file_dict["file_size"] = file_size
    
    return file_dict

def detect_programming_language(file_content, file_extension):
    
    file_map = {".py" : "python",
                ".js" : "javascript",
                ".ts" : "typescript",
                ".jsx" : "javascript xml",
                ".tsx" : "typescript.xml"}
    
    language = file_map.get(file_extension, "Unknown")
    
    return language

def _resolve_python_import_path(base_path, module_name, all_repo_files):
    all_repo_files_set = set(all_repo_files) 

    if module_name.startswith('.'):
        dots = len(module_name) - len(module_name.lstrip('.'))
        clean_module = module_name[dots:]
        
        path_parts = base_path.split(os.sep)
        
        for _ in range(dots-1):
            if path_parts:
                path_parts.pop()
                
        base = os.sep.join(path_parts)
        module_path = clean_module.replace('.', os.sep)
        
    else: # Direct/Absolute import
        base = base_path 
        module_path = module_name.replace('.', os.sep)
        
    candidates = [
        os.path.join(base, module_path + '.py'),
        os.path.join(base, module_path, '__init__.py') 
    ]
    
    for path in candidates:
        normalized = os.path.normpath(path)
        if normalized in all_repo_files_set: # Use the set for lookup
            return normalized
    
    return None

def _resolve_js_ts_jsx_tsx_path(base_path, module_path, all_repo_files):
    
    all_repo_files_set = set(all_repo_files) #making set of files
    
    #possible extensions for js modules
    possible_extensions = ['.js', '.ts','.tsx', '.jsx', '/index.js', '/index.ts', '/index.jsx']
    
    path_without_quotes = module_path.strip("'\"")
    
    if path_without_quotes.startswith(('./', '../')):
        
        for ext in possible_extensions:
            normalized = os.path.normpath(os.path.join(base_path, path_without_quotes + ext))
            if normalized in all_repo_files_set:
                return normalized
        
        potential_path_exact = os.path.normpath(os.path.join(base_path, path_without_quotes))
        if potential_path_exact in all_repo_files_set:
            return potential_path_exact
    
    return None


def find_dependencies(file_content, file_path, all_repo_files):
    dependencies = []
    all_repo_files_set = set(all_repo_files) 
    
    file_extension = os.path.splitext(file_path)[1].lower()
    
    language_category = 'other'
    
    if file_extension == '.py':
        language_category = 'python'
    if file_extension in ['.js','.ts','.jsx','.tsx']:
        language_category = 'js_ts_jsx_tsx'
    
    current_dir = os.path.dirname(file_path)
    
    if language_category == "python":
        for line in file_content:
            stripped_line = line.strip()
            module = None
            
            if line.startswith("import"):
                parts = stripped_line[len("import "):].split(' ', 1)[0].split(',', 1)[0]
                module_name = parts.split('.')[0]
            
            elif line.startswith("from"):
                parts = stripped_line[len("from "):].split(' ', 1)
                if len(parts)>0:
                    module_name = parts[0].split('.')[0]
                    
            if module_name:
                resolved_path = _resolve_python_import_path(current_dir, module_name, all_repo_files_set)
                if resolved_path and resolved_path!= file_path:
                    dependencies.append(resolved_path)
                    
    elif language_category == "js_ts_jsx_tsx":
        
        for line in file_content:
            stripped_line = line.strip()
            
            if "import" in stripped_line and "from" in stripped_line:
                from_idx = stripped_line.find("from")
                
                if from_idx != -1:
                    import_path_part = stripped_line[from_idx + len(" from "):].strip()
                    if import_path_part.startswith(('"', "'")):
                        closing_quote_idx = import_path_part.find(import_path_part[0], 1)
                        if closing_quote_idx != -1:
                            module_path_str = import_path_part[1:closing_quote_idx]
                
            elif stripped_line.startswith("import ") and (stripped_line.endswith('"') or stripped_line.endswith("'")):
                first_quote_idx = max(stripped_line.find("'"), stripped_line.find('"'))
                if first_quote_idx != -1:
                    close_quote_idx = stripped_line.rfind(stripped_line[first_quote_idx])
                    if closing_quote_idx != first_quote_idx:
                        module_path_str = stripped_line[first_quote_idx+1:closing_quote_idx]
            
            elif "require(" in stripped_line:
                require_idx = stripped_line.find("require(")
                if require_idx != -1:
                    open_paren_idx = require_idx+  len("require(")
                    open_quote_idx = stripped_line.find('"', open_paren_idx)
                    if open_quote_idx == -1:
                        open_quote_idx = stripped_line.find("'", open_paren_idx)
                        
                    if open_quote_idx != -1:
                        closing_quote_idx = stripped_line.find(stripped_line[open_quote_idx], open_quote_idx + 1)
                        if closing_quote_idx != -1:
                            module_path_str = stripped_line[open_quote_idx+1:closing_quote_idx]
                            
            if module_path_str:
                js_path_resolve = _resolve_js_ts_jsx_tsx_path(current_dir, module_path_str, all_repo_files_set)
                if js_path_resolve and js_path_resolve != file_path:
                        dependencies.append(js_path_resolve)
    
    return list(dependencies)
                    
        
                    
                      
        
    
                
