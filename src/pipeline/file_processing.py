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

def extract_function_definitions_with_code(file_content, language):
    """
    Extract function names along with their complete code structure.
    Returns a list of dictionaries with 'name' and 'code' keys.
    """
    functions = []
    lines = file_content.splitlines()

    if language == "python":
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            if stripped.startswith("def ") and "(" in stripped and ":" in stripped:
                # Extract function name
                name_start = stripped.find("def ") + len("def ")
                name_end = stripped.find("(", name_start)
                func_name = stripped[name_start:name_end].strip()
                
                if func_name and " " not in func_name:
                    # Get indentation level
                    indent_level = len(line) - len(line.lstrip())
                    
                    # Collect function code
                    func_lines = [line]
                    i += 1
                    
                    # Continue collecting lines that are part of the function
                    while i < len(lines):
                        current_line = lines[i]
                        current_stripped = current_line.strip()
                        
                        # Stop if we hit a line with same or less indentation (unless it's empty or comment)
                        if current_stripped and not current_stripped.startswith('#'):
                            current_indent = len(current_line) - len(current_line.lstrip())
                            if current_indent <= indent_level:
                                break
                        
                        func_lines.append(current_line)
                        i += 1
                    
                    functions.append({
                        "name": func_name,
                        "code": "\n".join(func_lines)
                    })
                    continue
            i += 1

    elif language in ["javascript", "typescript", "javascript xml", "typescript xml"]:
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Patterns for different function declarations
            patterns = [
                (r'function\s+([a-zA-Z0-9_]+)\s*\(', 'function'),
                (r'const\s+([a-zA-Z0-9_]+)\s*=\s*function\s*\(', 'const_function'),
                (r'const\s+([a-zA-Z0-9_]+)\s*=\s*\(?.*?\)?\s*=>', 'arrow'),
                (r'let\s+([a-zA-Z0-9_]+)\s*=\s*function\s*\(', 'let_function'),
                (r'let\s+([a-zA-Z0-9_]+)\s*=\s*\(?.*?\)?\s*=>', 'let_arrow'),
                (r'export\s+function\s+([a-zA-Z0-9_]+)\s*\(', 'export_function'),
                (r'export\s+const\s+([a-zA-Z0-9_]+)\s*=\s*\(?.*?\)?\s*=>', 'export_arrow')
            ]
            
            for pattern, func_type in patterns:
                match = re.search(pattern, stripped)
                if match:
                    func_name = match.group(1)
                    func_lines = [line]
                    i += 1
                    
                    # Track braces to find function end
                    brace_count = stripped.count('{') - stripped.count('}')
                    
                    # For arrow functions, check if it's single line
                    if 'arrow' in func_type and '=>' in stripped:
                        if '{' not in stripped:
                            # Single line arrow function
                            functions.append({
                                "name": func_name,
                                "code": line
                            })
                            break
                    
                    # Multi-line function - collect until braces match
                    while i < len(lines) and brace_count > 0:
                        current_line = lines[i]
                        func_lines.append(current_line)
                        brace_count += current_line.count('{') - current_line.count('}')
                        i += 1
                    
                    if func_lines:
                        functions.append({
                            "name": func_name,
                            "code": "\n".join(func_lines)
                        })
                    break
            else:
                i += 1
                continue
            break

    # Remove duplicates based on function name
    seen = set()
    unique_functions = []
    for func in functions:
        if func["name"] not in seen:
            seen.add(func["name"])
            unique_functions.append(func)
    
    return unique_functions

def extract_function_definitions(file_content, language):
    """
    Legacy function that returns just function names for backward compatibility.
    """
    functions_with_code = extract_function_definitions_with_code(file_content, language)
    return [func["name"] for func in functions_with_code]

def find_external_imports(file_content, file_path, all_repo_files):
    external_deps = set()
    all_repo_files_set = set(all_repo_files)
    curr_dir = os.path.dirname(file_path)
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == ".py":
        for line in file_content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Handle: import x, y
            if stripped.startswith("import "):
                import_part = stripped[7:].strip()
                module_names = [m.strip() for m in import_part.split(",")]
                for module_name in module_names:
                    if "#" in module_name:
                        module_name = module_name.split("#")[0].strip()
                    if not module_name.startswith("."):
                        possible_path = os.path.join(curr_dir, *module_name.split(".")) + ".py"
                        normalized = os.path.normpath(possible_path)
                        if normalized not in all_repo_files_set:
                            external_deps.add(module_name)

            # Handle: from x import y
            elif stripped.startswith("from "):
                from_part = stripped[5:].strip()
                if "import" in from_part:
                    module_name = from_part.split(" import ")[0].strip()
                    if "#" in module_name:
                        module_name = module_name.split("#")[0].strip()
                    if not module_name.startswith("."):
                        possible_path = os.path.join(curr_dir, *module_name.split(".")) + ".py"
                        normalized = os.path.normpath(possible_path)
                        if normalized not in all_repo_files_set:
                            external_deps.add(module_name)

    elif file_extension in [".js", ".ts", ".jsx", ".tsx"]:
        for line in file_content.splitlines():
            stripped = line.strip()
            module_path = None
            if not stripped or stripped.startswith("//") or stripped.startswith("/*"):
                continue

            # Handle: import something from "lib"
            if "import" in stripped and "from" in stripped:
                from_idx = stripped.find("from")
                if from_idx != -1:
                    import_path_part = stripped[from_idx + 4:].strip()
                    if import_path_part.startswith(("'", '"')):
                        quote_char = import_path_part[0]
                        end_quote_idx = import_path_part.find(quote_char, 1)
                        if end_quote_idx != -1:
                            module_path = import_path_part[1:end_quote_idx]

            # Handle: import "lib"
            elif stripped.startswith("import "):
                import_path = stripped[7:].strip()
                if import_path.startswith(("'", '"')):
                    quote_char = import_path[0]
                    end_quote_idx = import_path.find(quote_char, 1)
                    if end_quote_idx != -1:
                        module_path = import_path[1:end_quote_idx]

            # Handle: const x = require("lib")
            elif "require(" in stripped:
                start_idx = stripped.find("require(") + len("require(")
                after = stripped[start_idx:].strip()
                if after.startswith(("'", '"')):
                    quote_char = after[0]
                    end_quote_idx = after.find(quote_char, 1)
                    if end_quote_idx != -1:
                        module_path = after[1:end_quote_idx]

            # Final check: skip relative paths
            if module_path and not module_path.startswith((".", "/", "../")):
                external_deps.add(module_path)

    return list(external_deps)

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
        
        # Extract functions with their code
        functions_with_code = extract_function_definitions_with_code(content, language)
        defined_functions = [func["name"] for func in functions_with_code]
        file_defined_functions_cache[abs_path] = defined_functions or []

        processed_files_data.append({
            "file_path": os.path.relpath(abs_path, repo_root_path),
            "metadata": metadata,
            "language": language,
            "functions": functions_with_code,  # Now includes both name and code
            "dependencies": [],
            "used_functions_from_dependencies_hints": [],
            "external_libraries": find_external_imports(content, file_path, all_repo_files)
        })

    for file_entry in processed_files_data:
        abs_file_path = os.path.abspath(os.path.join(repo_root_path, file_entry["file_path"]))
        content = file_content_cache.get(abs_file_path, "")

        # Ensure dependencies is always a list
        abs_dependencies = find_dependencies(content, abs_file_path, all_repo_files_set) or []

        file_entry["dependencies"] = [
            os.path.relpath(dep, repo_root_path) for dep in abs_dependencies
        ]

        used_hints = []
        for dep_path in abs_dependencies:
            for func_name in file_defined_functions_cache.get(dep_path, []):
                if func_name in content:
                    used_hints.append(f"{os.path.basename(dep_path)}:{func_name}")

        file_entry["used_functions_from_dependencies_hints"] = used_hints

    return json.dumps(processed_files_data, indent=2)