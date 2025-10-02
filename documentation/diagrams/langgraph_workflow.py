#!/usr/bin/env python3
"""
Generate LangGraph workflow diagram for Campaign Assistant
Based on the actual workflow structure from agents/graph/viz_graph.ipynb
"""

import graphviz
import os

def create_langgraph_workflow_diagram():
    """Create a detailed workflow diagram showing the LangGraph structure."""
    
    # Create a new directed graph
    dot = graphviz.Digraph(
        'langgraph_workflow',
        comment='Campaign Assistant LangGraph Workflow',
        format='png'
    )
    
    # Set graph attributes for better layout
    dot.attr(rankdir='TB', size='12,10', dpi='300')
    dot.attr('node', shape='box', style='rounded,filled', fontname='Arial', fontsize='10')
    dot.attr('edge', fontname='Arial', fontsize='9')
    
    # Define color scheme
    colors = {
        'start_end': '#E8F5E8',
        'analysis': '#E3F2FD', 
        'data': '#FFF3E0',
        'response': '#F3E5F5',
        'conditional': '#FFEBEE'
    }
    
    # Add START node
    dot.node('START', 'START', 
             fillcolor=colors['start_end'], 
             shape='ellipse',
             style='filled,bold')
    
    # Add main workflow nodes
    dot.node('analyze_query', 
             'Query Analyzer\n\n• Understand user intent\n• Extract entities\n• Determine data needs\n• Set query type',
             fillcolor=colors['analysis'])
    
    dot.node('should_retrieve', 
             'Conditional Logic\n\nneeds_data?\n(Decision Point)',
             fillcolor=colors['conditional'],
             shape='diamond')
    
    dot.node('retrieve_data', 
             'Data Retriever\n\n• Fetch campaign data\n• Search documents\n• Aggregate metrics\n• Format results',
             fillcolor=colors['data'])
    
    dot.node('generate_response', 
             'Response Generator\n\n• Create formatted response\n• Generate insights\n• Suggest visualizations\n• Add recommendations',
             fillcolor=colors['response'])
    
    # Add END node
    dot.node('END', 'END', 
             fillcolor=colors['start_end'], 
             shape='ellipse',
             style='filled,bold')
    
    # Add workflow edges
    dot.edge('START', 'analyze_query', 'Entry Point')
    dot.edge('analyze_query', 'should_retrieve', 'Analyze Complete')
    
    # Conditional edges
    dot.edge('should_retrieve', 'retrieve_data', 
             'needs_data = True\n(Performance, Analysis, Comparison)', 
             color='green')
    dot.edge('should_retrieve', 'generate_response', 
             'needs_data = False\n(General queries)', 
             color='blue')
    
    # Continuation edge
    dot.edge('retrieve_data', 'generate_response', 'Data Retrieved')
    dot.edge('generate_response', 'END', 'Response Complete')
    
    return dot

def main():
    """Generate the LangGraph workflow diagram."""
    print("🎨 Generating LangGraph Workflow Diagram...")
    
    # Create the diagram
    dot = create_langgraph_workflow_diagram()
    
    # Set output directory
    output_dir = '/Users/lolo/shared/projects/turing/sprint-3/project-23/documentation/diagrams'
    output_file = os.path.join(output_dir, 'langgraph_workflow')
    
    # Render the diagram
    try:
        dot.render(output_file, cleanup=True)
        print(f"✅ Diagram saved to: {output_file}.png")
        
        # Also save the source code
        with open(f"{output_file}.gv", 'w') as f:
            f.write(dot.source)
        print(f"✅ Source code saved to: {output_file}.gv")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating diagram: {e}")
        return False

if __name__ == "__main__":
    main()
