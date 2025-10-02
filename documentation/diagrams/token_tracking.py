#!/usr/bin/env python3
"""
Generate Token Tracking Architecture diagram for Campaign Assistant
Based on the Mermaid diagram in README_V2.md
"""

import graphviz
import os

def create_token_tracking_diagram():
    """Create a token tracking architecture diagram showing the monitoring system."""
    
    # Create a new directed graph
    dot = graphviz.Digraph(
        'token_tracking',
        comment='Campaign Assistant Token Tracking Architecture',
        format='png'
    )
    
    # Set graph attributes for better layout
    dot.attr(rankdir='TB', size='12,10', dpi='300')
    dot.attr('node', shape='box', style='rounded,filled', fontname='Arial', fontsize='10')
    dot.attr('edge', fontname='Arial', fontsize='9')
    
    # Define color scheme
    colors = {
        'input': '#E8F5E8',
        'agent': '#E3F2FD',
        'llm': '#FFF3E0',
        'tracking': '#F3E5F5',
        'storage': '#E0F2F1',
        'analytics': '#FFEBEE',
        'output': '#E8F5E8'
    }
    
    # Add nodes
    dot.node('user_query', 'User Query', 
             fillcolor=colors['input'], 
             shape='ellipse',
             style='filled,bold')
    
    dot.node('langgraph_agent', 'LangGraph Agent\n\n• Query processing\n• Tool orchestration\n• Workflow management', 
             fillcolor=colors['agent'])
    
    dot.node('llm_processing', 'LLM Processing\n\n• OpenAI/LM Studio\n• Token consumption\n• Response generation\n• Usage metadata', 
             fillcolor=colors['llm'])
    
    dot.node('token_calculation', 'Token Calculation\n\n• Input token count\n• Output token count\n• Usage metadata\n• Cost calculation', 
             fillcolor=colors['tracking'])
    
    dot.node('token_tracker_db', 'TokenTracker Database\n\n• conversations.db\n• token_usage table\n• user_id tracking\n• thread_id isolation', 
             fillcolor=colors['storage'])
    
    dot.node('usage_analytics', 'Usage Analytics\n\n• Total token count\n• Cost analysis\n• Usage patterns\n• Performance metrics', 
             fillcolor=colors['analytics'])
    
    dot.node('user_dashboard', 'User Dashboard\n\n• Account page display\n• Real-time statistics\n• Historical data\n• Cost monitoring', 
             fillcolor=colors['output'])
    
    dot.node('response_generation', 'Response Generation\n\n• Formatted response\n• Context integration\n• Source attribution', 
             fillcolor=colors['agent'])
    
    dot.node('save_chat_tokens', 'Save Chat + Tokens\n\n• Store conversation\n• Record token usage\n• Update statistics\n• Maintain history', 
             fillcolor=colors['storage'])
    
    dot.node('cost_monitoring', 'Cost Monitoring\n\n• Real-time costs\n• Budget tracking\n• Usage alerts\n• Optimization insights', 
             fillcolor=colors['analytics'])
    
    dot.node('usage_limits', 'Usage Limits\n\n• Rate limiting\n• Budget controls\n• Access management\n• Quota enforcement', 
             fillcolor=colors['analytics'])
    
    # Add edges
    dot.edge('user_query', 'langgraph_agent', 'Process Query')
    
    dot.edge('langgraph_agent', 'llm_processing', 'LLM Request')
    
    dot.edge('llm_processing', 'token_calculation', 'Usage Metadata')
    
    dot.edge('token_calculation', 'token_tracker_db', 'Store Tokens')
    dot.edge('token_calculation', 'response_generation', 'Continue Flow')
    
    dot.edge('token_tracker_db', 'usage_analytics', 'Aggregate Data')
    
    dot.edge('usage_analytics', 'user_dashboard', 'Display Stats')
    
    dot.edge('response_generation', 'save_chat_tokens', 'Save Interaction')
    
    dot.edge('save_chat_tokens', 'token_tracker_db', 'Update Database')
    
    dot.edge('token_tracker_db', 'cost_monitoring', 'Cost Data')
    dot.edge('token_tracker_db', 'usage_limits', 'Usage Data')
    
    return dot

def main():
    """Generate the Token Tracking Architecture diagram."""
    print("🎨 Generating Token Tracking Architecture Diagram...")
    
    # Create the diagram
    dot = create_token_tracking_diagram()
    
    # Set output directory
    output_dir = '/Users/lolo/shared/projects/turing/sprint-3/project-23/documentation/diagrams'
    output_file = os.path.join(output_dir, 'token_tracking')
    
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
