/**
 * Gym Workout RAG - Frontend Application
 * Modern JavaScript with ES6+ features
 */

// ============================================
// State Management
// ============================================
const AppState = {
    currentStep: 'model-selection',
    modelConfig: {},
    userProfile: {},
    isGenerating: false,
    modelValidated: false,
    isValidating: false
};

// ============================================
// DOM Elements Cache
// ============================================
const DOM = {
    modelSelectionCard: null,
    workoutFormCard: null,
    outputArea: null,
    generateBtn: null,
    workoutForm: null,
    
    init() {
        this.modelSelectionCard = document.getElementById('modelSelectionCard');
        this.workoutFormCard = document.getElementById('workoutFormCard');
        this.outputArea = document.getElementById('outputArea');
        this.generateBtn = document.getElementById('generateBtn');
        this.workoutForm = document.getElementById('workoutForm');
    }
};

// ============================================
// Model Configuration
// ============================================
const ModelConfig = {
    availableModels: [],
    llmHost: '127.0.0.1',   // populated from /api/config at init

    // Maps provider key → [port, path]
    _providerPorts: {
        'lm_studio':   [1234,  '/v1'],
        'ollama':      [11434, '/v1'],
        'ollama_8001': [8001,  '/v1'],
    },

    /**
     * Build a full base URL for a local provider using the runtime host.
     * @param {string} providerKey - one of the _providerPorts keys
     * @returns {string} e.g. "http://host.docker.internal:1234/v1"
     */
    _providerUrl(providerKey) {
        const [port, path] = this._providerPorts[providerKey] || [1234, '/v1'];
        return `http://${this.llmHost}:${port}${path}`;
    },

    /**
     * Fetch the runtime LLM host from the backend config endpoint.
     * Called once on page load.
     */
    async loadRuntimeHost() {
        try {
            const resp = await fetch('/api/config');
            const data = await resp.json();
            if (data.llm_host) {
                this.llmHost = data.llm_host;
            }
        } catch (e) {
            console.log('Could not load runtime host, defaulting to 127.0.0.1', e);
        }
    },

    
    /**
     * Update visible model options based on selected type
     */
    updateOptions() {
        const modelType = document.getElementById('modelType').value;
        
        // Hide all options
        document.querySelectorAll('.model-options').forEach(el => {
            el.style.display = 'none';
        });
        
        // Show selected option
        const optionsMap = {
            'mlx': 'mlxOptions',
            'omlx': 'omlxOptions',
            'gguf': 'ggufOptions',
            'local_server': 'localServerOptions',
            'openai': 'openaiOptions',
            'anthropic': 'anthropicOptions',
            'groq': 'groqOptions'
        };
        
        const optionsId = optionsMap[modelType];
        if (optionsId) {
            document.getElementById(optionsId).style.display = 'block';
        }
        
        // Load cached values for OMLX
        if (modelType === 'omlx') {
            this.loadCachedOMLXConfig();
        }
    },
    
    /**
     * Load cached OMLX configuration from backend
     */
    async loadCachedOMLXConfig() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            
            // If backend has OMLX configured, pre-fill the fields
            if (data.backend_config) {
                const serverUrl = document.getElementById('omlxServerUrl');
                const apiKey = document.getElementById('omlxApiKey');
                
                if (data.backend_config.llm_base_url) {
                    serverUrl.value = data.backend_config.llm_base_url;
                }
                if (data.backend_config.llm_api_key) {
                    apiKey.value = data.backend_config.llm_api_key;
                }
            }
        } catch (error) {
            console.log('Could not load cached config:', error);
        }
    },
    
    /**
     * Fetch available models from OMLX server
     */
    async fetchOMLXModels() {
        const serverUrl = document.getElementById('omlxServerUrl').value;
        const apiKey = document.getElementById('omlxApiKey').value;
        
        if (!serverUrl) {
            return { success: false, message: 'Please enter server URL first' };
        }
        
        try {
            // Call backend to fetch models
            const response = await fetch('/api/models', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    base_url: serverUrl,
                    api_key: apiKey || null
                })
            });
            
            const data = await response.json();
            
            if (data.success && data.models) {
                this.availableModels = data.models;
                this.updateModelDropdown();
                return { success: true, count: data.models.length };
            } else {
                return { success: false, message: data.message || 'Failed to fetch models' };
            }
        } catch (error) {
            return { success: false, message: `Error: ${error.message}` };
        }
    },
    
    /**
     * Fetch available models from Local Server (LM Studio/OLLAMA)
     */
    async fetchLocalServerModels(button) {
        const providerKey = document.getElementById('localServerUrl').value;
        const resolvedUrl = this._providerUrl(providerKey);

        if (!providerKey) {
            UI.showNotification('Please select a server first', 'error');
            return;
        }

        // Show loading state
        const originalText = button.innerHTML;
        button.innerHTML = '⏳ Fetching...';
        button.disabled = true;
        
        try {
            // Call backend to fetch models using the runtime-resolved URL
            const response = await fetch('/api/models', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    base_url: resolvedUrl,
                    api_key: null
                })
            });
            
            const data = await response.json();
            
            if (data.success && data.models && data.models.length > 0) {
                this.availableModels = data.models;
                this.updateLocalServerModelDropdown();
                UI.showNotification(`Found ${data.models.length} model(s)`, 'success');
            } else {
                UI.showNotification(data.message || 'No models found. Make sure LM Studio server is running and a model is loaded.', 'error');
            }
        } catch (error) {
            UI.showNotification(`Error: ${error.message}`, 'error');
        } finally {
            button.innerHTML = originalText;
            button.disabled = false;
        }
    },
    
    /**
     * Update local server model dropdown with fetched models
     */
    updateLocalServerModelDropdown() {
        const modelInput = document.getElementById('localServerModel');
        const currentValue = modelInput.value;
        
        // Convert input to select dropdown
        if (modelInput.tagName === 'INPUT') {
            const select = document.createElement('select');
            select.id = 'localServerModel';
            select.className = modelInput.className;
            
            // Add models as options
            this.availableModels.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = model.id;
                select.appendChild(option);
            });
            
            // Replace input with select
            modelInput.parentNode.replaceChild(select, modelInput);
            
            // Try to select the current value if it exists
            if (currentValue && this.availableModels.some(m => m.id === currentValue)) {
                select.value = currentValue;
            }
        } else {
            // Already a select, just update options
            modelInput.innerHTML = '';
            this.availableModels.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = model.id;
                modelInput.appendChild(option);
            });
        }
    },
    
    /**
     * Clear local server models when URL changes
     */
    clearLocalServerModels() {
        const modelField = document.getElementById('localServerModel');
        
        // If it's a select, convert back to input
        if (modelField.tagName === 'SELECT') {
            const input = document.createElement('input');
            input.type = 'text';
            input.id = 'localServerModel';
            input.className = modelField.className;
            input.placeholder = 'local-model or select from list';
            modelField.parentNode.replaceChild(input, modelField);
        } else {
            modelField.value = '';
        }
        
        this.availableModels = [];
    },
    
    /**
     * Update model dropdown with fetched models (for OMLX)
     */
    updateModelDropdown() {
        const modelInput = document.getElementById('omlxModel');
        const currentValue = modelInput.value;
        
        // Convert input to select dropdown
        if (modelInput.tagName === 'INPUT') {
            const select = document.createElement('select');
            select.id = 'omlxModel';
            select.className = modelInput.className;
            
            // Add models as options
            this.availableModels.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = model.id;
                select.appendChild(option);
            });
            
            // Replace input with select
            modelInput.parentNode.replaceChild(select, modelInput);
            
            // Try to select the current value if it exists
            if (currentValue && this.availableModels.some(m => m.id === currentValue)) {
                select.value = currentValue;
            }
        } else {
            // Already a select, just update options
            modelInput.innerHTML = '';
            this.availableModels.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = model.id;
                modelInput.appendChild(option);
            });
        }
    },
    
    /**
     * Collect current model configuration
     */
    getConfig() {
        const modelType = document.getElementById('modelType').value;
        const config = { model_type: modelType };
        
        switch(modelType) {
            case 'mlx':
                config.mlx_model_path = document.getElementById('mlxModelPath').value;
                break;
                
            case 'omlx':
                config.llm_base_url = document.getElementById('omlxServerUrl').value;
                config.llm_model = document.getElementById('omlxModel').value;
                const omlxApiKey = document.getElementById('omlxApiKey').value;
                if (omlxApiKey && omlxApiKey.trim() !== '') {
                    config.llm_api_key = omlxApiKey;
                }
                break;
                
            case 'gguf':
                config.gguf_model_path = document.getElementById('ggufModelPath').value;
                config.gguf_n_ctx = parseInt(document.getElementById('ggufContext').value);
                config.gguf_n_gpu_layers = parseInt(document.getElementById('ggufGpuLayers').value);
                break;
                
            case 'local_server':
                config.llm_base_url = this._providerUrl(document.getElementById('localServerUrl').value);
                const localServerModel = document.getElementById('localServerModel').value;
                if (localServerModel && localServerModel.trim() !== '') {
                    config.llm_model = localServerModel;
                }
                // empty model → backend will auto-resolve from /v1/models
                break;
                
            case 'openai':
                config.llm_base_url = 'https://api.openai.com/v1';
                config.llm_model = document.getElementById('openaiModel').value;
                config.llm_api_key = document.getElementById('openaiApiKey').value;
                break;
                
            case 'anthropic':
                config.llm_base_url = 'https://api.anthropic.com/v1';
                config.llm_model = document.getElementById('anthropicModel').value;
                config.llm_api_key = document.getElementById('anthropicApiKey').value;
                break;
                
            case 'groq':
                config.llm_base_url = 'https://api.groq.com/openai/v1';
                config.llm_model = document.getElementById('groqModel').value;
                config.llm_api_key = document.getElementById('groqApiKey').value;
                break;
        }
        
        return config;
    },
    
    /**
     * Validate model configuration
     */
    async validate() {
        const config = this.getConfig();
        
        try {
            const response = await fetch('/api/validate-model', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });
            
            const data = await response.json();
            return data;
            
        } catch (error) {
            return {
                success: false,
                message: `Validation error: ${error.message}`
            };
        }
    }
};

// ============================================
// Navigation
// ============================================
const Navigation = {
    /**
     * Proceed to workout form (Step 2) - with validation
     */
    async toWorkoutForm() {
        // Check if model is already validated
        if (AppState.modelValidated) {
            this._proceedToForm();
            return;
        }
        
        // Validate model first
        const validateBtn = document.getElementById('validateModelBtn');
        if (validateBtn) {
            validateBtn.disabled = true;
            validateBtn.textContent = '🔄 Validating Model...';
        }
        
        AppState.isValidating = true;
        
        try {
            const result = await ModelConfig.validate();
            
            if (result.success) {
                AppState.modelValidated = true;
                AppState.modelConfig = ModelConfig.getConfig();
                
                // Show success message briefly
                UI.showModelValidationSuccess(result.message);
                
                // Proceed to form after short delay
                setTimeout(() => {
                    this._proceedToForm();
                }, 1000);
            } else {
                UI.showModelValidationError(result.message, result.details);
            }
        } catch (error) {
            UI.showModelValidationError(`Validation failed: ${error.message}`);
        } finally {
            AppState.isValidating = false;
            if (validateBtn) {
                validateBtn.disabled = false;
                validateBtn.textContent = 'Test Connection & Continue →';
            }
        }
    },
    
    /**
     * Internal method to proceed to form
     */
    _proceedToForm() {
        AppState.currentStep = 'workout-form';
        DOM.modelSelectionCard.style.display = 'none';
        DOM.workoutFormCard.style.display = 'block';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    },
    
    /**
     * Go back to model selection (Step 1)
     */
    toModelSelection() {
        AppState.currentStep = 'model-selection';
        AppState.modelValidated = false;  // Reset validation
        
        DOM.workoutFormCard.style.display = 'none';
        DOM.modelSelectionCard.style.display = 'block';
        
        // Smooth scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
};

// ============================================
// Form Handling
// ============================================
const FormHandler = {
    /**
     * Collect form data
     */
    collectFormData() {
        return {
            model_config: AppState.modelConfig,
            height: document.getElementById('height').value,
            weight: document.getElementById('weight').value,
            age: document.getElementById('age').value,
            gender: document.getElementById('gender').value,
            fitness_level: document.getElementById('fitness_level').value,
            days_per_week: document.getElementById('days_per_week').value,
            session_duration: document.getElementById('session_duration').value,
            goals: [document.getElementById('goals').value],
            equipment: document.getElementById('equipment').value,
            injuries: document.getElementById('injuries').value,
            preferred_split: document.getElementById('preferred_split').value
        };
    },
    
    /**
     * Validate form data
     */
    validate(data) {
        const errors = [];
        
        if (data.height < 100 || data.height > 250) {
            errors.push('Height must be between 100-250 cm');
        }
        
        if (data.weight < 30 || data.weight > 200) {
            errors.push('Weight must be between 30-200 kg');
        }
        
        if (data.age < 13 || data.age > 100) {
            errors.push('Age must be between 13-100 years');
        }
        
        if (data.days_per_week < 1 || data.days_per_week > 7) {
            errors.push('Days per week must be between 1-7');
        }
        
        if (data.session_duration < 30 || data.session_duration > 180) {
            errors.push('Session duration must be between 30-180 minutes');
        }
        
        if (!data.equipment || data.equipment.trim() === '') {
            errors.push('Please specify available equipment');
        }
        
        return errors;
    }
};

// ============================================
// API Communication
// ============================================
const API = {
    /**
     * Generate workout plan
     */
    async generateWorkout(formData) {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
};

// ============================================
// UI Rendering
// ============================================
const UI = {
    /**
     * Show model validation success
     */
    showModelValidationSuccess(message) {
        const outputArea = document.getElementById('modelValidationOutput');
        if (outputArea) {
            outputArea.innerHTML = `
                <div class="alert alert-success">
                    <strong>✅ Success:</strong> ${this.escapeHtml(message)}
                </div>
            `;
        }
    },
    
    /**
     * Show model validation error
     */
    showModelValidationError(message, details = null) {
        const outputArea = document.getElementById('modelValidationOutput');
        if (outputArea) {
            let html = `
                <div class="alert alert-error">
                    <strong>❌ Validation Failed:</strong> ${this.escapeHtml(message)}
            `;
            
            if (details && details.hint) {
                html += `<br><br><strong>💡 Hint:</strong> ${this.escapeHtml(details.hint)}`;
            }
            
            html += '</div>';
            outputArea.innerHTML = html;
        }
    },
    
    /**
     * Show loading state
     */
    showLoading() {
        DOM.outputArea.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <p>Generating your personalized workout plan...</p>
                <p style="color: var(--text-tertiary); font-size: 0.95em;">This may take 30-60 seconds</p>
            </div>
        `;
    },
    
    /**
     * Show error message
     */
    showError(message) {
        DOM.outputArea.innerHTML = `
            <div class="alert alert-error">
                <strong>❌ Error:</strong> ${this.escapeHtml(message)}
            </div>
        `;
    },
    
    /**
     * Show validation errors
     */
    showValidationErrors(errors) {
        const errorList = errors.map(err => `<li>${this.escapeHtml(err)}</li>`).join('');
        DOM.outputArea.innerHTML = `
            <div class="alert alert-error">
                <strong>❌ Validation Errors:</strong>
                <ul style="margin-top: 10px; margin-left: 20px;">
                    ${errorList}
                </ul>
            </div>
        `;
    },
    
    /**
     * Display workout plan - Updated for new custom format
     */
    displayWorkoutPlan(plan) {
        let html = '<div class="workout-plan">';
        
        // Check if we have workoutGroups (new format)
        const workoutGroups = plan.workoutGroups || plan.workout_days || [];
        
        if (workoutGroups.length === 0) {
            html += '<p>No workout groups found in the plan.</p>';
            html += '</div>';
            DOM.outputArea.innerHTML = html;
            return;
        }
        
        html += `<h3>${workoutGroups.length}-Day Workout Plan</h3>`;
        
        workoutGroups.forEach((group, index) => {
            // Support both old and new format
            const groupName = group.groupName || group.day_name || `Day ${index + 1}`;
            const exercises = group.selectedExercises || group.main_workout || [];
            
            html += `
                <div class="workout-day">
                    <h3>${this.escapeHtml(groupName)}</h3>
                    <p><strong>Total Exercises:</strong> ${exercises.length}</p>
                    
                    <h4>Exercises:</h4>
            `;
            
            exercises.forEach(exercise => {
                // Support both old and new format
                const exerciseName = exercise.exerciseName || exercise.name || 'Unknown Exercise';
                const targetMuscles = exercise.targetMuscles || (exercise.target_muscles ? exercise.target_muscles.join(', ') : 'N/A');
                const bodyPart = exercise.bodyPart || 'N/A';
                const equipment = exercise.equipments || 'N/A';
                
                // Parse description for instructions
                const description = exercise.description || '';
                const instructions = description.split('$$').map(s => s.trim()).filter(s => s);
                
                html += `
                    <div class="exercise">
                        <div class="exercise-name">${this.escapeHtml(exerciseName)}</div>
                        <div class="exercise-details">
                            <span>🎯 ${this.escapeHtml(targetMuscles)}</span>
                            <span>💪 ${this.escapeHtml(bodyPart)}</span>
                            <span>🏋️ ${this.escapeHtml(equipment)}</span>
                        </div>
                `;
                
                // Show instructions if available
                if (instructions.length > 0) {
                    html += '<div class="exercise-instructions"><strong>Instructions:</strong><ol>';
                    instructions.forEach(instruction => {
                        html += `<li>${this.escapeHtml(instruction)}</li>`;
                    });
                    html += '</ol></div>';
                }
                
                // Show media if available
                if (exercise.mediaUrl) {
                    html += `<div class="exercise-media"><img src="${this.escapeHtml(exercise.mediaUrl)}" alt="${this.escapeHtml(exerciseName)}" style="max-width: 200px; border-radius: 8px;"></div>`;
                }
                
                html += '</div>';
            });
            
            html += '</div>';
        });
        
        html += '</div>';
        DOM.outputArea.innerHTML = html;
    },
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// ============================================
// Main Application Logic
// ============================================
const App = {
    /**
     * Initialize application
     */
    init() {
        console.log('🏋️ Gym Workout RAG - Initializing...');
        
        // Fetch runtime host so local server URLs use the correct host
        ModelConfig.loadRuntimeHost();

        // Cache DOM elements
        DOM.init();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize model options
        ModelConfig.updateOptions();
        
        console.log('✅ Application initialized successfully');
    },
    
    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Model type change
        const modelTypeSelect = document.getElementById('modelType');
        if (modelTypeSelect) {
            modelTypeSelect.addEventListener('change', () => ModelConfig.updateOptions());
        }
        
        // Form submission
        if (DOM.workoutForm) {
            DOM.workoutForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }
    },
    
    /**
     * Handle form submission
     */
    async handleFormSubmit(event) {
        event.preventDefault();
        
        if (AppState.isGenerating) {
            console.log('⚠️ Generation already in progress');
            return;
        }
        
        try {
            AppState.isGenerating = true;
            DOM.generateBtn.disabled = true;
            
            // Collect and validate form data
            const formData = FormHandler.collectFormData();
            const validationErrors = FormHandler.validate(formData);
            
            if (validationErrors.length > 0) {
                UI.showValidationErrors(validationErrors);
                return;
            }
            
            // Show loading state
            UI.showLoading();
            
            // Call API
            console.log('📤 Sending request to API...');
            const response = await API.generateWorkout(formData);
            
            // Handle response
            if (response.success) {
                console.log('✅ Workout plan generated successfully');
                UI.displayWorkoutPlan(response.workout_plan);
            } else {
                console.error('❌ API returned error:', response.message);
                UI.showError(response.message || 'Failed to generate workout plan');
            }
            
        } catch (error) {
            console.error('❌ Error generating workout:', error);
            UI.showError(error.message || 'An unexpected error occurred');
        } finally {
            AppState.isGenerating = false;
            DOM.generateBtn.disabled = false;
        }
    }
};

// ============================================
// File Browser Handlers
// ============================================
window.handleMLXDirectorySelect = (event) => {
    const files = event.target.files;
    if (files.length > 0) {
        // Get the directory path from the first file
        const filePath = files[0].webkitRelativePath || files[0].name;
        // Extract directory path (remove filename)
        const dirPath = filePath.substring(0, filePath.lastIndexOf('/'));
        
        // For MLX models, we need the full path
        // Since we can't get absolute path from browser, we'll use the relative path
        // and let the user adjust if needed
        const modelPathInput = document.getElementById('mlxModelPath');
        if (dirPath) {
            // Show the relative path selected
            modelPathInput.value = dirPath;
            console.log('MLX model directory selected:', dirPath);
        }
    }
};

window.handleGGUFFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
        // For GGUF, we just need the filename
        // User will need to provide full path or we use the name
        const modelPathInput = document.getElementById('ggufModelPath');
        modelPathInput.value = file.name;
        console.log('GGUF model file selected:', file.name);
        
        // Show alert about full path
        const outputArea = document.getElementById('modelValidationOutput');
        if (outputArea) {
            outputArea.innerHTML = `
                <div class="alert alert-info">
                    <strong>📝 Note:</strong> File selected: ${file.name}<br>
                    Please enter the full path to this file in the text field above.
                </div>
            `;
        }
    }
};

// ============================================
// Password Visibility Toggle
// ============================================
window.togglePasswordVisibility = (inputId, button) => {
    const input = document.getElementById(inputId);
    if (input) {
        if (input.type === 'password') {
            input.type = 'text';
            button.textContent = '🙈 Hide';
        } else {
            input.type = 'password';
            button.textContent = '👁️ Show';
        }
    }
};

// ============================================
// Global Functions (for inline event handlers)
// ============================================
window.updateModelOptions = () => ModelConfig.updateOptions();
window.proceedToWorkoutForm = () => Navigation.toWorkoutForm();
window.backToModelSelection = () => Navigation.toModelSelection();
window.generateWorkout = (e) => App.handleFormSubmit(e);

/**
 * Fetch available models from OMLX server
 */
window.fetchOMLXModels = async () => {
    const statusDiv = document.getElementById('omlxModelFetchStatus');
    const fetchBtn = document.getElementById('fetchOMLXModelsBtn');
    
    if (fetchBtn) {
        fetchBtn.disabled = true;
        fetchBtn.textContent = '🔄 Fetching Models...';
    }
    
    if (statusDiv) {
        statusDiv.innerHTML = '<div class="alert alert-info">Fetching available models...</div>';
    }
    
    try {
        const result = await ModelConfig.fetchOMLXModels();
        
        if (result.success) {
            if (statusDiv) {
                statusDiv.innerHTML = `
                    <div class="alert alert-success">
                        ✅ Found ${result.count} model(s). Select one from the dropdown below.
                    </div>
                `;
            }
        } else {
            if (statusDiv) {
                statusDiv.innerHTML = `
                    <div class="alert alert-error">
                        ❌ ${result.message}
                    </div>
                `;
            }
        }
    } catch (error) {
        if (statusDiv) {
            statusDiv.innerHTML = `
                <div class="alert alert-error">
                    ❌ Error: ${error.message}
                </div>
            `;
        }
    } finally {
        if (fetchBtn) {
            fetchBtn.disabled = false;
            fetchBtn.textContent = '🔄 Fetch Available Models';
        }
    }
};

// ============================================
// Initialize on DOM Ready
// ============================================
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => App.init());
} else {
    App.init();
}

// ============================================
// Export for testing (if needed)
// ============================================
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { App, ModelConfig, FormHandler, UI, API };
}

// Made with Bob
