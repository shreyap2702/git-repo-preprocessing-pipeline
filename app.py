import streamlit as st
import io
import contextlib
import builtins
import re
import json
import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import os
from datetime import datetime
from run_pipeline import run_pipeline

st.set_page_config(page_title="GitHub Repository Analyzer", page_icon=None, layout="wide")

# Improved CSS with rounded corners and better UX
st.markdown("""
    <style>
    /* Import better font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    /* Main container styling */
    .main {
        background-color: #fafafa;
        font-family: 'Inter', sans-serif;
    }
    
    /* Header styling */
    .main-header {
        background: #ffffff;
        padding: 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    
    .main-header h1 {
        color: #1a1a1a;
        font-weight: 600;
        margin-bottom: 0.5rem;
        font-size: 2.2rem;
        letter-spacing: -0.02em;
    }
    
    .main-header p {
        color: #666666;
        font-size: 1.1rem;
        margin: 0;
        font-weight: 400;
    }
    
    /* Card styling */
    .metric-card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
    }
    
    /* Button styling */
    .stButton>button {
        background: #ffffff;
        color: #1a1a1a;
        border: 1.5px solid #d0d0d0;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 500;
        font-family: 'Inter', sans-serif;
        transition: all 0.2s ease;
        letter-spacing: 0.01em;
    }
    
    .stButton>button:hover {
        background: #f5f5f5;
        border-color: #a0a0a0;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
        padding: 0.5rem 0;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        border: 1.5px solid #e0e0e0;
        font-family: 'Inter', sans-serif;
        transition: all 0.2s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #f5f5f5;
        border: 1.5px solid #999999;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #ffffff;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        font-weight: 500;
        padding: 1rem;
        font-family: 'Inter', sans-serif;
        transition: all 0.2s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: #f9f9f9;
        border-color: #d0d0d0;
    }
    
    /* Input styling */
    .stTextInput>div>div>input {
        border-radius: 10px;
        border: 1.5px solid #d0d0d0;
        padding: 0.75rem 1rem;
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
        transition: all 0.2s ease;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #999999;
        box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.05);
    }
    
    /* Selectbox styling */
    .stSelectbox>div>div {
        border-radius: 10px;
        border: 1.5px solid #d0d0d0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Dataframe styling */
    .dataframe {
        border-radius: 12px;
        overflow: hidden;
        font-family: 'Inter', sans-serif;
    }
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 600;
        color: #1a1a1a;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        font-weight: 500;
        color: #666666;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Code block styling */
    .stCodeBlock {
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }
    
    /* Info/Success/Error boxes */
    .stAlert {
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }
    
    [data-testid="stSidebar"] h2 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: #1a1a1a;
    }
    
    /* Checkbox styling */
    .stCheckbox {
        font-family: 'Inter', sans-serif;
    }
    
    /* Download button */
    .stDownloadButton>button {
        background: #ffffff;
        color: #1a1a1a;
        border: 1.5px solid #d0d0d0;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 500;
        font-family: 'Inter', sans-serif;
        transition: all 0.2s ease;
    }
    
    .stDownloadButton>button:hover {
        background: #f5f5f5;
        border-color: #a0a0a0;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: #d0d0d0 !important;
        border-right-color: #666666 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="main-header">
        <h1>GitHub Repository Analyzer</h1>
        <p>Advanced code analysis and dependency visualization tool</p>
    </div>
""", unsafe_allow_html=True)

# Initialize session state to store analysis results
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = None
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    save_repo = st.checkbox("Save repository locally", value=False)
    show_full_json = st.checkbox("Show full JSON output", value=False)
    st.markdown("---")
    st.subheader("About")
    st.markdown("""
    This tool analyzes GitHub repositories to extract:
    - File structure and metadata
    - Function definitions with code
    - Dependency relationships
    - External library usage
    """)
    st.markdown("---")
    
    # Clear analysis button
    if st.session_state.analysis_complete:
        if st.button("Clear Analysis", use_container_width=True):
            st.session_state.analysis_data = None
            st.session_state.analysis_complete = False
            st.rerun()
    
    st.caption("Built with Streamlit & NetworkX")

url = st.text_input("GitHub Repository URL", placeholder="https://github.com/username/repo")

if st.button("Run Analysis", type="primary", use_container_width=True):
    if not url.strip():
        st.error("Please enter a valid GitHub repository URL.")
    else:
        # Override input() so pipeline uses Streamlit values
        input_responses = [url, "n" if not save_repo else "y", "n"]
        input_iterator = iter(input_responses)
        builtins.input = lambda prompt="": next(input_iterator, "")

        with st.spinner("Cloning repository and analyzing..."):
            try:
                # Check for analysis results directory
                output_dir = "analysis_results"
                
                # Run the pipeline (it now saves to JSON file)
                run_pipeline()
                
                # Find the most recent analysis file
                if os.path.exists(output_dir):
                    json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
                    if json_files:
                        # Get the most recent file
                        latest_file = max([os.path.join(output_dir, f) for f in json_files], 
                                        key=os.path.getctime)
                        
                        with open(latest_file, 'r', encoding='utf-8') as f:
                            analysis_data = json.load(f)
                        
                        # Store in session state
                        st.session_state.analysis_data = analysis_data
                        st.session_state.analysis_complete = True
                        
                        st.success(f"Analysis complete! Found {len(analysis_data)} files.")
                    else:
                        st.error("No analysis files found. The pipeline may not have completed successfully.")
                else:
                    st.error("Analysis results directory not found.")

            except Exception as e:
                st.error(f"An error occurred during pipeline execution: {e}")
                import traceback
                with st.expander("View Error Details"):
                    st.code(traceback.format_exc())

# Display analysis results if available
if st.session_state.analysis_complete and st.session_state.analysis_data:
    analysis_data = st.session_state.analysis_data
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "Overview", 
        "Function Explorer", 
        "Dependency Graph",
        "Raw Data"
    ])
    
    # TAB 1: Overview
    with tab1:
        st.subheader("Repository Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        total_functions = sum(len(file.get('functions', [])) for file in analysis_data)
        total_deps = sum(len(file.get('dependencies', [])) for file in analysis_data)
        
        with col1:
            st.metric("Total Files", len(analysis_data))
        with col2:
            st.metric("Total Functions", total_functions)
        with col3:
            st.metric("Dependencies", total_deps)
        with col4:
            all_external = set()
            for file in analysis_data:
                all_external.update(file.get('external_libraries', []))
            st.metric("External Libraries", len(all_external))
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Language distribution
        st.subheader("Programming Languages")
        language_counts = {}
        for file in analysis_data:
            lang = file.get('language', 'Unknown')
            language_counts[lang] = language_counts.get(lang, 0) + 1
        
        # Grayscale color palette
        gray_colors = ['#333333', '#666666', '#999999', '#cccccc', '#e0e0e0']
        
        fig_lang = go.Figure(data=[go.Pie(
            labels=list(language_counts.keys()),
            values=list(language_counts.values()),
            hole=.3,
            marker=dict(colors=gray_colors, line=dict(color='#000000', width=1))
        )])
        fig_lang.update_layout(
            title="Files by Language", 
            height=400,
            showlegend=True,
            paper_bgcolor='#ffffff',
            plot_bgcolor='#ffffff',
            font=dict(color='#000000', family='Inter, sans-serif')
        )
        st.plotly_chart(fig_lang, use_container_width=True)
        
        # External libraries list
        if all_external:
            st.subheader("External Libraries Used")
            cols = st.columns(3)
            sorted_libs = sorted(list(all_external))
            for idx, lib in enumerate(sorted_libs):
                with cols[idx % 3]:
                    st.code(lib, language=None)
        
        # File statistics
        st.subheader("File Statistics")
        file_stats = []
        for file in analysis_data:
            file_stats.append({
                'File': file.get('file_path', 'Unknown'),
                'Language': file.get('language', 'Unknown'),
                'Functions': len(file.get('functions', [])),
                'Dependencies': len(file.get('dependencies', [])),
                'External Libs': len(file.get('external_libraries', []))
            })
        
        st.dataframe(file_stats, use_container_width=True, height=400)
    
    # TAB 2: Function Explorer
    with tab2:
        st.subheader("Function Explorer")
        st.markdown("Browse all functions and view their source code")
        
        # File selector
        file_paths = [file.get('file_path', 'Unknown') for file in analysis_data]
        selected_file = st.selectbox("Select a file", file_paths, key="file_selector")
        
        if selected_file:
            file_data = next((f for f in analysis_data if f.get('file_path') == selected_file), None)
            
            if file_data:
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown(f"**File:** `{os.path.basename(selected_file)}`")
                    st.markdown(f"**Language:** `{file_data.get('language', 'Unknown')}`")
                    st.markdown(f"**Functions:** `{len(file_data.get('functions', []))}`")
                
                with col2:
                    if file_data.get('dependencies'):
                        st.markdown("**Dependencies:**")
                        for dep in file_data.get('dependencies', [])[:3]:
                            st.code(dep, language=None)
                        if len(file_data.get('dependencies', [])) > 3:
                            st.caption(f"... and {len(file_data.get('dependencies', [])) - 3} more")
                
                st.markdown("---")
                
                # Display functions
                functions = file_data.get('functions', [])
                
                if functions:
                    st.subheader(f"Functions ({len(functions)})")
                    
                    # Search/filter
                    search_term = st.text_input("Search functions", "", key="func_search")
                    
                    filtered_functions = [
                        f for f in functions 
                        if search_term.lower() in f.get('name', '').lower()
                    ]
                    
                    if filtered_functions:
                        # Create expandable sections for each function
                        for func in filtered_functions:
                            func_name = func.get('name', 'Unknown')
                            func_code = func.get('code', 'No code available')
                            
                            with st.expander(f"Function: {func_name}", expanded=False):
                                # Detect language for syntax highlighting
                                lang = file_data.get('language', 'python')
                                if lang == 'javascript xml':
                                    lang = 'jsx'
                                elif lang == 'typescript xml':
                                    lang = 'tsx'
                                
                                st.code(func_code, language=lang)
                                
                                st.caption(f"Lines of code: {len(func_code.splitlines())}")
                    else:
                        st.info("No functions match your search.")
                else:
                    st.info("No functions found in this file.")
    
    # TAB 3: Dependency Graph
    with tab3:
        st.subheader("Dependency Graph Visualization")
        
        # Create network graph
        G = nx.DiGraph()
        node_info = {}

        for file in analysis_data:
            file_path = file.get("file_path", "")
            deps = file.get("dependencies", [])
            
            # Calculate lines of code from functions
            total_lines = sum(len(f.get('code', '').splitlines()) for f in file.get('functions', []))
            
            # Add node info
            node_info[file_path] = {
                'lines_of_code': total_lines,
                'dependencies': len(deps),
                'file_type': file_path.split('.')[-1] if '.' in file_path else 'unknown'
            }
            
            # Add edges
            for dep in deps:
                G.add_edge(file_path, dep)

        if G.number_of_nodes() > 0:
            # Create tabs for different graph views
            graph_tab1, graph_tab2, graph_tab3 = st.tabs([
                "Interactive Graph", 
                "Static Graph", 
                "Graph Metrics"
            ])
            
            with graph_tab1:
                st.markdown("**Interactive Dependency Network** - Hover over nodes for details")
                
                # Create interactive plotly graph
                if G.number_of_edges() > 0:
                    # Use different layout algorithms based on graph size
                    if len(G.nodes()) < 20:
                        pos = nx.spring_layout(G, k=3, iterations=50)
                    elif len(G.nodes()) < 50:
                        pos = nx.kamada_kawai_layout(G)
                    else:
                        pos = nx.spring_layout(G, k=1, iterations=20)
                    
                    # Extract positions
                    node_x = [pos[node][0] for node in G.nodes()]
                    node_y = [pos[node][1] for node in G.nodes()]
                    
                    # Create edge traces
                    edge_x = []
                    edge_y = []
                    for edge in G.edges():
                        x0, y0 = pos[edge[0]]
                        x1, y1 = pos[edge[1]]
                        edge_x.extend([x0, x1, None])
                        edge_y.extend([y0, y1, None])
                    
                    # Grayscale colors for nodes
                    file_types = list(set(node_info[node]['file_type'] for node in G.nodes()))
                    gray_shades = ['#1a1a1a', '#404040', '#666666', '#8c8c8c', '#b3b3b3', '#d9d9d9']
                    type_to_color = dict(zip(file_types, gray_shades[:len(file_types)]))
                    
                    node_colors = [type_to_color[node_info[node]['file_type']] for node in G.nodes()]
                    node_sizes = [max(10, min(50, node_info[node]['lines_of_code'] / 10)) for node in G.nodes()]
                    
                    # Create hover text
                    hover_text = []
                    for node in G.nodes():
                        info = node_info[node]
                        hover_text.append(
                            f"<b>{node}</b><br>"
                            f"File Type: {info['file_type']}<br>"
                            f"Lines of Code: {info['lines_of_code']}<br>"
                            f"Dependencies: {info['dependencies']}<br>"
                            f"In-degree: {G.in_degree(node)}<br>"
                            f"Out-degree: {G.out_degree(node)}"
                        )
                    
                    # Create the plot
                    fig = go.Figure()
                    
                    # Add edges
                    fig.add_trace(go.Scatter(
                        x=edge_x, y=edge_y,
                        line=dict(width=1, color='#999999'),
                        hoverinfo='none',
                        mode='lines',
                        name='Dependencies'
                    ))
                    
                    # Add nodes
                    fig.add_trace(go.Scatter(
                        x=node_x, y=node_y,
                        mode='markers+text',
                        marker=dict(
                            size=node_sizes,
                            color=node_colors,
                            line=dict(width=1, color='#000000'),
                            opacity=0.9
                        ),
                        text=[node.split('/')[-1] for node in G.nodes()],
                        textposition="middle center",
                        textfont=dict(size=8, color="white", family="Inter, sans-serif"),
                        hovertext=hover_text,
                        hoverinfo='text',
                        name='Files'
                    ))
                    
                    fig.update_layout(
                        title=dict(
                            text=f"Dependency Graph - {len(G.nodes())} files, {len(G.edges())} dependencies",
                            x=0.5,
                            font=dict(size=16, family="Inter, sans-serif", color='#000000')
                        ),
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        annotations=[dict(
                            text="Node size represents lines of code | Color represents file type",
                            showarrow=False,
                            xref="paper", yref="paper",
                            x=0.005, y=-0.002,
                            xanchor='left', yanchor='bottom',
                            font=dict(color="#666666", size=11, family="Inter, sans-serif")
                        )],
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        paper_bgcolor='#ffffff',
                        plot_bgcolor='#ffffff',
                        height=600
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Add legend for file types
                    if len(file_types) > 1:
                        st.markdown("**File Type Legend:**")
                        legend_cols = st.columns(min(5, len(file_types)))
                        for i, (ftype, color) in enumerate(type_to_color.items()):
                            with legend_cols[i % len(legend_cols)]:
                                st.markdown(f'<span style="display:inline-block; width:12px; height:12px; background-color:{color}; border:1px solid #000000; margin-right:6px; border-radius:3px;"></span>{ftype}', unsafe_allow_html=True)
                else:
                    st.info("No dependencies found to visualize.")
            
            with graph_tab2:
                st.markdown("**Static Network Graph** - Traditional matplotlib visualization")
                
                if G.number_of_edges() > 0:
                    fig_static, ax = plt.subplots(figsize=(12, 8), facecolor='white')
                    
                    # Choose layout based on graph size
                    if len(G.nodes()) < 15:
                        pos = nx.spring_layout(G, k=2, iterations=50)
                    else:
                        pos = nx.kamada_kawai_layout(G)
                    
                    # Draw edges first
                    nx.draw_networkx_edges(G, pos, 
                                         edge_color='#666666',
                                         arrows=True,
                                         arrowsize=15,
                                         arrowstyle='->',
                                         alpha=0.5,
                                         width=1.5)
                    
                    # Grayscale colors for nodes
                    file_types = list(set(node_info[node]['file_type'] for node in G.nodes()))
                    gray_values = np.linspace(0.2, 0.8, len(file_types))
                    type_to_color_static = dict(zip(file_types, gray_values))
                    node_colors = [type_to_color_static[node_info[node]['file_type']] for node in G.nodes()]
                    
                    # Size nodes by lines of code
                    node_sizes = [max(300, min(2000, node_info[node]['lines_of_code'] * 5)) for node in G.nodes()]
                    
                    # Draw nodes
                    nx.draw_networkx_nodes(G, pos,
                                         node_color=node_colors,
                                         node_size=node_sizes,
                                         alpha=0.85,
                                         edgecolors='#000000',
                                         linewidths=1.5,
                                         cmap='gray')
                    
                    # Add labels (just filenames)
                    labels = {node: node.split('/')[-1] for node in G.nodes()}
                    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='normal', font_family='sans-serif')
                    
                    plt.title(f"File Dependency Network\n{len(G.nodes())} files, {len(G.edges())} dependencies", 
                             fontsize=14, fontweight='normal', pad=20)
                    plt.axis('off')
                    plt.tight_layout()
                    
                    st.pyplot(fig_static)
                    
                    # Add file type legend
                    if len(file_types) > 1:
                        st.markdown("**Legend:**")
                        legend_text = " | ".join([f"{ftype}" for ftype in file_types])
                        st.markdown(legend_text)
                else:
                    st.info("No dependencies found to visualize.")
            
            with graph_tab3:
                st.markdown("**Graph Analysis Metrics**")
                
                if G.number_of_nodes() > 0:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Nodes (Files)", len(G.nodes()))
                        st.metric("Edges (Dependencies)", len(G.edges()))
                        st.metric("Density", f"{nx.density(G):.3f}")
                    
                    with col2:
                        if len(G.edges()) > 0:
                            st.metric("Avg In-degree", f"{sum(d for n, d in G.in_degree()) / len(G.nodes()):.2f}")
                            st.metric("Avg Out-degree", f"{sum(d for n, d in G.out_degree()) / len(G.nodes()):.2f}")
                        else:
                            st.metric("Avg In-degree", "0")
                            st.metric("Avg Out-degree", "0")
                    
                    with col3:
                        try:
                            if nx.is_weakly_connected(G):
                                st.metric("Connected Components", "1 (fully connected)")
                            else:
                                components = nx.number_weakly_connected_components(G)
                                st.metric("Weakly Connected Components", components)
                        except:
                            st.metric("Connected Components", "N/A")
                        
                        # Check for cycles
                        try:
                            cycles = list(nx.simple_cycles(G))
                            st.metric("Circular Dependencies", len(cycles))
                        except:
                            st.metric("Circular Dependencies", "N/A")
                    
                    # Most connected files
                    if len(G.edges()) > 0:
                        st.subheader("Most Connected Files")
                        
                        degree_centrality = nx.degree_centrality(G)
                        top_files = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
                        
                        for i, (file, centrality) in enumerate(top_files, 1):
                            in_deg = G.in_degree(file)
                            out_deg = G.out_degree(file)
                            st.markdown(f"**{i}. {file.split('/')[-1]}** - "
                                   f"In: {in_deg}, Out: {out_deg}, "
                                   f"Centrality: {centrality:.3f}")
                else:
                    st.info("No graph data available for analysis.")
        else:
            st.info("No files found in the analysis to create a dependency graph.")
    
    # TAB 4: Raw Data
    with tab4:
        st.subheader("Raw JSON Data")
        
        if show_full_json:
            st.json(analysis_data)
        else:
            st.info("Full JSON output is hidden. Enable it in the sidebar to view.")
        
        # Download button
        st.download_button(
            label="Download Analysis JSON",
            data=json.dumps(analysis_data, indent=2),
            file_name=f"repo_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

elif not st.session_state.analysis_complete:
    st.info("Enter a GitHub repository URL and click 'Run Analysis' to begin.")