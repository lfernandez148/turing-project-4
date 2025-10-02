"""Functions for saving evaluation results to database."""
from datetime import datetime
from typing import Dict
import pandas as pd
from databases.mysql_config import get_mysql_client


def save_results_to_db(results_df: pd.DataFrame) -> None:
    """
    Save evaluation results to MySQL database.
    
    Args:
        results_df: DataFrame containing evaluation results including overall_score and pass_fail (1=pass, 0=fail)
    """
    
    # Generate run_id using timestamp
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    conn = None
    cursor = None
    try:
        conn = get_mysql_client()
        cursor = conn.cursor()

        # Create table if not exists with new columns
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS qa_evaluation_results (
            id INT AUTO_INCREMENT PRIMARY KEY,
            run_id VARCHAR(20),
            question TEXT,
            expected_response TEXT,
            actual_response TEXT,
            context TEXT,
            faithfulness_score FLOAT,
            factual_correctness_score FLOAT,
            answer_similarity_score FLOAT,
            context_precision_score FLOAT,
            context_recall_score FLOAT,
            answer_accuracy_score FLOAT,
            overall_score FLOAT,
            pass_fail TINYINT(1),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_table_sql)

        # Prepare and insert data
        for _, row in results_df.iterrows():
            cursor.execute("""
                INSERT INTO qa_evaluation_results (
                    run_id,
                    question,
                    expected_response,
                    actual_response,
                    context,
                    faithfulness_score,
                    factual_correctness_score,
                    answer_similarity_score,
                    context_precision_score,
                    context_recall_score,
                    answer_accuracy_score,
                    overall_score,
                    pass_fail
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                run_id,
                row['question'],
                row['reference'],
                row['answer'],
                str(row['contexts']),
                row.get('faithfulness', 0),
                row.get('factual_correctness(mode=f1)', 0),
                row.get('answer_similarity', 0),
                row.get('context_precision', 0),
                row.get('context_recall', 0),
                row.get('nv_accuracy', 0),
                row.get('overall_score', 0),
                row.get('pass_fail', 0)  # Default to 0 (fail) if not provided
            ))
        
        conn.commit()
        print(f"Successfully saved evaluation results to MySQL with run_id: {run_id}")
    
    except Exception as e:
        print(f"Error saving results to database: {e}")
        if conn:
            conn.rollback()
        raise
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
