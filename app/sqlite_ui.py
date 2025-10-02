import streamlit as st
from . import login
import sqlite3
import pandas as pd
from datetime import datetime
from databases.sqlite_config import SQLiteConfig

@st.cache_resource
def get_db_connection():
    """Get a connection to the SQLite database."""
    # Get the conversations database path
    db_path = SQLiteConfig.CONVERSATIONS_DB
    
    if not db_path.exists():
        st.error("❌ Database file not found!")
        st.info(f"Expected database at: {db_path}")
        return None
    
    st.success(f"✅ Using database: {db_path}")
    return sqlite3.connect(str(db_path), check_same_thread=False)

def format_timestamp(timestamp_str):
    """Format timestamp string to a more readable format."""
    try:
        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return timestamp_str


def app():
    """SQLite Database Management page."""
    st.title("SQLite Explorer")
    
    # Get current user from login module
    user_info = login.get_current_user()
    
    if not user_info:
        st.error("User information not available. Please login again.")
        if st.button("Go to Login"):
            login.logout()
        return

    try:
        conn = get_db_connection()
        if conn is None:
            st.stop()
            
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        excluded_tables = {'writes', 'sqlite_sequence', 'checkpoints'}
        tables = [
            row[0] for row in cursor.fetchall()
            if row[0] not in excluded_tables
        ]

        # Sidebar for table selection
        st.sidebar.markdown("### 📋 Select Table")
        selected_table = st.sidebar.selectbox("Choose a table", sorted(tables))

        if selected_table:
            st.markdown(f"### 📊 Table: {selected_table}")

            # Get column names
            cursor.execute(f"PRAGMA table_info({selected_table})")
            columns = [row[1] for row in cursor.fetchall()]

            # Query builder section
            st.markdown("### 🔍 Query Options")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Search in specific columns
                search_col = st.selectbox(
                    "Search in column",
                    ["All"] + columns
                )
                search_term = st.text_input("Search term")
            
            with col2:
                limit = st.number_input(
                    "Limit rows",
                    min_value=1,
                    value=100
                )

            # Build and execute query
            query = f"SELECT * FROM {selected_table}"
            params = []

            if search_term and search_col != "All":
                query += f" WHERE {search_col} LIKE ?"
                params.append(f"%{search_term}%")
            elif search_term:
                # Search in all string/text columns if "All" is selected
                search_conditions = []
                for col in columns:
                    search_conditions.append(f"{col} LIKE ?")
                    params.append(f"%{search_term}%")
                query += " WHERE " + " OR ".join(search_conditions)

            query += f" ORDER BY id DESC LIMIT {limit}"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Convert to DataFrame for better display
            df = pd.DataFrame(rows, columns=columns)

            # Format timestamp columns if they exist
            # Format timestamp columns
            timestamp_cols = [
                col for col in df.columns
                if "timestamp" in col.lower()
            ]
            for col in timestamp_cols:
                df[col] = df[col].apply(format_timestamp)

            # Display results
            if not df.empty:
                st.markdown(f"### 📋 Results ({len(df)} rows)")
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No data found matching your criteria.")

    except Exception as e:
        st.error(f"❌ Error accessing database: {str(e)}")
        st.info(
            "💡 Make sure the SQLite database exists and is accessible."
        )
