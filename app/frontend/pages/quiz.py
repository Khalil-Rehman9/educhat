"""
Quiz generation and interaction page for EduChat.
"""

import streamlit as st
import requests
import json
import os
import sys
from typing import List, Dict, Any

# Fix the Python path to ensure 'app' module can be found
current_file_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_file_path, "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import from app
from app.config.settings import BACKEND_HOST, BACKEND_PORT, API_PREFIX

# API URL configuration
API_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}{API_PREFIX}"

def get_documents():
    """Fetch documents list from the API"""
    try:
        response = requests.get(f"{API_URL}/documents/")
        if response.status_code == 200:
            return response.json().get("documents", [])
        else:
            st.error(f"Error fetching documents: {response.text}")
            return []
    except Exception as e:
        st.error(f"Error connecting to backend: {str(e)}")
        return []

def generate_quiz(document_ids, num_questions, question_types, difficulty, topic=None):
    """Generate a quiz from selected documents"""
    try:
        payload = {
            "document_ids": document_ids,
            "num_questions": num_questions,
            "question_types": question_types,
            "difficulty": difficulty
        }
        
        if topic:
            payload["topic"] = topic
        
        response = requests.post(
            f"{API_URL}/quiz/generate",
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error generating quiz: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to backend: {str(e)}")
        return None

def generate_topic_quiz(document_ids, topic, num_questions, question_types, difficulty):
    """Generate a topic-specific quiz from selected documents"""
    try:
        payload = {
            "document_ids": document_ids,
            "topic": topic,
            "num_questions": num_questions,
            "question_types": question_types,
            "difficulty": difficulty
        }
        
        response = requests.post(
            f"{API_URL}/quiz/generate/topic",
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error generating topic quiz: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to backend: {str(e)}")
        return None

def display_quiz(quiz_data):
    """Display quiz questions and collect answers"""
    if not quiz_data or "questions" not in quiz_data or not quiz_data["questions"]:
        st.warning("No quiz questions available.")
        return
    
    st.subheader("Quiz")
    
    questions = quiz_data["questions"]
    user_answers = {}
    
    if "topic" in quiz_data and quiz_data["topic"]:
        st.write(f"Topic: {quiz_data['topic']}")
    
    # Create a container with scrolling for the quiz
    quiz_container = st.container(height=450, border=False)
    
    with quiz_container:
        for i, question in enumerate(questions):
            with st.container(border=True):
                st.write(f"**Question {i+1}**: {question.get('question', '')}")
                
                question_type = question.get("type", "").lower()
                
                if not question_type and "options" in question:
                    question_type = "multiple_choice"
                elif not question_type:
                    question_type = "short_answer"
                
                if question_type == "multiple_choice":
                    options = question.get("options", [])
                    if options:
                        answer = st.radio("Select an answer:", options, key=f"q{i}")
                        user_answers[i] = {
                            "user_answer": answer,
                            "correct_answer": question.get("answer", ""),
                            "explanation": question.get("explanation", "")
                        }
                elif question_type == "true_false":
                    answer = st.radio("Select an answer:", ["True", "False"], key=f"q{i}")
                    user_answers[i] = {
                        "user_answer": answer,
                        "correct_answer": question.get("answer", ""),
                        "explanation": question.get("explanation", "")
                    }
                else:  # short_answer or any other type
                    answer = st.text_input("Your answer:", key=f"q{i}")
                    user_answers[i] = {
                        "user_answer": answer,
                        "correct_answer": question.get("answer", ""),
                        "explanation": question.get("explanation", "")
                    }
    
    # Check answers button
    if st.button("📝 Check Answers", use_container_width=True, type="primary"):
        st.subheader("Results")
        
        # Results container
        results_container = st.container(height=400, border=False)
        
        with results_container:
            correct_count = 0
            
            for i, question in enumerate(questions):
                with st.container(border=True):
                    st.write(f"**Question {i+1}**: {question.get('question', '')}")
                    
                    user_answer = user_answers[i]["user_answer"]
                    correct_answer = user_answers[i]["correct_answer"]
                    explanation = user_answers[i]["explanation"]
                    
                    st.write(f"Your answer: {user_answer}")
                    st.write(f"Correct answer: {correct_answer}")
                    
                    # Simple string matching for correctness
                    if isinstance(user_answer, str) and isinstance(correct_answer, str):
                        is_correct = user_answer.lower().strip() == correct_answer.lower().strip()
                    else:
                        is_correct = user_answer == correct_answer
                    
                    if is_correct:
                        st.success("Correct! ✅")
                        correct_count += 1
                    else:
                        st.error("Incorrect ❌")
                    
                    if explanation:
                        with st.expander("See explanation"):
                            st.write(explanation)
            
            # Show final score in a card
            with st.container(border=True):
                score_percentage = (correct_count / len(questions)) * 100
                
                cols = st.columns(3)
                with cols[0]:
                    st.metric("Questions", len(questions))
                with cols[1]:
                    st.metric("Correct Answers", correct_count)
                with cols[2]:
                    st.metric("Score", f"{score_percentage:.1f}%")
            
            if score_percentage >= 80:
                st.balloons()
                st.success("Excellent job! 🎉")
            elif score_percentage >= 60:
                st.success("Good work! Keep studying! 👍")
            else:
                st.info("Keep practicing! You'll improve with more study. 📚")

def main():
    st.title("📝 Quiz Generator")
    st.write("Generate quizzes based on your uploaded documents to test your understanding.")
    
    # Initialize state
    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = None
    
    # Layout - use columns for better organization
    col1, col2 = st.columns([1, 2])
    
    with col1:
        with st.container(border=True):
            st.subheader("Quiz Settings")
            
            # Document selection section
            st.write("**Step 1:** Select Documents")
            
            # Option to use documents already selected in main interface
            use_selected = False
            if "selected_documents" in st.session_state and st.session_state.selected_documents:
                use_selected = st.checkbox("Use documents selected in Library", value=True)
            
            selected_docs = []
            if use_selected:
                selected_docs = st.session_state.selected_documents
                # Show which documents are selected
                docs = get_documents()
                doc_names = []
                for doc_id in selected_docs:
                    for doc in docs:
                        if doc['id'] == doc_id:
                            doc_names.append(doc.get('title') or doc.get('original_filename', 'Untitled'))
                
                if doc_names:
                    st.write(f"📚 Using: {', '.join(doc_names)}")
            else:
                # Manual document selection
                documents = get_documents()
                if documents:
                    for doc in documents:
                        if st.checkbox(f"{doc.get('title') or doc.get('original_filename', 'Untitled')}", key=f"quiz_doc_{doc['id']}"):
                            selected_docs.append(doc['id'])
                else:
                    st.info("No documents available. Please upload documents first.")
            
            # Quiz parameters
            st.write("**Step 2:** Configure Quiz")
            
            quiz_types = ["General Quiz", "Topic-Specific Quiz"]
            quiz_type = st.radio(
                "Quiz Type:",
                quiz_types,
                horizontal=True
            )
            
            topic = None
            if quiz_type == "Topic-Specific Quiz":
                topic = st.text_input("Enter Topic:")
            
            difficulty_options = ["easy", "medium", "hard"]
            difficulty_labels = {"easy": "Easy", "medium": "Medium", "hard": "Hard"}
            
            difficulty = st.select_slider(
                "Difficulty:",
                options=difficulty_options,
                format_func=lambda x: difficulty_labels.get(x, x),
                value="medium"
            )
            
            num_questions = st.slider("Number of Questions:", min_value=1, max_value=10, value=5)
            
            # Question type selection using a more compact interface
            st.write("Question Types:")
            question_type_cols = st.columns(3)
            
            question_types = []
            with question_type_cols[0]:
                if st.checkbox("Multiple Choice", value=True, key="mc"):
                    question_types.append("multiple_choice")
            with question_type_cols[1]:
                if st.checkbox("True/False", value=True, key="tf"):
                    question_types.append("true_false")
            with question_type_cols[2]:
                if st.checkbox("Short Answer", value=False, key="sa"):
                    question_types.append("short_answer")
            
            # Generate button
            if st.button("🎮 Generate Quiz", use_container_width=True, type="primary"):
                if not selected_docs:
                    st.warning("Please select at least one document.")
                elif quiz_type == "Topic-Specific Quiz" and not topic:
                    st.warning("Please enter a topic.")
                elif not question_types:
                    st.warning("Please select at least one question type.")
                else:
                    with st.spinner("Generating quiz..."):
                        if quiz_type == "General Quiz":
                            quiz_data = generate_quiz(
                                document_ids=selected_docs,
                                num_questions=num_questions,
                                question_types=question_types,
                                difficulty=difficulty,
                                topic=topic
                            )
                        else:  # Topic-Specific Quiz
                            quiz_data = generate_topic_quiz(
                                document_ids=selected_docs,
                                topic=topic,
                                num_questions=num_questions,
                                question_types=question_types,
                                difficulty=difficulty
                            )
                        
                        if quiz_data and "error" not in quiz_data:
                            st.session_state.quiz_data = quiz_data
                            st.experimental_rerun()
                        elif quiz_data and "error" in quiz_data:
                            st.error(quiz_data["error"])
    
    with col2:
        if st.session_state.quiz_data:
            display_quiz(st.session_state.quiz_data)
        else:
            # Placeholder content when no quiz is available
            st.info("Quiz will appear here after generation.")
            
            # Center the image and add some helpful text
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image("https://img.icons8.com/color/96/000000/quiz.png", width=100)
                st.write("### How to use:")
                st.write("1. Select documents from the left panel")
                st.write("2. Choose quiz type and difficulty")
                st.write("3. Click 'Generate Quiz' to create your personalized quiz")
                st.write("4. Answer the questions and check your score")

if __name__ == "__main__":
    main() 