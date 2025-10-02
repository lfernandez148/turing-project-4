"""Streamlit UI for RAG Evaluation Results."""
import os
import sys
import pandas as pd
import streamlit as st
from . import login
from loguru import logger
from databases.mysql_config import get_mysql_client
from tests.evaluation.evaluate import run_evaluation  # Add this import

# Configure logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logs.config import LogConfig  # noqa: E402

# Set up logging to both file and console
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    format=LogConfig.STANDARD_FORMAT,
    level="INFO"
)
logger.add(
    LogConfig.get_evaluation_debug_log(),
    format=LogConfig.STANDARD_FORMAT,
    level="INFO"
)


def add_test_question(question: str, expected_response: str) -> bool:
    """Add a new test question to the database."""
    try:
        conn = get_mysql_client()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO qa_tests (question, expected_response) VALUES (%s, %s)",
            (question, expected_response)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error adding test question: {e}")
        return False


def update_test_question(id: int, question: str, expected_response: str) -> bool:
    """Update an existing test question."""
    try:
        conn = get_mysql_client()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE qa_tests SET question = %s, expected_response = %s WHERE id = %s",
            (question, expected_response, id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error updating test question: {e}")
        return False

def delete_test_question(id: int) -> bool:
    """Delete a test question."""
    try:
        conn = get_mysql_client()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM qa_tests WHERE id = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error deleting test question: {e}")
        return False


def get_test_questions():
    """Load test questions from MySQL database."""
    try:
        conn = get_mysql_client()
        query = "SELECT * FROM qa_tests"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        logger.error(f"Error loading test questions: {e}")
        return pd.DataFrame()


def get_evaluation_results():
    """Load evaluation results from MySQL database."""
    try:
        conn = get_mysql_client()
        query = """
        SELECT * FROM qa_evaluation_results 
        ORDER BY created_at DESC
        LIMIT 20
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        logger.error(f"Error loading evaluation results: {e}")
        return pd.DataFrame()


def app():
    """Evaluation results management page."""
    st.title("RAG Evaluation")
    
    # Get current user from login module
    user_info = login.get_current_user()
    
    if not user_info:
        st.warning("Please log in to access this page")
        return
        
    # Section 1: Test Questions Dataset
    test_questions = get_test_questions()
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.info(f"**Total Questions:** {len(test_questions)}")
    with col2:
        if st.button("🧪 Run Tests", use_container_width=True):
            with st.spinner('Running tests...'):
                if run_evaluation():
                    st.success("✅ Evaluation completed successfully!")
                    st.rerun()
                else:
                    st.error("Failed to run evaluation. Check logs for details.")
    with col3:
        if st.button("➕ Add New QA", use_container_width=True):
            st.session_state['show_add_form'] = True
            st.rerun()
    
    # Add new QA form
    if st.session_state.get('show_add_form', False):
        with st.container():
            st.subheader("Add New Question & Answer")
            new_question = st.text_area("Question", height=100, key="new_question")
            new_response = st.text_area("Expected Response", height=150, key="new_response")
            col1, col2, _ = st.columns([1, 1, 2])
            with col1:
                if st.button("Save", use_container_width=True):
                    if new_question and new_response:
                        if add_test_question(new_question, new_response):
                            st.success("Question added successfully!")
                            st.session_state['show_add_form'] = False
                            st.rerun()
                        else:
                            st.error("Failed to add question")
                    else:
                        st.warning("Please fill in both fields")
            with col2:
                if st.button("Cancel", use_container_width=True):
                    st.session_state['show_add_form'] = False
                    st.rerun()
            st.divider()
    
    # Display test questions with edit/delete options
    if not test_questions.empty:
        st.markdown("### 📋 Test Questions")
        for _, row in test_questions.iterrows():
            question_preview = (row['question'][:100] + '...') if len(row['question']) > 100 else row['question']
            with st.expander(f"❓ {question_preview}"):
                st.text_area(
                    "Question",
                    value=row['question'],
                    key=f"q_{row['id']}",
                    height=100
                )
                st.text_area(
                    "Expected Response",
                    value=row['expected_response'],
                    key=f"r_{row['id']}",
                    height=150
                )
                col1, col2, _ = st.columns([1, 1, 2])
                with col1:
                    if st.button("Update", key=f"update_{row['id']}", use_container_width=True):
                        updated_q = st.session_state[f"q_{row['id']}"]
                        updated_r = st.session_state[f"r_{row['id']}"]
                        if update_test_question(row['id'], updated_q, updated_r):
                            st.success("Updated successfully!")
                            st.rerun()
                        else:
                            st.error("Update failed")
                with col2:
                    if st.button("Delete", key=f"delete_{row['id']}", use_container_width=True):
                        if delete_test_question(row['id']):
                            st.success("Deleted successfully!")
                            st.rerun()
                        else:
                            st.error("Delete failed")
    else:
        st.warning("No test questions found in the dataset.")

    # Section 2: Evaluation Results
    st.markdown("### 📊 Test Results")
    results_df = get_evaluation_results()
    
    if not results_df.empty:
        runs = results_df['run_id'].unique()
        selected_run = st.selectbox(
            "Select Evaluation Run ID", 
            runs,
            key="run_selector"
        )
        
        # Get data for selected run
        run_data = results_df[results_df['run_id'] == selected_run]
        run_date = pd.to_datetime(run_data['created_at'].iloc[0]).strftime(
            '%Y-%m-%d %H:%M:%S'
        )
        st.info(f"**Run Date:** {run_date}")
        
        # Display summary metrics
        metric_cols = st.columns(3)
        with metric_cols[0]:
            st.metric(
                "📈 Faithfulness", 
                f"{run_data['faithfulness_score'].mean():.2f}",
                help="Measures how factually consistent the answer is with the given context"
            )
            st.metric(
                "🎯 Context Precision", 
                f"{run_data['context_precision_score'].mean():.2f}",
                help="Measures how relevant the retrieved context is to the question"
            )
            st.metric(
                "🎭 Overall Score", 
                f"{run_data['overall_score'].mean():.2f}",
                help="Combined score across all evaluation metrics"
            )
        with metric_cols[1]:
            st.metric(
                "🔄 Answer Similarity", 
                f"{run_data['answer_similarity_score'].mean():.2f}",
                help="Measures how similar the generated answer is to the expected response"
            )
            st.metric(
                "📡 Context Recall", 
                f"{run_data['context_recall_score'].mean():.2f}",
                help="Measures how well the context covers all aspects needed for the answer"
            )
            pass_rate = (run_data['pass_fail'].mean() * 100)
            st.metric(
                "✨ Pass Rate", 
                f"{pass_rate:.1f}%",
                help="Percentage of tests that passed the evaluation"
            )
        with metric_cols[2]:
            st.metric(
                "✅ Factual Correctness", 
                f"{run_data['factual_correctness_score'].mean():.2f}",
                help="Measures the factual accuracy of the generated answer"
            )
            st.metric(
                "🎪 Answer Accuracy", 
                f"{run_data['answer_accuracy_score'].mean():.2f}",
                help="Overall measure of answer accuracy"
            )
        
        # Detailed results section
        st.markdown("### 📋 Detailed Results")
        for idx, row in run_data.iterrows():
            question_preview = (row['question'][:100] + '...') if len(row['question']) > 100 else row['question']
            with st.expander(f"❓ {question_preview}"):
                # Question
                st.markdown("**❓ Question:**")
                st.text_area(
                    "Question",
                    value=row['question'],
                    height=100,
                    disabled=True,
                    label_visibility="collapsed",
                    key=f"question_{idx}"
                )
                
                # Expected Response
                st.markdown("**🎯 Expected Response:**")
                st.text_area(
                    "Expected Response",
                    value=row['expected_response'],
                    height=150,
                    disabled=True,
                    label_visibility="collapsed",
                    key=f"expected_{idx}"
                )
                
                # Actual Response
                st.markdown("**🤖 Actual Response:**")
                st.text_area(
                    "Actual Response",
                    value=row['actual_response'],
                    height=150,
                    disabled=True,
                    label_visibility="collapsed",
                    key=f"actual_{idx}"
                )
                
                # Context Used
                st.markdown("**📚 Context Used:**")
                st.text_area(
                    "Context",
                    value=row['context'],
                    height=100,
                    disabled=True,
                    label_visibility="collapsed",
                    key=f"context_{idx}"
                )
                
                # Individual metrics
                st.markdown("**📊 Metrics:**")
                metric_cols = st.columns(3)
                with metric_cols[0]:
                    st.metric(
                        "📈 Faithfulness", 
                        f"{row['faithfulness_score']:.2f}",
                        help="Measures how factually consistent the answer is with the given context"
                    )
                    st.metric(
                        "🎯 Context Precision", 
                        f"{row['context_precision_score']:.2f}",
                        help="Measures how relevant the retrieved context is to the question"
                    )
                    st.metric(
                        "🎭 Overall Score", 
                        f"{row['overall_score']:.2f}",
                        help="Combined score across all evaluation metrics"
                    )
                with metric_cols[1]:
                    st.metric(
                        "🔄 Answer Similarity", 
                        f"{row['answer_similarity_score']:.2f}",
                        help="Measures how similar the generated answer is to the expected response"
                    )
                    st.metric(
                        "📡 Context Recall", 
                        f"{row['context_recall_score']:.2f}",
                        help="Measures how well the context covers all aspects needed for the answer"
                    )
                    pass_status = "PASS" if row['pass_fail'] == 1 else "FAIL"
                    status_color = "green" if row['pass_fail'] == 1 else "red"
                    st.markdown(f"**✨ Status:** :{status_color}[{pass_status}]")
                with metric_cols[2]:
                    st.metric(
                        "✅ Factual Correctness", 
                        f"{row['factual_correctness_score']:.2f}",
                        help="Measures the factual accuracy of the generated answer"
                    )
                    st.metric(
                        "🎪 Answer Accuracy", 
                        f"{row['answer_accuracy_score']:.2f}",
                        help="Overall measure of answer accuracy"
                    )
    
    else:
        st.info("💡 No evaluation results found. Run evaluations to see results here.")
