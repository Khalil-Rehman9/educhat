# EduChat - AI Study Companion with RAG

EduChat is an AI-powered educational platform designed to help students learn from their documents using advanced Retrieval-Augmented Generation (RAG) technology. The application provides an intuitive interface for document management, intelligent chat, and auto-generated quizzes.

## Key Features

- **Multi-Format Document Upload**: Upload and process various document types (PDF, DOCX, PPTX, images)
- **RAG-powered Chat**: Ask questions about your uploaded documents and get intelligent, contextually relevant responses
- **Document Organization**: Categorize and organize documents for better management
- **Different Interaction Modes**:
  - **Standard Mode**: Regular explanations and answers
  - **Explain Like I'm 5 (ELI5)**: Simplified explanations for complex topics
- **Quiz Generator**: Create personalized quizzes to test your understanding of the material

## Technical Architecture

EduChat uses a modern architecture combining FastAPI, Streamlit, and Langchain:

### Backend (FastAPI)
- **Document Processing Pipeline**: Upload → Process → Extract Text → Create Embeddings → Store
- **RAG Integration**: Leverages Langchain and FAISS for vector storage and retrieval
- **Chat Service**: Implements conversation memory and retrieval chain for document-based responses
- **Quiz Generation**: Creates personalized quizzes based on document content

### Frontend (Streamlit)
- **Document Management**: Upload, organize, and search documents
- **Chat Interface**: Ask questions about documents with different modes
- **Quiz Interface**: Generate and take quizzes based on documents

### RAG System Flow
1. **Document Upload and Processing**:
   - Documents are uploaded and processed to extract text
   - Text is chunked and embedded using OpenAI embeddings
   - Vectors are stored in FAISS indexes

2. **Chat with RAG**:
   - User queries are matched against document embeddings
   - Relevant document chunks are retrieved
   - LLM generates responses using both the user query and retrieved context

3. **Quiz Generation**:
   - System retrieves relevant document content based on parameters
   - LLM generates questions, answers, and explanations based on the content

## Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/EduChat-bot.git
   cd EduChat-bot
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the project root with:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ```

### Running the Application

Start the application using:
   ```
python run.py
```

The application will be available at:
- Frontend (Streamlit): http://localhost:8501
- Backend API (FastAPI): http://localhost:8000

## Using EduChat

### Document Management
1. Use the Documents tab to upload and organize your files
2. Add categories to organize documents
3. Use search and filters to find specific documents

### Chat with Documents
1. Select documents you want to chat about
2. Choose a conversation mode (Standard or ELI5)
3. Ask questions about your documents

### Create and Take Quizzes
1. Select documents to create a quiz from
2. Configure quiz parameters (topic, difficulty, question types)
3. Generate and take the quiz to test your knowledge

## Development

### Project Structure
```
EduChat-bot/
├── app/
│   ├── backend/
│   │   ├── api/              # FastAPI routes and endpoints
│   │   ├── services/         # Business logic and RAG implementation
│   │   ├── database/         # Database models and operations
│   │   └── document_processors/ # Document parsing and processing
│   ├── frontend/             # Streamlit UI components
│   ├── config/               # Configuration settings
│   └── data/                 # Data storage directory
│       ├── raw/              # Original uploaded documents
│       ├── processed/        # Processed document data
│       └── embeddings/       # Vector embeddings
├── requirements.txt          # Python dependencies
└── run.py                    # Application runner
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Specify Your License]

## Acknowledgements

- [Langchain](https://langchain.com/) for the RAG implementation
- [OpenAI](https://openai.com/) for the language model and embeddings
- [Streamlit](https://streamlit.io/) for the frontend framework
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework 
- [FAISS](https://github.com/facebookresearch/faiss) for the vector database 