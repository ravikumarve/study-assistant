// Global State — single source of truth
const AppState = {
    currentFeature: 'explain',
    provider: 'ollama',
    theme: 'auto',
    ollamaAvailable: false,
    conversationHistory: [],
    sessionToken: localStorage.getItem('sessionToken') || generateUUID(),
};

// Initialize application
function initApp() {
    // Set session token
    localStorage.setItem('sessionToken', AppState.sessionToken);
    
    // Set initial theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        AppState.theme = savedTheme;
        document.documentElement.dataset.theme = savedTheme === 'auto' ? 
            (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') : savedTheme;
    }
    
    // Check Ollama status
    checkOllamaStatus();
    
    // Set up event listeners
    setupEventListeners();
    
    // Load progress if needed
    if (AppState.currentFeature === 'progress') {
        loadProgress();
    }
}

// Check Ollama status
async function checkOllamaStatus() {
    try {
        const response = await fetch('/api/ollama/status');
        const data = await response.json();
        AppState.ollamaAvailable = data.available;
        
        if (!data.available) {
            showToast('Ollama is not available. Using Puter AI instead.', 'warning');
            AppState.provider = 'puter';
            updateProviderLabel();
        }
    } catch (error) {
        console.error('Failed to check Ollama status:', error);
        AppState.ollamaAvailable = false;
    }
}

// Set up event listeners
function setupEventListeners() {
    // Chat input enter key
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendChatMessage();
            }
        });
    }
    
    // Keyboard navigation for feature panels
    document.addEventListener('keydown', handleKeyboardNavigation);
    
    // Theme preference changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (AppState.theme === 'auto') {
            document.documentElement.dataset.theme = e.matches ? 'dark' : 'light';
        }
    });
}

// Toggle theme
function toggleTheme() {
    const themes = ['light', 'dark', 'auto'];
    const currentIndex = themes.indexOf(AppState.theme);
    AppState.theme = themes[(currentIndex + 1) % themes.length];
    
    localStorage.setItem('theme', AppState.theme);
    updateThemeUI();
}

// Keyboard navigation handler
function handleKeyboardNavigation(e) {
    // Tab navigation between feature panels
    if (e.key === 'Tab' && !e.ctrlKey && !e.altKey) {
        const features = ['explain', 'quiz', 'flashcards', 'study-plan', 'mind-map', 'summarize', 'chat', 'progress'];
        const currentIndex = features.indexOf(AppState.currentFeature);
        
        if (e.shiftKey) {
            // Shift+Tab: move to previous feature
            const prevIndex = (currentIndex - 1 + features.length) % features.length;
            setActiveFeature(features[prevIndex]);
        } else {
            // Tab: move to next feature
            const nextIndex = (currentIndex + 1) % features.length;
            setActiveFeature(features[nextIndex]);
        }
        e.preventDefault();
    }
    
    // Arrow key navigation for flashcards
    if (AppState.currentFeature === 'flashcards' && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) {
        const flashcards = document.querySelectorAll('.flashcard');
        const currentCard = document.querySelector('.flashcard:focus-within');
        
        if (currentCard && flashcards.length > 1) {
            const currentIndex = Array.from(flashcards).indexOf(currentCard);
            let nextIndex;
            
            if (e.key === 'ArrowRight') {
                nextIndex = (currentIndex + 1) % flashcards.length;
            } else {
                nextIndex = (currentIndex - 1 + flashcards.length) % flashcards.length;
            }
            
            flashcards[nextIndex].focus();
            e.preventDefault();
        }
    }
}
    
    showToast(`Theme set to ${AppState.theme}`, 'info', 2000);
}

// Toggle provider
function toggleProvider() {
    AppState.provider = AppState.provider === 'ollama' ? 'puter' : 'ollama';
    updateProviderLabel();
    
    if (AppState.provider === 'ollama' && !AppState.ollamaAvailable) {
        showToast('Ollama is not available. Switch back to Puter AI?', 'warning', 3000);
    }
}

// Update provider label
function updateProviderLabel() {
    const label = document.getElementById('provider-label');
    if (label) {
        label.textContent = AppState.provider.charAt(0).toUpperCase() + AppState.provider.slice(1);
    }
}

// Set active feature
function setActiveFeature(feature) {
    // Update navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.feature === feature) {
            item.classList.add('active');
        }
    });
    
    // Update panels
    document.querySelectorAll('.feature-panel').forEach(panel => {
        panel.classList.remove('active');
        if (panel.dataset.feature === feature) {
            panel.classList.add('active');
        }
    });
    
    AppState.currentFeature = feature;
    
    // Load progress if switching to progress tab
    if (feature === 'progress') {
        loadProgress();
    }
    
    // Clear chat history if switching away from chat
    if (feature !== 'chat') {
        AppState.conversationHistory = [];
    }
}

// API Call Wrapper
async function apiCall(endpoint, payload = {}) {
    setLoading(true);
    const start = Date.now();
    
    try {
        const response = await fetch(`/api/${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Session-Token': AppState.sessionToken,
            },
            body: JSON.stringify({ ...payload, provider: AppState.provider }),
        });
        
        const data = await response.json();
        
        if (!data.success) {
            showToast(data.error, 'error');
            return null;
        }
        
        if (data.cached) {
            showToast('Loaded from cache ⚡', 'info', 2000);
        }
        
        // Log progress for AI activities
        if (endpoint !== 'progress' && endpoint !== 'ollama/status') {
            logProgress(endpoint, payload.topic || 'Unknown topic');
        }
        
        return data.data;
        
    } catch (error) {
        showToast('Network error — check your connection.', 'error');
        return null;
    } finally {
        setLoading(false);
    }
}

// Set loading state
function setLoading(loading) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.toggle('visible', loading);
    }
}

// Show toast message
function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    // Remove oldest toast if more than 3
    if (container.children.length > 3) {
        container.removeChild(container.children[0]);
    }
    
    // Auto remove
    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }
    }, duration);
}

// Generate UUID
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Feature-specific functions
async function generateExplanation() {
    const topic = document.getElementById('explain-topic').value.trim();
    const level = document.getElementById('explain-level').value;
    
    if (!topic) {
        showToast('Please enter a topic', 'error');
        return;
    }
    
    const data = await apiCall('explain', { topic, level });
    if (!data) return;
    
    renderExplanation(data);
}

async function generateQuiz() {
    const topic = document.getElementById('quiz-topic').value.trim();
    const count = parseInt(document.getElementById('quiz-count').value);
    const difficulty = document.getElementById('quiz-difficulty').value;
    
    if (!topic) {
        showToast('Please enter a topic', 'error');
        return;
    }
    
    const data = await apiCall('quiz', { topic, count, difficulty });
    if (!data) return;
    
    renderQuiz(data);
}

async function generateFlashcards() {
    const topic = document.getElementById('flashcards-topic').value.trim();
    const count = parseInt(document.getElementById('flashcards-count').value);
    
    if (!topic) {
        showToast('Please enter a topic', 'error');
        return;
    }
    
    const data = await apiCall('flashcards', { topic, count });
    if (!data) return;
    
    renderFlashcards(data);
}

async function generateStudyPlan() {
    const topic = document.getElementById('study-plan-topic').value.trim();
    const days = parseInt(document.getElementById('study-plan-days').value);
    const hours_per_day = parseInt(document.getElementById('study-plan-hours').value);
    
    if (!topic) {
        showToast('Please enter a topic', 'error');
        return;
    }
    
    const data = await apiCall('study-plan', { topic, days, hours_per_day });
    if (!data) return;
    
    renderStudyPlan(data);
}

async function generateMindMap() {
    const topic = document.getElementById('mind-map-topic').value.trim();
    
    if (!topic) {
        showToast('Please enter a topic', 'error');
        return;
    }
    
    const data = await apiCall('mind-map', { topic });
    if (!data) return;
    
    renderMindMap(data);
}

async function summarizeNotes() {
    const notes = document.getElementById('summarize-notes').value.trim();
    const format = document.getElementById('summarize-format').value;
    
    if (!notes) {
        showToast('Please enter some notes', 'error');
        return;
    }
    
    const data = await apiCall('summarize', { notes, format });
    if (!data) return;
    
    renderSummary(data);
}

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) {
        showToast('Please enter a message', 'error');
        return;
    }
    
    // Add user message to history and UI
    AppState.conversationHistory.push({ role: 'user', content: message });
    renderChatMessage(message, 'user');
    input.value = '';
    
    const data = await apiCall('chat', { 
        message, 
        history: AppState.conversationHistory 
    });
    if (!data) return;
    
    // Add AI response to history and UI
    AppState.conversationHistory.push({ role: 'assistant', content: data.response });
    renderChatMessage(data.response, 'assistant');
}

async function loadProgress() {
    try {
        const response = await fetch('/api/progress', {
            headers: {
                'X-Session-Token': AppState.sessionToken,
            },
        });
        
        const data = await response.json();
        
        if (data.success) {
            renderProgressStats(data.data);
        } else {
            showToast('Failed to load progress', 'error');
        }
    } catch (error) {
        showToast('Network error loading progress', 'error');
    }
}

// Log progress
async function logProgress(activity, topic) {
    try {
        await fetch('/api/progress', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Session-Token': AppState.sessionToken,
            },
            body: JSON.stringify({
                activity: activity.replace('api/', ''),
                topic: topic,
            }),
        });
    } catch (error) {
        console.error('Failed to log progress:', error);
    }
}

// Render functions
function renderExplanation(data) {
    const container = document.getElementById('explain-result');
    if (!container) return;
    
    container.innerHTML = `
        <div class="explanation-content">
            <h3>${data.explanation}</h3>
            
            ${data.examples && data.examples.length ? `
                <div class="examples-section">
                    <h4>Examples</h4>
                    <ul>
                        ${data.examples.map(ex => `<li>${ex}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            ${data.key_concepts && data.key_concepts.length ? `
                <div class="concepts-section">
                    <h4>Key Concepts</h4>
                    <ul>
                        ${data.key_concepts.map(concept => `<li>${concept}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            ${data.analogies && data.analogies.length ? `
                <div class="analogies-section">
                    <h4>Analogies</h4>
                    <ul>
                        ${data.analogies.map(analogy => `<li>${analogy}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            ${data.misconceptions && data.misconceptions.length ? `
                <div class="misconceptions-section">
                    <h4>Common Misconceptions</h4>
                    <ul>
                        ${data.misconceptions.map(misconception => `<li>${misconception}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        </div>
    `;
}

function renderQuiz(data) {
    const container = document.getElementById('quiz-result');
    if (!container) return;
    
    container.innerHTML = `
        <div class="quiz-container">
            <h3>Quiz: ${data.questions.length} Questions</h3>
            ${data.questions.map((q, index) => `
                <div class="quiz-question">
                    <h4>${index + 1}. ${q.question}</h4>
                    <div class="quiz-options">
                        ${q.options.map((opt, optIndex) => `
                            <label class="quiz-option">
                                <input type="radio" name="q${index}" value="${optIndex}">
                                ${opt}
                            </label>
                        `).join('')}
                    </div>
                    <div class="quiz-answer hidden">
                        <strong>Answer:</strong> ${q.answer}<br>
                        <strong>Explanation:</strong> ${q.explanation}
                    </div>
                    <button class="show-answer" onclick="this.parentNode.querySelector('.quiz-answer').classList.toggle('hidden');this.textContent=this.textContent==='Show Answer'?'Hide Answer':'Show Answer';">Show Answer</button>
                </div>
            `).join('')}
        </div>
    `;
}

function renderFlashcards(data) {
    const container = document.getElementById('flashcards-result');
    if (!container) return;
    
    container.innerHTML = data.cards.map(card => `
        <div class="flashcard" onclick="this.classList.toggle('flipped')">
            <div class="flashcard-inner">
                <div class="flashcard-front">
                    <h4>${card.front}</h4>
                    <small>Click to flip</small>
                </div>
                <div class="flashcard-back">
                    <p>${card.back}</p>
                    ${card.difficulty ? `<span class="difficulty-badge ${card.difficulty}">${card.difficulty}</span>` : ''}
                </div>
            </div>
        </div>
    `).join('');
}

function renderStudyPlan(data) {
    const container = document.getElementById('study-plan-result');
    if (!container) return;
    
    container.innerHTML = `
        <div class="study-plan">
            <h3>${data.plan.length}-Day Study Plan</h3>
            ${data.plan.map(day => `
                <div class="study-day">
                    <h4>${day.day}</h4>
                    ${day.tasks && day.tasks.length ? `
                        <div class="tasks">
                            <h5>Tasks:</h5>
                            <ul>
                                ${day.tasks.map(task => `<li>${task}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    ${day.milestones && day.milestones.length ? `
                        <div class="milestones">
                            <h5>Milestones:</h5>
                            <ul>
                                ${day.milestones.map(milestone => `<li>${milestone}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    ${day.resources && day.resources.length ? `
                        <div class="resources">
                            <h5>Resources:</h5>
                            <ul>
                                ${day.resources.map(resource => `<li>${resource}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `).join('')}
        </div>
    `;
}

function renderMindMap(data) {
    const container = document.getElementById('mind-map-result');
    if (!container) return;
    
    // Simple text representation for now
    container.innerHTML = `
        <div class="mind-map">
            <h3>${data.center}</h3>
            <div class="mind-map-content">
                <pre>${JSON.stringify(data, null, 2)}</pre>
            </div>
        </div>
    `;
}

function renderSummary(data) {
    const container = document.getElementById('summarize-result');
    if (!container) return;
    
    // Create copyable content
    const copyContent = `Summary: ${data.summary}\n\nKey Points:\n${data.key_points?.join('\n') || 'None'}`;
    
    container.innerHTML = `
        <div class="summary">
            <div class="summary-header">
                <h3>Summary</h3>
                ${data.confidence_score ? `<div class="confidence-badge">Confidence: ${data.confidence_score}%</div>` : ''}
                ${data.estimated_reading_time ? `<div class="time-badge">Read Time: ${data.estimated_reading_time} min</div>` : ''}
                ${data.information_density ? `<div class="density-badge">Density: ${data.information_density}</div>` : ''}
                ${data.complexity_level ? `<div class="complexity-badge ${data.complexity_level}">${data.complexity_level}</div>` : ''}
            </div>
            <div class="summary-content">
                <p>${data.summary}</p>
            </div>
            ${data.key_points && data.key_points.length ? `
                <div class="key-points">
                    <h4>Key Points:</h4>
                    <ul>
                        ${data.key_points.map(point => `<li>${point}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            ${data.key_takeaways && data.key_takeaways.length ? `
                <div class="key-takeaways">
                    <h4>Key Takeaways:</h4>
                    <ul>
                        ${data.key_takeaways.map(takeaway => `<li>${takeaway}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        </div>
    `;
    
    // Add copy button after rendering
    addCopyButton(container, copyContent);
}

function renderChatMessage(message, role) {
    const container = document.getElementById('chat-messages');
    if (!container) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;
    messageDiv.textContent = message;
    
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

function renderProgressStats(data) {
    const container = document.getElementById('progress-stats');
    if (!container) return;
    
    container.innerHTML = `
        <div class="stat-card">
            <div class="stat-value">${data.stats?.total_activities || 0}</div>
            <div class="stat-label">Total Activities</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${data.stats?.topics_covered || 0}</div>
            <div class="stat-label">Topics Covered</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${data.stats?.streak_days || 0}</div>
            <div class="stat-label">Day Streak</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${Math.round(data.stats?.avg_score || 0)}%</div>
            <div class="stat-label">Average Score</div>
        </div>
        
        ${data.recent_topics && data.recent_topics.length ? `
            <div class="recent-topics">
                <h4>Recent Topics:</h4>
                <ul>
                    ${data.recent_topics.map(topic => `<li>${topic}</li>`).join('')}
                </ul>
            </div>
        ` : ''}
        
        ${data.activity_breakdown ? `
            <div class="activity-breakdown">
                <h4>Activity Breakdown:</h4>
                <ul>
                    ${Object.entries(data.activity_breakdown).map(([activity, count]) => 
                        `<li>${activity}: ${count}</li>`
                    ).join('')}
                </ul>
            </div>
        ` : ''}
    `;
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', initApp);