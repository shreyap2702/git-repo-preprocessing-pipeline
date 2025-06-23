import os
import json
import re

def discover_and_filter_files(repo_root_path):
    filtered_files = []
    valid_extensions = ['.py', '.js', '.tsx', '.ts']
    
    for root, dirs, files in os.walk(repo_root_path):
        for file_name in files:
            file_extension = os.path.splitext(file_name)[1]
            if file_extension in valid_extensions:
                full_file_path = os.path.join(root, file_name)
                filtered_files.append(os.path.abspath(full_file_path))
    
    return filtered_files

def read_file_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None

def extract_file_metadata(file_path):
    return {
        "file_name": os.path.basename(file_path),
        "file_type": os.path.splitext(file_path)[1],
        "file_size": os.path.getsize(file_path)
    }

def detect_programming_language(file_content, file_extension):
    return {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript xml",
        ".tsx": "typescript xml"
    }.get(file_extension, "Unknown")

def _resolve_python_import_path(base_path, module_name, all_repo_files):
    all_repo_files_set = set(all_repo_files)

    if module_name.startswith('.'):
        dots = len(module_name) - len(module_name.lstrip('.'))
        clean_module = module_name[dots:]
        path_parts = base_path.split(os.sep)
        for _ in range(dots - 1):
            if path_parts:
                path_parts.pop()
        base = os.sep.join(path_parts) if path_parts else base_path
        module_path = clean_module.replace('.', os.sep)
    else:
        base = base_path
        module_path = module_name.replace('.', os.sep)

    candidates = []
    if module_path:
        candidates += [
            os.path.join(base, module_path + '.py'),
            os.path.join(base, module_path, '__init__.py'),
        ]

    if not module_name.startswith('.'):
        current_base = base
        while current_base and current_base != os.path.dirname(current_base):
            candidates += [
                os.path.join(current_base, module_path + '.py'),
                os.path.join(current_base, module_path, '__init__.py'),
            ]
            current_base = os.path.dirname(current_base)

    for path in candidates:
        if os.path.normpath(path) in all_repo_files_set:
            return os.path.normpath(path)

    return None

def _resolve_js_ts_jsx_tsx_path(base_path, module_path, all_repo_files):
    all_repo_files_set = set(all_repo_files)
    possible_extensions = ['.js', '.ts', '.tsx', '.jsx']
    index_files = ['/index.js', '/index.ts', '/index.jsx', '/index.tsx']
    path_without_quotes = module_path.strip("'\"")

    if path_without_quotes.startswith(('./', '../', '/')):
        base_candidate = os.path.join(base_path, path_without_quotes)
        for ext in [''] + possible_extensions + index_files:
            candidate = os.path.normpath(base_candidate + ext)
            if candidate in all_repo_files_set:
                return candidate

    return None

def find_dependencies(file_content, file_path, all_repo_files):
    dependencies = []
    all_repo_files_set = set(all_repo_files)
    file_extension = os.path.splitext(file_path)[1].lower()
    language_category = 'python' if file_extension == '.py' else (
        'js_ts_jsx_tsx' if file_extension in ['.js', '.ts', '.jsx', '.tsx'] else 'other'
    )
    current_dir = os.path.dirname(file_path)

    if language_category == "python":
        for line in file_content.splitlines():
            stripped_line = line.strip()
            module_name = None
            if not stripped_line or stripped_line.startswith('#'):
                continue
            if stripped_line.startswith("import "):
                import_part = stripped_line[7:].strip().split(" as ")[0].split(',')[0].split('#')[0].strip()
                module_name = import_part
            elif stripped_line.startswith("from "):
                from_part = stripped_line[5:].strip()
                if " import " in from_part:
                    module_name = from_part.split(" import ")[0].split('#')[0].strip()
            if module_name:
                resolved_path = _resolve_python_import_path(current_dir, module_name, all_repo_files)
                if resolved_path and resolved_path != file_path:
                    dependencies.append(resolved_path)

    elif language_category == "js_ts_jsx_tsx":
        for line in file_content.splitlines():
            stripped_line = line.strip()
            module_path_str = None
            if not stripped_line or stripped_line.startswith('//') or stripped_line.startswith('/*'):
                continue
            if "import" in stripped_line and " from " in stripped_line:
                import_path_part = stripped_line.split(" from ")[-1].strip()
                if import_path_part[0] in ['"', "'"]:
                    module_path_str = import_path_part[1:].split(import_path_part[0])[0]
            elif stripped_line.startswith("import "):
                import_part = stripped_line[7:].strip()
                if import_part[0] in ['"', "'"]:
                    module_path_str = import_part[1:].split(import_part[0])[0]
            elif "require(" in stripped_line:
                after_require = stripped_line.split("require(", 1)[1]
                for q in ['"', "'"]:
                    if q in after_require:
                        module_path_str = after_require.split(q)[1]
                        break
            if module_path_str and module_path_str.startswith(('./', '../', '/')):
                resolved = _resolve_js_ts_jsx_tsx_path(current_dir, module_path_str, all_repo_files)
                if resolved and resolved != file_path:
                    dependencies.append(resolved)

    return list(set(dependencies))

def extract_function_definitions(file_content, language):
    functions = []
    lines = file_content.splitlines()

    if language == "python":
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("def ") and "(" in stripped and ":" in stripped:
                name_start = stripped.find("def ") + len("def ")
                name_end = stripped.find("(", name_start)
                func_name = stripped[name_start:name_end].strip()
                if func_name and " " not in func_name:
                    functions.append(func_name)

    elif language in ["javascript", "typescript", "javascript xml", "typescript xml"]:
        patterns = [
            r'function\s+([a-zA-Z0-9_]+)\s*\(',
            r'const\s+([a-zA-Z0-9_]+)\s*=\s*function\s*\(',
            r'const\s+([a-zA-Z0-9_]+)\s*=\s*\(?.*?\)?\s*=>',
            r'let\s+([a-zA-Z0-9_]+)\s*=\s*function\s*\(',
            r'let\s+([a-zA-Z0-9_]+)\s*=\s*\(?.*?\)?\s*=>',
            r'export\s+function\s+([a-zA-Z0-9_]+)\s*\(',
            r'export\s+const\s+([a-zA-Z0-9_]+)\s*=\s*\(?.*?\)?\s*=>'
        ]
        for line in lines:
            stripped = line.strip()
            for pattern in patterns:
                match = re.search(pattern, stripped)
                if match:
                    functions.append(match.group(1))

    return list(set(functions))

def process_repository_for_json(repo_root_path):
    all_repo_files = [os.path.abspath(p) for p in discover_and_filter_files(repo_root_path)]
    processed_files_data = []
    all_repo_files_set = set(all_repo_files)
    file_content_cache = {}
    file_defined_functions_cache = {}

    for file_path in all_repo_files:
        content = read_file_content(file_path)
        if content is None:
            continue
        abs_path = os.path.abspath(file_path)
        file_content_cache[abs_path] = content
        metadata = extract_file_metadata(abs_path)
        language = detect_programming_language(content, metadata["file_type"])
        defined_functions = extract_function_definitions(content, language)
        file_defined_functions_cache[abs_path] = defined_functions

        processed_files_data.append({
            "file_path": os.path.relpath(abs_path, repo_root_path),
            "metadata": metadata,
            "language": language,
            "functions": defined_functions,
            "dependencies": [],
            "used_functions_from_dependencies_hints": []
        })

    for file_entry in processed_files_data:
        abs_file_path = os.path.abspath(os.path.join(repo_root_path, file_entry["file_path"]))
        content = file_content_cache.get(abs_file_path, "")
        abs_dependencies = find_dependencies(content, abs_file_path, all_repo_files_set)

        file_entry["dependencies"] = [
            os.path.relpath(dep, repo_root_path) for dep in abs_dependencies
        ]

        used_hints = []
        for dep_path in abs_dependencies:
            if dep_path in file_defined_functions_cache:
                for func_name in file_defined_functions_cache[dep_path]:
                    if func_name in content:
                        used_hints.append(f"{os.path.basename(dep_path)}:{func_name}")

        file_entry["used_functions_from_dependencies_hints"] = used_hints

    return json.dumps(processed_files_data, indent=2)
