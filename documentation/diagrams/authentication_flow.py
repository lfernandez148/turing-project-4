#!/usr/bin/env python3
"""
Generate Authentication Flow diagram for Campaign Assistant
Based on the Mermaid diagram in README_V2.md
"""

import graphviz
import os

def create_authentication_flow_diagram():
    """Create an authentication flow diagram showing the Firebase auth process."""
    
    # Create a new directed graph
    dot = graphviz.Digraph(
        'authentication_flow',
        comment='Campaign Assistant Authentication Flow',
        format='png'
    )
    
    # Set graph attributes for better layout
    dot.attr(rankdir='TB', size='12,10', dpi='300')
    dot.attr('node', shape='box', style='rounded,filled', fontname='Arial', fontsize='10')
    dot.attr('edge', fontname='Arial', fontsize='9')
    
    # Define color scheme
    colors = {
        'start': '#E8F5E8',
        'decision': '#FFEBEE',
        'process': '#E3F2FD',
        'action': '#FFF3E0',
        'success': '#E8F5E8',
        'error': '#FFCDD2'
    }
    
    # Add nodes
    dot.node('user_access', 'User Access', 
             fillcolor=colors['start'], 
             shape='ellipse',
             style='filled,bold')
    
    dot.node('authenticated', 'Authenticated?', 
             fillcolor=colors['decision'],
             shape='diamond')
    
    dot.node('main_app', 'Main Application', 
             fillcolor=colors['success'],
             shape='ellipse',
             style='filled,bold')
    
    dot.node('login_page', 'Login Page', 
             fillcolor=colors['process'])
    
    dot.node('choose_action', 'Choose Action', 
             fillcolor=colors['decision'],
             shape='diamond')
    
    dot.node('sign_in', 'Sign In\n\n• Email/Password\n• Form validation', 
             fillcolor=colors['action'])
    
    dot.node('sign_up', 'Sign Up\n\n• Create account\n• Email verification\n• Auto-login', 
             fillcolor=colors['action'])
    
    dot.node('reset_password', 'Reset Password\n\n• Email reset link\n• Firebase email\n• Return to login', 
             fillcolor=colors['action'])
    
    dot.node('firebase_auth', 'Firebase Auth\n\n• REST API calls\n• Token generation\n• Session management', 
             fillcolor=colors['process'])
    
    dot.node('auth_success', 'Success?', 
             fillcolor=colors['decision'],
             shape='diamond')
    
    dot.node('set_session', 'Set Session State\n\n• user_email\n• user_id\n• id_token\n• role (admin/user)\n• login_time', 
             fillcolor=colors['success'])
    
    dot.node('show_error', 'Show Error\n\n• Display error message\n• Return to form\n• Clear inputs', 
             fillcolor=colors['error'])
    
    # Add edges
    dot.edge('user_access', 'authenticated', 'Initial Request')
    
    dot.edge('authenticated', 'main_app', 'Yes\n(Valid Session)', color='green')
    dot.edge('authenticated', 'login_page', 'No\n(No Session)', color='red')
    
    dot.edge('login_page', 'choose_action', 'Display Options')
    
    dot.edge('choose_action', 'sign_in', 'Login')
    dot.edge('choose_action', 'sign_up', 'Register')
    dot.edge('choose_action', 'reset_password', 'Forgot Password')
    
    dot.edge('sign_in', 'firebase_auth', 'Submit Credentials')
    dot.edge('sign_up', 'firebase_auth', 'Create Account')
    dot.edge('reset_password', 'firebase_auth', 'Send Reset Email')
    
    dot.edge('firebase_auth', 'auth_success', 'Process Request')
    
    dot.edge('auth_success', 'set_session', 'Yes\n(Valid Response)', color='green')
    dot.edge('auth_success', 'show_error', 'No\n(Error Response)', color='red')
    
    dot.edge('set_session', 'main_app', 'Redirect to App')
    dot.edge('show_error', 'login_page', 'Return to Form')
    
    return dot

def main():
    """Generate the Authentication Flow diagram."""
    print("🎨 Generating Authentication Flow Diagram...")
    
    # Create the diagram
    dot = create_authentication_flow_diagram()
    
    # Set output directory
    output_dir = '/Users/lolo/shared/projects/turing/sprint-3/project-23/documentation/diagrams'
    output_file = os.path.join(output_dir, 'authentication_flow')
    
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
