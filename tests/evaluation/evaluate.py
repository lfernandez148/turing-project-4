"""Main RAG evaluation logic."""
import pandas as pd
import os
from typing import Dict, Optional, List, Tuple
from ragas import evaluate
from databases.mysql_config import get_mysql_client
from ragas.metrics import (
    Faithfulness,
    FactualCorrectness,
    AnswerSimilarity,
    ContextPrecision,
    ContextRecall,
    AnswerAccuracy,
)
from datasets import Dataset
from dotenv import load_dotenv
from agents.chatbot import chat_query
from databases.chroma_config import get_chroma_client
import chromadb
from loguru import logger

from tests.evaluation.db_utils import save_results_to_db

# Load environment variables
load_dotenv()


def get_test_data() -> Tuple[List[str], List[str]]:
    """Get test questions and expected responses from MySQL database."""
    try:
        conn = get_mysql_client()
        query = "SELECT question, expected_response FROM qa_tests"
        df = pd.read_sql(query, conn)
        conn.close()
        return df['question'].tolist(), df['expected_response'].tolist()
    except Exception as e:
        logger.error(f"Error loading test data: {e}")
        return [], []

def get_contexts_from_db(questions: List[str]) -> List[List[str]]:
    """Retrieve relevant contexts from ChromaDB for each question."""
    client = get_chroma_client()
    collection = client.get_collection("campaign_reports")
    contexts = []
    
    for question in questions:
        results = collection.query(
            query_texts=[question],
            n_results=3
        )
        if results and 'documents' in results:
            contexts.append(results['documents'][0])  # first item since we only have one query
        else:
            contexts.append([])
            
    return contexts

def evaluate_rag_system(
    custom_questions: Optional[list] = None
) -> Tuple[Dict, Dict]:
    """
    Evaluate the RAG system using RAGAS metrics.
    
    Args:
        custom_questions: Optional list of custom test questions
        
    Returns:
        Tuple containing:
        - evaluation results dictionary
        - data dictionary with questions, contexts, answers, and references
    """
    # Get test questions and references
    if custom_questions:
        questions = custom_questions
        references = [""] * len(questions)  # Empty references for custom questions
    else:
        questions, references = get_test_data()
    
    # Get contexts from ChromaDB
    contexts = get_contexts_from_db(questions)
    
    # Generate answers using the chatbot
    answers = []
    for question in questions:
        response = chat_query(question)
        
        if isinstance(response, dict):
            answer = response.get("message", "")
            source = response.get("source", "")
            if source:
                answer += f"\nSource: {source}"
        else:
            answer = str(response)
            
        answers.append(answer)
    
    # Create dataset for evaluation using HuggingFace datasets
    data = {
        'question': questions,
        'contexts': contexts,
        'answer': answers,
        'reference': references
    }
    dataset = Dataset.from_dict(data)
    
    # Run evaluation with all available metrics
    results = evaluate(
        dataset=dataset,
        metrics=[
            Faithfulness(),
            FactualCorrectness(),
            AnswerSimilarity(),
            ContextPrecision(),
            ContextRecall(),
            AnswerAccuracy(),
        ]
    )
    
    return results, data

def run_evaluation() -> bool:
    """
    Run the complete evaluation process and save results to database.
    
    Returns:
        bool: True if evaluation and saving succeeded, False otherwise
    """
    try:
        # Run evaluation
        results, data = evaluate_rag_system()
        
        # Convert results to DataFrame
        df = results.to_pandas()

        # Overall score
        weights = {
            'faithfulness': 0.20,
            'factual_correctness': 0.20,
            'answer_similarity': 0.40,
            'context_precision': 0.05,
            'context_recall': 0.05,
            'answer_accuracy': 0.10
        }
        row_scores = []
        row_pass_fail = []
        score_threshold = 0.5  # Define a threshold for pass/fail
        for _, row in df.iterrows():
            print('row:\n', row.to_dict())
            row_score = (
                (row['faithfulness'] * weights['faithfulness']) +
                (row['factual_correctness(mode=f1)'] * weights['factual_correctness']) +
                (row['answer_similarity'] * weights['answer_similarity']) +
                (row['context_precision'] * weights['context_precision']) +
                (row['context_recall'] * weights['context_recall']) +
                (row['nv_accuracy'] * weights['answer_accuracy'])
            )
            row_scores.append(row_score)
            row_pass_fail.append(1 if row_score >= score_threshold else 0)

        df['overall_score'] = row_scores
        df['pass_fail'] = row_pass_fail
        
        # Add additional columns needed for database
        for key in ['question', 'contexts', 'answer', 'reference']:
            df[key] = data[key]
        
        # Save to Database
        save_results_to_db(df)
        return True
        
    except Exception as e:
        logger.error(f"Error during evaluation process: {e}")
        return False

if __name__ == "__main__":
    success = run_evaluation()
    if success:
        print("Evaluation completed successfully!")
    else:
        print("Evaluation failed. Check logs for details.")
