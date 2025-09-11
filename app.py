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
from run_pipeline import run_pipeline

st.title("GitHub Repo Preprocessing Pipeline")

url = st.text_input("Enter GitHub repository URL", placeholder="https://github.com/username/repo")

if st.button("Run Analysis"):
    if not url.strip():
        st.error("Please enter a valid GitHub repository URL.")
    else:
        # Override input() so pipeline uses Streamlit URL
        builtins.input = lambda prompt="": url

        with st.spinner("Running pipeline..."):
            buffer = io.StringIO()
            try:
                # Capture printed output from pipeline
                with contextlib.redirect_stdout(buffer):
                    run_pipeline()

                output = buffer.getvalue()

                # Extract JSON from output
                match = re.search(
                    r"--- Analysis Results \(JSON Output\) ---\n(.*?)\n---",
                    output,
                    re.S,
                )

                if match:
                    analysis_json_str = match.group(1).strip()
                    try:
                        analysis_data = json.loads(analysis_json_str)

                        # 1. Show JSON
                        st.subheader("📦 Raw JSON Output")
                        st.json(analysis_data)

                        # 2. Dependency Graph Visualization
                        st.subheader("🕸️ File-to-File Dependency Graph")

                        # Create network graph
                        G = nx.DiGraph()
                        node_info = {}

                        for file in analysis_data:
                            file_path = file.get("file_path", "")
                            deps = file.get("dependencies", [])
                            
                            # Add node info
                            node_info[file_path] = {
                                'lines_of_code': file.get('lines_of_code', 0),
                                'dependencies': len(deps),
                                'file_type': file_path.split('.')[-1] if '.' in file_path else 'unknown'
                            }
                            
                            # Add edges
                            for dep in deps:
                                G.add_edge(file_path, dep)

                        if G.number_of_nodes() > 0:
                            # Create tabs for different graph views
                            graph_tab1, graph_tab2, graph_tab3 = st.tabs(["Interactive Graph", "Static Graph", "Graph Metrics"])
                            
                            with graph_tab1:
                                st.write("**Interactive Dependency Network** - Hover over nodes for details")
                                
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
                                    
                                    # Color nodes by file type
                                    file_types = list(set(node_info[node]['file_type'] for node in G.nodes()))
                                    color_map = px.colors.qualitative.Set3[:len(file_types)]
                                    type_to_color = dict(zip(file_types, color_map))
                                    
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
                                        line=dict(width=1, color='rgba(100,100,100,0.5)'),
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
                                            line=dict(width=1, color='white'),
                                            opacity=0.8
                                        ),
                                        text=[node.split('/')[-1] for node in G.nodes()],  # Show just filename
                                        textposition="middle center",
                                        textfont=dict(size=8, color="white"),
                                        hovertext=hover_text,
                                        hoverinfo='text',
                                        name='Files'
                                    ))
                                    
                                    fig.update_layout(
                                        title=dict(
                                            text=f"Dependency Graph ({len(G.nodes())} files, {len(G.edges())} dependencies)",
                                            x=0.5,
                                            font=dict(size=16)
                                        ),
                                        showlegend=False,
                                        hovermode='closest',
                                        margin=dict(b=20,l=5,r=5,t=40),
                                        annotations=[ dict(
                                            text="Node size = Lines of Code | Color = File Type",
                                            showarrow=False,
                                            xref="paper", yref="paper",
                                            x=0.005, y=-0.002,
                                            xanchor='left', yanchor='bottom',
                                            font=dict(color="gray", size=12)
                                        )],
                                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                        height=600
                                    )
                                    
                                    st.plotly_chart(fig, use_container_width=True)
                                    
                                    # Add legend for file types
                                    if len(file_types) > 1:
                                        st.write("**File Type Legend:**")
                                        legend_cols = st.columns(min(5, len(file_types)))
                                        for i, (ftype, color) in enumerate(type_to_color.items()):
                                            with legend_cols[i % len(legend_cols)]:
                                                st.markdown(f'<span style="color: {color};">●</span> {ftype}', unsafe_allow_html=True)
                                else:
                                    st.info("No dependencies found to visualize.")
                            
                            with graph_tab2:
                                st.write("**Static Network Graph** - Traditional matplotlib visualization")
                                
                                if G.number_of_edges() > 0:
                                    fig, ax = plt.subplots(figsize=(12, 8))
                                    
                                    # Choose layout based on graph size
                                    if len(G.nodes()) < 15:
                                        pos = nx.spring_layout(G, k=2, iterations=50)
                                    else:
                                        pos = nx.kamada_kawai_layout(G)
                                    
                                    # Draw edges first
                                    nx.draw_networkx_edges(G, pos, 
                                                         edge_color='lightgray',
                                                         arrows=True,
                                                         arrowsize=15,
                                                         arrowstyle='->',
                                                         alpha=0.6,
                                                         width=1.5)
                                    
                                    # Color nodes by file type
                                    file_types = list(set(node_info[node]['file_type'] for node in G.nodes()))
                                    colors = plt.cm.Set3(np.linspace(0, 1, len(file_types)))
                                    type_to_color = dict(zip(file_types, colors))
                                    node_colors = [type_to_color[node_info[node]['file_type']] for node in G.nodes()]
                                    
                                    # Size nodes by lines of code
                                    node_sizes = [max(300, min(2000, node_info[node]['lines_of_code'] * 5)) for node in G.nodes()]
                                    
                                    # Draw nodes
                                    nx.draw_networkx_nodes(G, pos,
                                                         node_color=node_colors,
                                                         node_size=node_sizes,
                                                         alpha=0.8,
                                                         edgecolors='black',
                                                         linewidths=1)
                                    
                                    # Add labels (just filenames)
                                    labels = {node: node.split('/')[-1] for node in G.nodes()}
                                    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold')
                                    
                                    plt.title(f"File Dependency Network\n{len(G.nodes())} files, {len(G.edges())} dependencies", 
                                             fontsize=14, fontweight='bold')
                                    plt.axis('off')
                                    plt.tight_layout()
                                    
                                    st.pyplot(fig)
                                    
                                    # Add file type legend
                                    if len(file_types) > 1:
                                        st.write("**Legend:**")
                                        legend_text = " | ".join([f"**{ftype}**" for ftype in file_types])
                                        st.markdown(legend_text)
                                else:
                                    st.info("No dependencies found to visualize.")
                            
                            with graph_tab3:
                                st.write("**Graph Analysis Metrics**")
                                
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
                                            st.write(f"**{i}. {file.split('/')[-1]}** - "
                                                   f"In: {in_deg}, Out: {out_deg}, "
                                                   f"Centrality: {centrality:.3f}")
                                else:
                                    st.info("No graph data available for analysis.")

                    except json.JSONDecodeError:
                        st.error("Failed to decode JSON from pipeline output. Check the `run_pipeline` script for correct output format.")
                        st.text_area("Pipeline Output", output, height=300)

                else:
                    st.error("JSON output marker not found in the pipeline output.")
                    st.text_area("Pipeline Output", output, height=300)

            except Exception as e:
                st.error(f"An error occurred during pipeline execution: {e}")
                st.text_area("Pipeline Output", buffer.getvalue(), height=300)
else:
    st.info("Enter a GitHub repository URL and click 'Run Analysis' to begin.")