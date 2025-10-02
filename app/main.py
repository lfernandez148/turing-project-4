# Main - Streamlit App entry point

import streamlit as st
from streamlit_option_menu import option_menu
from . import home
from . import account
from . import login  # Import the login module
from . import chroma_ui  # Add ChromaDB UI import
from . import sqlite_ui  # Add SQLite UI import
from . import evaluation_ui  # Add Evaluation UI import


# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False


def run_authenticated_app():
    """Run the main application for authenticated users."""
    st.set_page_config(
        page_title="CPAssist",
    )
    
    # Get current user info
    user_info = login.get_current_user()
    
    with st.sidebar:
        # User info display
        st.markdown(f"User: {user_info['email']}")
        
        # Prepare menu options based on user role
        menu_options = ['Home', 'Account']
        menu_icons = ['house-fill', 'person-circle']
        
        # Add admin options
        if user_info['role'] == 'admin':
            menu_options.extend(['ChromaDB', 'SQLite', 'Evaluation'])
            menu_icons.extend(['database', 'card-list', 'graph-up'])
        
        # Always add Logout as the last option
        menu_options.append('Logout')
        menu_icons.append('door-open')
        
        # Main navigation
        app = option_menu(
            menu_title='CPAssist',
            options=menu_options,
            icons=menu_icons,
            menu_icon='',
            default_index=0,
            styles={
                "container": {
                    "padding": "5!important",
                    "background-color": "white"
                },
                "icon": {"color": "green", "font-size": "23px"},
                "nav-link": {
                    "color": "black",
                    "font-size": "20px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "#cccccce6"
                },
                "nav-link-selected": {"background-color": "#02ab21"},
            }
        )
    
    # Route to appropriate page
    if app == "Home":
        home.app()
    elif app == "Account":
        account.app()
    elif app == "ChromaDB" and user_info['role'] == 'admin':
        chroma_ui.app()
    elif app == "SQLite" and user_info['role'] == 'admin':
        sqlite_ui.app()
    elif app == "Evaluation" and user_info['role'] == 'admin':
        evaluation_ui.app()
    elif app == 'Logout':
        login.logout()

def run():
    """Main application entry point."""
    # Check authentication
    if not login.check_authentication():
        # Show login page
        login.login_page()
    else:
        # Show main application
        run_authenticated_app()


if __name__ == "__main__":
    run()
