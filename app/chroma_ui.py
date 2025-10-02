import streamlit as st
from . import login
import os
from loguru import logger
from databases.chroma_config import get_chroma_client

# Configure logging
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logs.config import LogConfig, setup_logger  # noqa: E402

# Set up logging to both file and console
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    format=LogConfig.STANDARD_FORMAT,
    level="INFO"
)
logger.add(
    LogConfig.get_chroma_debug_log(),
    format=LogConfig.STANDARD_FORMAT,
    level="INFO"
)


@st.cache_resource
def get_client():
    """Initialize connection to ChromaDB."""
    return get_chroma_client()


def app():
    """ChromaDB management page."""
    st.title("ChromaDB Explorer")
    
    # Get current user from login module
    user_info = login.get_current_user()
    
    if not user_info:
        st.error("User information not available. Please login again.")
        if st.button("Go to Login"):
            login.logout()
        return

    try:
        client = get_client()
        collections = client.list_collections()

        # Collections Overview Section
        st.markdown("### 📚 Collections Overview")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"**Total Collections:** {len(collections)}")
        
        with col2:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()

        # Collections List Section
        st.markdown("### 📋 Collections List")
        if not collections:
            st.info("No collections found in the database")
        else:
            for collection in collections:
                with st.expander(f"📁 Collection: {collection.name}"):
                    try:
                        # Collection Info
                        count = collection.count()
                        st.info(f"**Documents Count:** {count}")
                        
                        # Sample Documents
                        if count > 0:
                            st.markdown("#### 📄 Sample Documents")
                            # Show first 5 documents
                            result = collection.peek(5)
                            if 'documents' in result:
                                docs = result['documents']
                                metas = result['metadatas']
                                docs_with_idx = enumerate(zip(docs, metas))
                                for idx, (doc, meta) in docs_with_idx:
                                    with st.expander(f"Document {idx + 1}"):
                                        st.write("**Content:**")
                                        doc_preview = doc[:500]
                                        if len(doc) > 500:
                                            doc_preview += "..."
                                        st.text(doc_preview)
                                        st.write("**Metadata:**")
                                        st.json(meta)
                            
                    except Exception as e:
                        st.error(
                            f"Error accessing collection "
                            f"{collection.name}: {str(e)}"
                        )

    except Exception as e:
        st.error(f"❌ Error connecting to ChromaDB: {str(e)}")
        st.info(
            "💡 Make sure the ChromaDB service is running and accessible."
        )
