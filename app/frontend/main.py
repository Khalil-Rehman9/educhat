import streamlit as st
import requests
import os
import json
from datetime import datetime
import sys
import time

# Fix the Python path to ensure 'app' module can be found
current_file_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_file_path, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import from app
from app.config.settings import APP_NAME, APP_DESCRIPTION, BACKEND_HOST, BACKEND_PORT, API_PREFIX

# API URL configuration
API_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}{API_PREFIX}"

# Page configuration
st.set_page_config(
    page_title=APP_NAME,
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "selected_documents" not in st.session_state:
    st.session_state.selected_documents = []
if "documents_list" not in st.session_state:
    # Initialize documents_list with data from the API
    try:
        response = requests.get(f"{API_URL}/documents/")
        if response.status_code == 200:
            st.session_state.documents_list = response.json().get("documents", [])
        else:
            st.session_state.documents_list = []
    except:
        st.session_state.documents_list = []
if "chat_mode" not in st.session_state:
    st.session_state.chat_mode = "standard"
if "current_page" not in st.session_state:
    st.session_state.current_page = "chat"
if "document_summary" not in st.session_state:
    st.session_state.document_summary = None
if "document_categories" not in st.session_state:
    st.session_state.document_categories = []
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Chat"

# Helper functions
def get_documents():
    """Fetch documents list from the API"""
    try:
        response = requests.get(f"{API_URL}/documents/")
        if response.status_code == 200:
            docs = response.json().get("documents", [])
            # Extract unique categories if they exist
            categories = set()
            for doc in docs:
                if "category" in doc and doc["category"]:
                    categories.add(doc["category"])
            st.session_state.document_categories = sorted(list(categories))
            return docs
        else:
            st.error(f"Error fetching documents: {response.text}")
            return []
    except Exception as e:
        st.error(f"Error connecting to backend: {str(e)}")
        return []

def refresh_documents():
    """Refresh the documents list"""
    docs = get_documents()
    if docs:
        st.session_state.documents_list = docs
    else:
        st.session_state.documents_list = []

def create_new_session():
    """Create a new chat session"""
    try:
        title = f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        response = requests.post(
            f"{API_URL}/chat/sessions",
            json={"title": title, "document_ids": st.session_state.selected_documents}
        )
        
        if response.status_code == 200:
            session_data = response.json()
            st.session_state.current_session_id = session_data["id"]
            st.session_state.chat_history = []
            return True
        else:
            st.error(f"Error creating chat session: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error connecting to backend: {str(e)}")
        return False

def send_message(message):
    """Send a message to the AI and get a response"""
    if not message.strip():
        return
    
    # Create a new session if none exists
    if not st.session_state.current_session_id:
        if not create_new_session():
            return
    
    try:
        response = requests.post(
            f"{API_URL}/chat/message",
            json={
                "message": message,
                "session_id": st.session_state.current_session_id,
                "document_ids": st.session_state.selected_documents,
                "mode": st.session_state.chat_mode
            }
        )
        
        if response.status_code == 200:
            response_data = response.json()
            st.session_state.chat_history = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in response_data["chat_history"]
            ]
        else:
            st.error(f"Error sending message: {response.text}")
    except Exception as e:
        st.error(f"Error connecting to backend: {str(e)}")

def upload_document(uploaded_file, title, category=None, description=None):
    """Upload a document to the backend"""
    try:
        files = {"file": uploaded_file}
        data = {}
        if title:
            data["title"] = title
        if description:
            data["description"] = description
        if category:
            data["category"] = category
        
        response = requests.post(
            f"{API_URL}/documents/upload",
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            refresh_documents()
            return response.json()
        else:
            st.error(f"Error uploading {uploaded_file.name}: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to backend: {str(e)}")
        return None

def get_document_summary(document_id):
    """Get a summary of a document."""
    url = f"{API_URL}/documents/{document_id}/summary"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error generating document summary: {str(e)}")
        return None

def delete_document(document_id):
    """Delete a document from the backend"""
    try:
        response = requests.delete(f"{API_URL}/documents/{document_id}")
        if response.status_code == 200:
            # Remove from selected documents if present
            if document_id in st.session_state.selected_documents:
                st.session_state.selected_documents.remove(document_id)
            refresh_documents()
            return True
        else:
            st.error(f"Error deleting document: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error connecting to backend: {str(e)}")
        return False

def create_chat_session(document_ids=None):
    """Create a new chat session with selected documents"""
    try:
        title = f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        response = requests.post(
            f"{API_URL}/chat/sessions",
            json={"title": title, "document_ids": document_ids or []}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error creating chat session: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to backend: {str(e)}")
        return None

# Chat page
def show_chat_page():
    st.title("💬 Chat with EduChat")
    
    # Display chat header based on selected documents
    if st.session_state.selected_documents:
        doc_names = []
        for doc_id in st.session_state.selected_documents:
            for doc in st.session_state.documents_list:
                if doc.get("id") == doc_id:
                    doc_name = doc.get("title") or doc.get("original_filename", "Untitled")
                    doc_names.append(doc_name)
        
        if doc_names:
            st.write(f"📄 Currently discussing: {', '.join(doc_names)}")
    
    # Chat container with fixed height for better UX
    chat_container = st.container(height=500, border=False)
    
    with chat_container:
        # Display chat history
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.chat_message("user").write(message["content"])
            else:
                st.chat_message("assistant").write(message["content"])
    
    # Chat input
    if user_input := st.chat_input("Ask a question about your documents..."):
        # Display user message
        st.chat_message("user").write(user_input)
        
        # Get AI response
        send_message(user_input)
        
        # Display assistant response (the function will update st.session_state.chat_history)
        if st.session_state.chat_history:
            assistant_messages = [msg for msg in st.session_state.chat_history if msg["role"] == "assistant"]
            if assistant_messages:
                st.chat_message("assistant").write(assistant_messages[-1]["content"])

# Import and use the quiz page
from app.frontend.pages.quiz import main as show_quiz_page

# Main UI
def main():
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/student-center.png", width=80)
        st.title(f"{APP_NAME}")
        st.write(APP_DESCRIPTION)
        
        # Navigation tabs with icons
        tabs = ["Chat", "Documents", "Quiz"]
        icons = ["💬", "📚", "📝"]
        
        # Create columns for tabs
        cols = st.columns(len(tabs))
        for i, (col, tab, icon) in enumerate(zip(cols, tabs, icons)):
            with col:
                if st.button(f"{icon} {tab}", key=f"tab_{tab}", use_container_width=True):
                    st.session_state.active_tab = tab
                    # Reset the page when switching to chat
                    if tab == "Chat":
                        st.session_state.current_page = "chat"
                    elif tab == "Quiz":
                        st.session_state.current_page = "quiz"
        
        st.divider()
        
        # Chat mode selection (only show when Chat tab is active)
        if st.session_state.active_tab == "Chat":
            st.subheader("💬 Chat Mode")
            chat_modes = ["standard", "eli5"]
            mode_labels = {"standard": "Standard", "eli5": "Explain Like I'm 5"}
            
            selected_mode = st.selectbox(
                "Select conversation mode:",
                options=chat_modes,
                format_func=lambda x: mode_labels.get(x, x),
                index=chat_modes.index(st.session_state.chat_mode)
            )
            
            if selected_mode != st.session_state.chat_mode:
                st.session_state.chat_mode = selected_mode
                
            if st.button("🧹 Clear Chat History"):
                st.session_state.chat_history = []
                st.session_state.current_session_id = None
                st.experimental_rerun()

    # Main content area based on active tab
    if st.session_state.active_tab == "Documents":
        # Document Management Page
        st.title("📚 Document Library")
        
        # Upload section in a container
        with st.expander("📤 Upload New Documents", expanded=False):
            uploaded_files = st.file_uploader(
                "Choose files to upload",
                type=["pdf", "docx", "pptx", "png", "jpg", "jpeg"],
                accept_multiple_files=True,
                help="You can select multiple files by holding Ctrl/Cmd while selecting files"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                doc_title_prefix = st.text_input("Title Prefix (Optional)")
                
            with col2:
                # Document category - allow choosing existing or creating new
                category_options = [""] + st.session_state.document_categories + ["+ Add New Category"]
                selected_category = st.selectbox("Category", options=category_options)
                
                if selected_category == "+ Add New Category":
                    new_category = st.text_input("Enter new category name")
                    category = new_category
                else:
                    category = selected_category
            
            # Create a placeholder for progress indication outside the expander
            upload_button = st.button("Upload All Files", use_container_width=True)
        
        # Progress indicators outside the expander
        upload_status_placeholder = st.empty()
        upload_progress_placeholder = st.empty()
        upload_result_placeholder = st.empty()
            
        # Process uploads if the button was clicked
        if uploaded_files and upload_button:
            # Show progress bar
            progress_bar = upload_progress_placeholder.progress(0)
            total_files = len(uploaded_files)
            successful_uploads = 0
            
            for i, uploaded_file in enumerate(uploaded_files):
                # Set title with optional prefix
                file_title = f"{doc_title_prefix} {uploaded_file.name}" if doc_title_prefix else uploaded_file.name
                
                # Update status
                upload_status_placeholder.info(f"Uploading {i+1}/{total_files}: {uploaded_file.name}")
                
                # Update progress bar
                progress_bar.progress((i) / total_files)
                
                # Upload the file
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    result = upload_document(uploaded_file, file_title, category)
                    if result:
                        successful_uploads += 1
            
            # Final progress update
            progress_bar.progress(1.0)
            
            # Final status update
            if successful_uploads == total_files:
                upload_result_placeholder.success(f"✅ Successfully uploaded all {total_files} files!")
            else:
                upload_result_placeholder.warning(f"⚠️ Uploaded {successful_uploads} out of {total_files} files")
        
            # Clear placeholders after 5 seconds
            time.sleep(3)
            upload_status_placeholder.empty()
        
        # Document library display
        documents = get_documents()
        
        if not documents:
            st.info("No documents uploaded yet. Use the upload section to add documents.")
        else:
            # Document statistics
            doc_count = len(documents)
            doc_types = {}
            for doc in documents:
                file_type = doc.get('file_type', '').lower()
                if file_type:
                    doc_types[file_type] = doc_types.get(file_type, 0) + 1
            
            # Display statistics in a card
            with st.container(border=True):
                st.subheader("📊 Library Statistics")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Documents", doc_count)
                with col2:
                    file_type_str = ", ".join([f"{count} {file_type}" for file_type, count in doc_types.items()])
                    st.write(f"**Document Types:** {file_type_str}")
            
            # Filter options
            st.subheader("🔍 Filter Documents")
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                search_term = st.text_input("Search by title:")
            
            with filter_col2:
                if st.session_state.document_categories:
                    filter_category = st.multiselect(
                        "Filter by category:",
                        options=["All"] + st.session_state.document_categories,
                        default=["All"]
                    )
                else:
                    filter_category = ["All"]
            
            # Filter documents based on search and category
            filtered_docs = documents
            if search_term:
                filtered_docs = [doc for doc in filtered_docs if search_term.lower() in (doc.get('title', '') or '').lower()]
            
            if filter_category and "All" not in filter_category:
                filtered_docs = [doc for doc in filtered_docs if doc.get('category', '') in filter_category]
            
            # Group documents by category
            if "All" in filter_category or not filter_category:
                # Group by category if filtering by All
                categories = ["Uncategorized"] + st.session_state.document_categories
                for category in categories:
                    category_docs = [doc for doc in filtered_docs if 
                                    (category == "Uncategorized" and not doc.get('category')) or 
                                    doc.get('category') == category]
                    
                    if category_docs:  # Only show categories that have documents
                        with st.expander(f"{category} ({len(category_docs)})", expanded=True):
                            for doc in category_docs:
                                doc_id = doc.get('id')
                                doc_title = doc.get('title') or doc.get('original_filename', 'Untitled')
                                doc_type = doc.get('file_type', '').lower()
                                
                                # Document card with actions
                                with st.container(border=True):
                                    col1, col2, col3 = st.columns([5, 2, 2])
                                    
                                    with col1:
                                        # File type icons
                                        file_icons = {
                                            "pdf": "📄", "docx": "📝", "doc": "📝", 
                                            "pptx": "📊", "ppt": "📊",
                                            "jpg": "🖼️", "jpeg": "🖼️", "png": "🖼️"
                                        }
                                        icon = file_icons.get(doc_type, "📄")
                                        
                                        is_selected = doc_id in st.session_state.selected_documents
                                        if st.checkbox(
                                            f"{icon} {doc_title}", 
                                            key=f"select_{doc_id}",
                                            value=is_selected
                                        ):
                                            if doc_id not in st.session_state.selected_documents:
                                                st.session_state.selected_documents.append(doc_id)
                                        else:
                                            if doc_id in st.session_state.selected_documents:
                                                st.session_state.selected_documents.remove(doc_id)
                                    
                                    with col2:
                                        # Summary button
                                        if st.button("📝 Summary", key=f"summary_{doc_id}", use_container_width=True):
                                            with st.spinner("Generating summary..."):
                                                summary = get_document_summary(doc_id)
                                                if summary:
                                                    st.session_state.document_summary = summary
                                                    st.experimental_rerun()
                                    
                                    with col3:
                                        # Delete button
                                        if st.button("🗑️ Delete", key=f"delete_{doc_id}", use_container_width=True):
                                            if delete_document(doc_id):
                                                st.success(f"Document '{doc_title}' deleted successfully")
                                                # Refresh the document list
                                                st.experimental_rerun()
            else:
                # Show flat list if filtering by specific category
                for doc in filtered_docs:
                    doc_id = doc.get('id')
                    doc_title = doc.get('title') or doc.get('original_filename', 'Untitled')
                    doc_type = doc.get('file_type', '').lower()
                    
                    # Document card with actions
                    with st.container(border=True):
                        col1, col2, col3, col4 = st.columns([4, 3, 2, 2])
                        
                        with col1:
                            # File type icons
                            file_icons = {
                                "pdf": "📄", "docx": "📝", "doc": "📝", 
                                "pptx": "📊", "ppt": "📊",
                                "jpg": "🖼️", "jpeg": "🖼️", "png": "🖼️"
                            }
                            icon = file_icons.get(doc_type, "📄")
                            st.write(f"{icon} {doc_title}")
                        
                        with col2:
                            is_selected = doc_id in st.session_state.selected_documents
                            if st.checkbox(
                                "Select",
                                key=f"select_{doc_id}",
                                value=is_selected
                            ):
                                if doc_id not in st.session_state.selected_documents:
                                    st.session_state.selected_documents.append(doc_id)
                            else:
                                if doc_id in st.session_state.selected_documents:
                                    st.session_state.selected_documents.remove(doc_id)
                        
                        with col3:
                            # Summary button
                            if st.button("📝 Summary", key=f"summary_{doc_id}", use_container_width=True):
                                with st.spinner("Generating summary..."):
                                    summary = get_document_summary(doc_id)
                                    if summary:
                                        st.session_state.document_summary = summary
                                        st.experimental_rerun()
                        
                        with col4:
                            # Delete button
                            if st.button("🗑️ Delete", key=f"delete_{doc_id}", use_container_width=True):
                                if delete_document(doc_id):
                                    st.success(f"Document '{doc_title}' deleted successfully")
                                    # Refresh the document list
                                    st.experimental_rerun()
            
            # Show action buttons for selected documents
            if st.session_state.selected_documents:
                st.subheader(f"Selected Documents: {len(st.session_state.selected_documents)}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💬 Start Chat with Selected Documents", use_container_width=True):
                        st.session_state.active_tab = "Chat"
                        st.session_state.current_page = "chat"
                        
                        # Create a new chat session
                        session = create_chat_session(st.session_state.selected_documents)
                        if session:
                            st.session_state.current_session_id = session.get("id")
                            st.session_state.chat_history = []
                            st.experimental_rerun()
                
                with col2:
                    if st.button("📝 Create Quiz from Selected Documents", use_container_width=True):
                        st.session_state.active_tab = "Quiz"
                        st.session_state.current_page = "quiz"
                        st.experimental_rerun()
    
    elif st.session_state.active_tab == "Quiz":
        # Show quiz page
        st.session_state.current_page = "quiz"
        show_quiz_page()
    else:
        # Default to chat page
        st.session_state.current_page = "chat"
        show_chat_page()

    # Display document summary if available
    if st.session_state.document_summary:
        with st.sidebar:
            with st.expander("📝 Document Summary", expanded=True):
                st.subheader(f"{st.session_state.document_summary.get('title', 'Document')}")
            st.write(st.session_state.document_summary.get('summary', 'No summary available'))
            if st.button("Close Summary"):
                st.session_state.document_summary = None
                st.experimental_rerun()

if __name__ == "__main__":
    main() 