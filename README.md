# Git Repo Preprocessing Pipeline

This tool automates the process of cloning GitHub repositories and performing structural analysis to extract semantic data for code visualization and exploration.

## Pipeline Workflow

1.  **Ingestion**: Clones the target GitHub repository into a temporary or local workspace.
2.  **Structural Extraction**: Programmatically traverses the file tree to identify and extract:
    *   **Functional Units**: Function definitions along with their complete implementation code.
    *   **Dependency Mapping**: Internal import relationships and file-to-file connectivity.
    *   **External Requirements**: Identification of third-party libraries and modules.
    *   **File Metadata**: Language detection, file sizes, and path indexing.
3.  **Serialization**: Generates a structured JSON blueprint of the repository's architecture.
4.  **Visualization**: Serves the analyzed data through a Streamlit dashboard featuring interactive dependency networks and functional explorers.

## Technical Specifications

*   **Language Support**: Full support for Python (.py) and JavaScript/TypeScript ecosystems (.js, .ts, .jsx, .tsx).
*   **Extraction Engine**: Uses pattern-based structural analysis to resolve module paths and map functional scopes.
*   **Resolution Logic**: Supports Python (absolute/relative imports) and standard Node.js module resolution.
*   **Stack**: Python 3.x, Streamlit, NetworkX (Graph Theory), Plotly (Interactions), GitPython.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface
To run the analysis pipeline directly:
```bash
python run_pipeline.py
```

### Visualization Dashboard
To view the results in an interactive interface:
```bash
streamlit run app.py
```
