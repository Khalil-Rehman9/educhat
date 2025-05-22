// Main JavaScript file for EduChat

document.addEventListener('DOMContentLoaded', function() {
    // Chat functionality
    setupChatForm();
    
    // Document upload functionality
    setupDocumentUpload();
    
    // Quiz functionality
    setupQuizForm();
    
    // Document selection checkboxes
    setupDocumentSelection();
    
    // Handle alerts dismissal
    setupAlertDismissal();
});

// Chat functionality
function setupChatForm() {
    const chatForm = document.getElementById('chat-form');
    if (!chatForm) return;
    
    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const messageInput = document.getElementById('message-input');
        const message = messageInput.value.trim();
        
        if (!message) return;
        
        // Clear input
        messageInput.value = '';
        
        // Add user message to chat
        addMessageToChat('user', message);
        
        // Show loading indicator
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'chat-message assistant-message';
        loadingIndicator.innerHTML = '<div class="message-content"><div class="typing-indicator"><span></span><span></span><span></span></div></div>';
        document.querySelector('.chat-container').appendChild(loadingIndicator);
        
        // Scroll to bottom
        scrollChatToBottom();
        
        try {
            // Send message to backend
            const sessionId = document.getElementById('session-id')?.value || '';
            const mode = document.getElementById('chat-mode')?.value || 'standard';
            
            // Get selected document IDs from URL query parameter
            let selectedDocuments = [];
            const urlParams = new URLSearchParams(window.location.search);
            const selectedDocsParam = urlParams.get('selected_docs');
            
            if (selectedDocsParam) {
                selectedDocuments = selectedDocsParam.split(',');
            } else {
                // Fallback to checkboxes if URL param is not available
                document.querySelectorAll('.document-checkbox:checked').forEach(checkbox => {
                    selectedDocuments.push(checkbox.value);
                });
            }
            
            const response = await fetch('/api/chat/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    session_id: sessionId,
                    document_ids: selectedDocuments,
                    mode: mode
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to send message');
            }
            
            const data = await response.json();
            
            // Remove loading indicator
            document.querySelector('.chat-container').removeChild(loadingIndicator);
            
            // Add assistant response to chat
            if (data.chat_history && data.chat_history.length > 0) {
                const lastMessage = data.chat_history[data.chat_history.length - 1];
                if (lastMessage.role === 'assistant') {
                    addMessageToChat('assistant', lastMessage.content);
                }
            }
            
            // Update session ID if needed
            if (data.session_id && !sessionId) {
                const sessionIdInput = document.getElementById('session-id');
                if (sessionIdInput) {
                    sessionIdInput.value = data.session_id;
                }
            }
            
        } catch (error) {
            console.error('Error sending message:', error);
            
            // Remove loading indicator
            document.querySelector('.chat-container').removeChild(loadingIndicator);
            
            // Show error message
            addMessageToChat('assistant', 'Sorry, there was an error processing your message. Please try again.');
        }
    });
}

function addMessageToChat(role, content) {
    const chatContainer = document.querySelector('.chat-container');
    if (!chatContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}-message`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.textContent = content;
    
    messageDiv.appendChild(messageContent);
    chatContainer.appendChild(messageDiv);
    
    scrollChatToBottom();
}

function scrollChatToBottom() {
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

// Document upload functionality
function setupDocumentUpload() {
    const uploadForm = document.getElementById('upload-form');
    if (!uploadForm) return;
    
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const fileInput = document.getElementById('file-input');
        const titleInput = document.getElementById('title-input');
        const categoryInput = document.getElementById('category-input');
        
        if (fileInput.files.length === 0) {
            showAlert('Please select a file to upload', 'danger');
            return;
        }
        
        // Show loading indicator
        const uploadBtn = document.querySelector('#upload-form button[type="submit"]');
        const originalBtnText = uploadBtn.textContent;
        uploadBtn.disabled = true;
        uploadBtn.textContent = 'Uploading...';
        
        // Create FormData
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        if (titleInput.value) {
            formData.append('title', titleInput.value);
        }
        
        if (categoryInput.value) {
            formData.append('category', categoryInput.value);
        }
        
        try {
            const response = await fetch('/api/documents/upload', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Failed to upload document');
            }
            
            const data = await response.json();
            
            // Show success message
            showAlert('Document uploaded successfully!', 'success');
            
            // Reset form
            uploadForm.reset();
            
            // Refresh document list
            if (typeof refreshDocuments === 'function') {
                refreshDocuments();
            } else {
                // Fallback to page reload
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            }
            
        } catch (error) {
            console.error('Error uploading document:', error);
            showAlert('Error uploading document. Please try again.', 'danger');
        } finally {
            // Reset button
            uploadBtn.disabled = false;
            uploadBtn.textContent = originalBtnText;
        }
    });
}

// Quiz functionality
function setupQuizForm() {
    const quizForm = document.getElementById('quiz-form');
    if (!quizForm) return;
    
    quizForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get selected document IDs
        const selectedDocuments = [];
        document.querySelectorAll('.quiz-document-checkbox:checked').forEach(checkbox => {
            selectedDocuments.push(checkbox.value);
        });
        
        if (selectedDocuments.length === 0) {
            showAlert('Please select at least one document', 'warning');
            return;
        }
        
        const quizType = document.querySelector('input[name="quiz-type"]:checked').value;
        const difficulty = document.getElementById('difficulty').value;
        const numQuestions = document.getElementById('num-questions').value;
        
        // Get selected question types
        const questionTypes = [];
        document.querySelectorAll('input[name="question-type"]:checked').forEach(checkbox => {
            questionTypes.push(checkbox.value);
        });
        
        if (questionTypes.length === 0) {
            showAlert('Please select at least one question type', 'warning');
            return;
        }
        
        // Show loading state
        const submitBtn = quizForm.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Generating Quiz...';
        
        // Prepare request data
        const requestData = {
            document_ids: selectedDocuments,
            num_questions: parseInt(numQuestions),
            question_types: questionTypes,
            difficulty: difficulty
        };
        
        // Add topic if topic-specific quiz
        if (quizType === 'topic') {
            const topicInput = document.getElementById('topic-input');
            if (!topicInput.value.trim()) {
                showAlert('Please enter a topic', 'warning');
                submitBtn.disabled = false;
                submitBtn.textContent = originalBtnText;
                return;
            }
            requestData.topic = topicInput.value.trim();
        }
        
        try {
            // Determine endpoint based on quiz type
            const endpoint = quizType === 'topic' ? '/api/quiz/generate/topic' : '/api/quiz/generate';
            
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                throw new Error('Failed to generate quiz');
            }
            
            const quizData = await response.json();
            
            // Display quiz questions
            displayQuiz(quizData);
            
        } catch (error) {
            console.error('Error generating quiz:', error);
            showAlert('Error generating quiz. Please try again.', 'danger');
        } finally {
            // Reset button
            submitBtn.disabled = false;
            submitBtn.textContent = originalBtnText;
        }
    });
}

function displayQuiz(quizData) {
    const quizContainer = document.getElementById('quiz-container');
    if (!quizContainer) return;
    
    // Clear previous quiz
    quizContainer.innerHTML = '';
    
    if (!quizData.questions || quizData.questions.length === 0) {
        quizContainer.innerHTML = '<div class="alert alert-info">No questions were generated. Try different settings.</div>';
        return;
    }
    
    // Add quiz title
    const quizTitle = document.createElement('h2');
    quizTitle.textContent = quizData.topic ? `Quiz on ${quizData.topic}` : 'Quiz';
    quizContainer.appendChild(quizTitle);
    
    // Add difficulty
    const difficultyText = document.createElement('p');
    difficultyText.textContent = `Difficulty: ${quizData.difficulty.charAt(0).toUpperCase() + quizData.difficulty.slice(1)}`;
    quizContainer.appendChild(difficultyText);
    
    // Create form for quiz submission
    const form = document.createElement('form');
    form.id = 'quiz-answers-form';
    
    // Add questions
    quizData.questions.forEach((question, index) => {
        const questionCard = document.createElement('div');
        questionCard.className = 'question-card';
        
        const questionText = document.createElement('div');
        questionText.className = 'question-text';
        questionText.textContent = `${index + 1}. ${question.question}`;
        questionCard.appendChild(questionText);
        
        // Different input based on question type
        if (question.type === 'multiple_choice' || (question.options && question.options.length > 0)) {
            const optionsList = document.createElement('div');
            optionsList.className = 'options-list';
            
            (question.options || []).forEach((option, optionIndex) => {
                const optionItem = document.createElement('div');
                optionItem.className = 'option-item';
                
                const radio = document.createElement('input');
                radio.type = 'radio';
                radio.name = `question-${index}`;
                radio.id = `q${index}-option${optionIndex}`;
                radio.value = option;
                
                const label = document.createElement('label');
                label.htmlFor = `q${index}-option${optionIndex}`;
                label.textContent = option;
                
                optionItem.appendChild(radio);
                optionItem.appendChild(label);
                optionsList.appendChild(optionItem);
            });
            
            questionCard.appendChild(optionsList);
        } else if (question.type === 'true_false') {
            const optionsList = document.createElement('div');
            optionsList.className = 'options-list';
            
            ['True', 'False'].forEach((option, optionIndex) => {
                const optionItem = document.createElement('div');
                optionItem.className = 'option-item';
                
                const radio = document.createElement('input');
                radio.type = 'radio';
                radio.name = `question-${index}`;
                radio.id = `q${index}-option${optionIndex}`;
                radio.value = option;
                
                const label = document.createElement('label');
                label.htmlFor = `q${index}-option${optionIndex}`;
                label.textContent = option;
                
                optionItem.appendChild(radio);
                optionItem.appendChild(label);
                optionsList.appendChild(optionItem);
            });
            
            questionCard.appendChild(optionsList);
        } else {
            // Short answer
            const answerInput = document.createElement('input');
            answerInput.type = 'text';
            answerInput.className = 'form-control';
            answerInput.name = `question-${index}`;
            answerInput.placeholder = 'Your answer...';
            questionCard.appendChild(answerInput);
        }
        
        // Store correct answer and explanation as data attributes
        questionCard.dataset.answer = question.answer || '';
        questionCard.dataset.explanation = question.explanation || '';
        
        form.appendChild(questionCard);
    });
    
    // Add submit button
    const submitBtn = document.createElement('button');
    submitBtn.type = 'submit';
    submitBtn.className = 'btn btn-primary';
    submitBtn.textContent = 'Check Answers';
    form.appendChild(submitBtn);
    
    // Add form to container
    quizContainer.appendChild(form);
    
    // Add event listener for form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        checkQuizAnswers();
    });
}

function checkQuizAnswers() {
    const questionCards = document.querySelectorAll('.question-card');
    let correctCount = 0;
    
    questionCards.forEach((card, index) => {
        const correctAnswer = card.dataset.answer;
        const explanation = card.dataset.explanation;
        
        // Get user's answer
        let userAnswer;
        const radioInputs = card.querySelectorAll(`input[name="question-${index}"]`);
        
        if (radioInputs.length > 0) {
            // Multiple choice or true/false
            const selectedRadio = Array.from(radioInputs).find(radio => radio.checked);
            userAnswer = selectedRadio ? selectedRadio.value : '';
        } else {
            // Short answer
            const textInput = card.querySelector(`input[name="question-${index}"]`);
            userAnswer = textInput ? textInput.value.trim() : '';
        }
        
        // Create result display
        const resultDiv = document.createElement('div');
        resultDiv.className = 'question-result mt-2';
        
        // Check if answer is correct
        const isCorrect = userAnswer.toLowerCase() === correctAnswer.toLowerCase();
        
        if (isCorrect) {
            resultDiv.innerHTML = '<div class="alert alert-success">Correct! ✅</div>';
            correctCount++;
        } else {
            resultDiv.innerHTML = `
                <div class="alert alert-danger">Incorrect ❌</div>
                <div class="correct-answer">Correct answer: ${correctAnswer}</div>
            `;
        }
        
        // Add explanation if available
        if (explanation) {
            const explanationDiv = document.createElement('div');
            explanationDiv.className = 'explanation mt-1';
            explanationDiv.innerHTML = `<strong>Explanation:</strong> ${explanation}`;
            resultDiv.appendChild(explanationDiv);
        }
        
        // Add to card
        card.appendChild(resultDiv);
    });
    
    // Show final score
    const quizContainer = document.getElementById('quiz-container');
    const scoreDiv = document.createElement('div');
    scoreDiv.className = 'quiz-score card mt-2';
    
    const scorePercentage = (correctCount / questionCards.length) * 100;
    
    scoreDiv.innerHTML = `
        <div class="card-header">
            <h3 class="card-title">Quiz Results</h3>
        </div>
        <div class="card-body">
            <div class="score-details">
                <p>Questions: ${questionCards.length}</p>
                <p>Correct Answers: ${correctCount}</p>
                <p>Score: ${scorePercentage.toFixed(1)}%</p>
            </div>
            <div class="score-message mt-1">
                ${scorePercentage >= 80 ? '<div class="alert alert-success">Excellent job! 🎉</div>' : 
                  scorePercentage >= 60 ? '<div class="alert alert-info">Good work! Keep studying! 👍</div>' :
                  '<div class="alert alert-warning">Keep practicing! You\'ll improve with more study. 📚</div>'}
            </div>
        </div>
    `;
    
    quizContainer.appendChild(scoreDiv);
    
    // Disable the submit button
    const submitBtn = document.querySelector('#quiz-answers-form button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
    }
}

// Document selection functionality
function setupDocumentSelection() {
    const selectAllCheckbox = document.getElementById('select-all-docs');
    if (!selectAllCheckbox) return;
    
    // Load selected documents from URL query parameter
    const urlParams = new URLSearchParams(window.location.search);
    const selectedDocs = urlParams.get('selected_docs');
    
    if (selectedDocs) {
        try {
            const selectedDocIds = selectedDocs.split(',');
            document.querySelectorAll('.document-checkbox').forEach(checkbox => {
                if (selectedDocIds.includes(checkbox.value)) {
                    checkbox.checked = true;
                }
            });
        } catch (e) {
            console.error('Error parsing selected documents:', e);
        }
    }
    
    selectAllCheckbox.addEventListener('change', function() {
        const isChecked = this.checked;
        document.querySelectorAll('.document-checkbox').forEach(checkbox => {
            checkbox.checked = isChecked;
        });
        updateSelectedDocumentsParam();
    });
    
    // Add change event listener to all document checkboxes
    document.addEventListener('change', function(e) {
        if (e.target && e.target.classList.contains('document-checkbox')) {
            updateSelectedDocumentsParam();
        }
    });
}

// Update selected documents in URL query parameter
function updateSelectedDocumentsParam() {
    const selectedDocIds = [];
    document.querySelectorAll('.document-checkbox:checked').forEach(checkbox => {
        selectedDocIds.push(checkbox.value);
    });
    
    // Update URL without reloading page
    const url = new URL(window.location);
    if (selectedDocIds.length > 0) {
        url.searchParams.set('selected_docs', selectedDocIds.join(','));
    } else {
        url.searchParams.delete('selected_docs');
    }
    window.history.replaceState({}, '', url);
}

// Alert handling
function showAlert(message, type = 'info') {
    const alertsContainer = document.getElementById('alerts-container');
    if (!alertsContainer) return;
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="close-alert" aria-label="Close">×</button>
    `;
    
    alertsContainer.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode === alertsContainer) {
            alertsContainer.removeChild(alertDiv);
        }
    }, 5000);
}

function setupAlertDismissal() {
    document.addEventListener('click', function(e) {
        if (e.target && e.target.classList.contains('close-alert')) {
            const alert = e.target.parentNode;
            if (alert && alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }
    });
}

// Function to refresh documents list via AJAX
function refreshDocuments() {
    fetch('/api/documents/')
        .then(response => response.json())
        .then(data => {
            const documentList = document.getElementById('document-list');
            if (!documentList) return;
            
            // Clear current list
            documentList.innerHTML = '';
            
            if (!data.documents || data.documents.length === 0) {
                documentList.innerHTML = '<div class="alert alert-info">No documents uploaded yet.</div>';
                return;
            }
            
            // Group documents by category
            const documentsByCategory = {};
            data.documents.forEach(doc => {
                const category = doc.category || 'Uncategorized';
                if (!documentsByCategory[category]) {
                    documentsByCategory[category] = [];
                }
                documentsByCategory[category].push(doc);
            });
            
            // Create document cards grouped by category
            Object.keys(documentsByCategory).forEach(category => {
                const categorySection = document.createElement('div');
                categorySection.className = 'category-section mb-2';
                
                const categoryHeader = document.createElement('h3');
                categoryHeader.textContent = category;
                categorySection.appendChild(categoryHeader);
                
                const categoryDocs = documentsByCategory[category];
                const docsGrid = document.createElement('div');
                docsGrid.className = 'document-list';
                
                categoryDocs.forEach(doc => {
                    const docCard = createDocumentCard(doc);
                    docsGrid.appendChild(docCard);
                });
                
                categorySection.appendChild(docsGrid);
                documentList.appendChild(categorySection);
            });
        })
        .catch(error => {
            console.error('Error refreshing documents:', error);
            showAlert('Error loading documents. Please refresh the page.', 'danger');
        });
}

function createDocumentCard(doc) {
    const docCard = document.createElement('div');
    docCard.className = 'document-card';
    
    // Determine icon based on file type
    let icon = 'fa-file';
    if (doc.file_type === 'pdf') icon = 'fa-file-pdf';
    else if (doc.file_type === 'docx' || doc.file_type === 'doc') icon = 'fa-file-word';
    else if (doc.file_type === 'pptx' || doc.file_type === 'ppt') icon = 'fa-file-powerpoint';
    else if (['jpg', 'jpeg', 'png'].includes(doc.file_type)) icon = 'fa-file-image';
    
    // Document title with icon
    const title = document.createElement('div');
    title.className = 'document-title';
    title.innerHTML = `<i class="fas ${icon}"></i> ${doc.title || doc.original_filename || 'Untitled'}`;
    docCard.appendChild(title);
    
    // Document metadata
    const meta = document.createElement('div');
    meta.className = 'document-meta';
    meta.textContent = `Type: ${doc.file_type.toUpperCase()} | Uploaded: ${new Date(doc.upload_date).toLocaleDateString()}`;
    docCard.appendChild(meta);
    
    // Document selection
    const selection = document.createElement('div');
    selection.className = 'document-selection';
    
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.className = 'document-checkbox';
    checkbox.id = `doc-${doc.id}`;
    checkbox.value = doc.id;
    
    const label = document.createElement('label');
    label.htmlFor = `doc-${doc.id}`;
    label.textContent = 'Select for chat';
    
    selection.appendChild(checkbox);
    selection.appendChild(label);
    docCard.appendChild(selection);
    
    // Document actions
    const actions = document.createElement('div');
    actions.className = 'document-actions';
    
    // Summary button
    const summaryBtn = document.createElement('button');
    summaryBtn.className = 'btn btn-info btn-sm';
    summaryBtn.innerHTML = '<i class="fas fa-file-alt"></i> Summary';
    summaryBtn.onclick = () => getDocumentSummary(doc.id);
    
    // Delete button
    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'btn btn-danger btn-sm';
    deleteBtn.innerHTML = '<i class="fas fa-trash"></i> Delete';
    deleteBtn.onclick = () => deleteDocument(doc.id, doc.title || doc.original_filename);
    
    actions.appendChild(summaryBtn);
    actions.appendChild(deleteBtn);
    docCard.appendChild(actions);
    
    return docCard;
}

function getDocumentSummary(documentId) {
    fetch(`/api/documents/${documentId}/summary`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to get document summary');
            }
            return response.json();
        })
        .then(data => {
            // Create modal for summary
            const modal = document.createElement('div');
            modal.className = 'modal';
            modal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>${data.title}</h3>
                        <span class="close-modal">&times;</span>
                    </div>
                    <div class="modal-body">
                        <p>${data.summary}</p>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Show modal
            setTimeout(() => {
                modal.classList.add('show');
            }, 10);
            
            // Close modal when clicking on X or outside
            modal.querySelector('.close-modal').addEventListener('click', () => {
                modal.classList.remove('show');
                setTimeout(() => {
                    document.body.removeChild(modal);
                }, 300);
            });
            
            window.addEventListener('click', function(e) {
                if (e.target === modal) {
                    modal.classList.remove('show');
                    setTimeout(() => {
                        document.body.removeChild(modal);
                    }, 300);
                }
            });
        })
        .catch(error => {
            console.error('Error getting document summary:', error);
            showAlert('Error getting document summary. Please try again.', 'danger');
        });
}

function deleteDocument(documentId, documentTitle) {
    if (!confirm(`Are you sure you want to delete "${documentTitle}"?`)) {
        return;
    }
    
    fetch(`/api/documents/${documentId}`, {
        method: 'DELETE'
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to delete document');
            }
            return response.json();
        })
        .then(data => {
            showAlert(`Document "${documentTitle}" deleted successfully`, 'success');
            refreshDocuments();
        })
        .catch(error => {
            console.error('Error deleting document:', error);
            showAlert('Error deleting document. Please try again.', 'danger');
        });
} 