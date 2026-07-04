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
    isValidating: false,
    activeTab: 'gguf'   // 'gguf' | 'local' | 'online'
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
        this.workoutFormCard    = document.getElementById('workoutFormCard');
        this.outputArea         = document.getElementById('outputArea');
        this.generateBtn        = document.getElementById('generateBtn');
        this.workoutForm        = document.getElementById('workoutForm');
    }
};

// ============================================
// Model Configuration
// ============================================
const ModelConfig = {

    // ── Tab switching ──────────────────────────────────────────
    switchTab(tab) {
        AppState.activeTab = tab;
        AppState.modelValidated = false;
        this.clearValidation();

        // Update tab button styles
        document.querySelectorAll('.option-tab').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tab);
        });

        // Show/hide panels
        ['gguf', 'local', 'online'].forEach(t => {
            const panel = document.getElementById(`tab-${t}`);
            if (panel) panel.style.display = t === tab ? 'block' : 'none';
        });
    },

    // ── Validation output helpers ──────────────────────────────
    clearValidation() {
        AppState.modelValidated = false;
        const el = document.getElementById('modelValidationOutput');
        if (el) el.innerHTML = '';
    },

    _setValidating(btnId, loading) {
        const btn = document.getElementById(btnId);
        if (!btn) return;
        if (loading) {
            btn.disabled = true;
            btn.dataset.origText = btn.textContent;
            btn.textContent = '⏳ Connecting...';
        } else {
            btn.disabled = false;
            if (btn.dataset.origText) btn.textContent = btn.dataset.origText;
        }
    },

    // ── Online provider hint text ──────────────────────────────
    onOnlineProviderChange() {
        const provider = document.getElementById('onlineProvider').value;
        const hints = {
            openai:    'OpenAI key starts with <code>sk-</code>',
            anthropic: 'Anthropic key starts with <code>sk-ant-</code>',
            groq:      'Groq key starts with <code>gsk_</code>',
            gemini:    'Google AI Studio key starts with <code>AIza</code>'
        };
        const el = document.getElementById('onlineApiKeyHint');
        if (el) el.innerHTML = hints[provider] || '';
        // Reset model picker when provider changes
        const wrap = document.getElementById('onlineModelPickerWrap');
        if (wrap) wrap.style.display = 'none';
        this.clearValidation();
    },

    // ── Local provider: fetch models ───────────────────────────
    async fetchLocalModels() {
        const url    = (document.getElementById('localProviderUrl').value || '').trim();
        const apiKey = (document.getElementById('localProviderApiKey').value || '').trim();

        if (!url) {
            UI.showValidationError('Please enter the server base URL first.');
            return;
        }

        this._setValidating('fetchLocalModelsBtn', true);
        const wrap = document.getElementById('localModelPickerWrap');
        if (wrap) wrap.style.display = 'none';

        try {
            const resp = await fetch('/api/fetch-models', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider_type: 'local', base_url: url, api_key: apiKey || null })
            });
            const data = await resp.json();

            if (data.success && data.models && data.models.length > 0) {
                this._populateSelect('localModelSelect', data.models);
                if (wrap) wrap.style.display = 'block';
                UI.showValidationSuccess(`Connected! Found ${data.models.length} model(s).`);
            } else {
                UI.showValidationError(data.message || 'No models found. Is the server running?');
            }
        } catch (err) {
            UI.showValidationError(`Network error: ${err.message}`);
        } finally {
            this._setValidating('fetchLocalModelsBtn', false);
        }
    },

    // ── Online provider: verify key + fetch models ─────────────
    async fetchOnlineModels() {
        const provider = document.getElementById('onlineProvider').value;
        const apiKey   = (document.getElementById('onlineApiKey').value || '').trim();

        if (!apiKey) {
            UI.showValidationError('Please enter your API key first.');
            return;
        }

        this._setValidating('fetchOnlineModelsBtn', true);
        const wrap = document.getElementById('onlineModelPickerWrap');
        if (wrap) wrap.style.display = 'none';

        try {
            const resp = await fetch('/api/fetch-models', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider_type: 'online', provider, api_key: apiKey })
            });
            const data = await resp.json();

            if (data.success && data.models && data.models.length > 0) {
                this._populateSelect('onlineModelSelect', data.models);
                if (wrap) wrap.style.display = 'block';
                UI.showValidationSuccess(`API key verified! Found ${data.models.length} model(s).`);
            } else {
                UI.showValidationError(data.message || 'Could not verify API key or fetch models.');
            }
        } catch (err) {
            UI.showValidationError(`Network error: ${err.message}`);
        } finally {
            this._setValidating('fetchOnlineModelsBtn', false);
        }
    },

    // ── Populate a <select> with model ids ─────────────────────
    _populateSelect(selectId, models) {
        const sel = document.getElementById(selectId);
        if (!sel) return;
        sel.innerHTML = '';
        models.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m.id || m;
            opt.textContent = m.id || m;
            sel.appendChild(opt);
        });
    },

    // ── Build config object for backend ───────────────────────
    getConfig() {
        const tab = AppState.activeTab;

        if (tab === 'gguf') {
            return {
                model_type:       'gguf',
                gguf_model_path:  document.getElementById('ggufModelPath').value,
                gguf_n_ctx:       parseInt(document.getElementById('ggufContext').value) || 4096,
                gguf_n_gpu_layers: parseInt(document.getElementById('ggufGpuLayers').value) || 0
            };
        }

        if (tab === 'local') {
            const apiKey = (document.getElementById('localProviderApiKey').value || '').trim();
            const config = {
                model_type:   'local_server',
                llm_base_url: document.getElementById('localProviderUrl').value,
                llm_model:    document.getElementById('localModelSelect')?.value || ''
            };
            if (apiKey) config.llm_api_key = apiKey;
            return config;
        }

        if (tab === 'online') {
            const provider = document.getElementById('onlineProvider').value;
            const apiKey   = document.getElementById('onlineApiKey').value;
            const model    = document.getElementById('onlineModelSelect')?.value || '';
            const baseUrls = {
                openai:    'https://api.openai.com/v1',
                anthropic: 'https://api.anthropic.com/v1',
                groq:      'https://api.groq.com/openai/v1',
                gemini:    'https://generativelanguage.googleapis.com/v1beta/openai'
            };
            return {
                model_type:   provider,
                llm_base_url: baseUrls[provider] || '',
                llm_model:    model,
                llm_api_key:  apiKey
            };
        }

        return {};
    },

    // ── Validate before proceeding ─────────────────────────────
    async validate() {
        const tab = AppState.activeTab;

        if (tab === 'gguf') {
            // GGUF: just verify file path via existing endpoint
            const config = this.getConfig();
            const resp = await fetch('/api/validate-model', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            return resp.json();
        }

        if (tab === 'local') {
            const wrap = document.getElementById('localModelPickerWrap');
            if (!wrap || wrap.style.display === 'none') {
                return { success: false, message: 'Please click "Connect & Fetch Models" first to verify the server.' };
            }
            return { success: true, message: 'Local provider verified.' };
        }

        if (tab === 'online') {
            const wrap = document.getElementById('onlineModelPickerWrap');
            if (!wrap || wrap.style.display === 'none') {
                return { success: false, message: 'Please click "Verify Key & Fetch Models" first.' };
            }
            return { success: true, message: 'API key verified.' };
        }

        return { success: false, message: 'Unknown tab' };
    }
};

// ============================================
// Navigation
// ============================================
const Navigation = {
    async toWorkoutForm() {
        if (AppState.modelValidated) {
            this._proceedToForm();
            return;
        }

        const validateBtn = document.getElementById('validateModelBtn');
        if (validateBtn) {
            validateBtn.disabled = true;
            validateBtn.textContent = '🔄 Validating...';
        }

        AppState.isValidating = true;

        try {
            const result = await ModelConfig.validate();

            if (result.success) {
                AppState.modelValidated = true;
                AppState.modelConfig = ModelConfig.getConfig();
                UI.showValidationSuccess(result.message);
                setTimeout(() => this._proceedToForm(), 800);
            } else {
                UI.showValidationError(result.message, result.details);
            }
        } catch (error) {
            UI.showValidationError(`Validation failed: ${error.message}`);
        } finally {
            AppState.isValidating = false;
            if (validateBtn) {
                validateBtn.disabled = false;
                validateBtn.textContent = '🔌 Test & Continue →';
            }
        }
    },

    _proceedToForm() {
        AppState.currentStep = 'workout-form';
        DOM.modelSelectionCard.style.display = 'none';
        DOM.workoutFormCard.style.display = 'block';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    },

    toModelSelection() {
        AppState.currentStep = 'model-selection';
        AppState.modelValidated = false;
        DOM.workoutFormCard.style.display = 'none';
        DOM.modelSelectionCard.style.display = 'block';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
};

// ============================================
// Form Handling
// ============================================
const FormHandler = {
    collectFormData() {
        return {
            model_config:     AppState.modelConfig,
            height:           document.getElementById('height').value,
            weight:           document.getElementById('weight').value,
            age:              document.getElementById('age').value,
            gender:           document.getElementById('gender').value,
            fitness_level:    document.getElementById('fitness_level').value,
            days_per_week:    document.getElementById('days_per_week').value,
            session_duration: document.getElementById('session_duration').value,
            goals:            [document.getElementById('goals').value],
            equipment:        document.getElementById('equipment').value,
            injuries:         document.getElementById('injuries').value,
            preferred_split:  document.getElementById('preferred_split').value
        };
    },

    validate(data) {
        const errors = [];
        if (data.height < 100 || data.height > 250) errors.push('Height must be between 100–250 cm');
        if (data.weight < 30  || data.weight > 200)  errors.push('Weight must be between 30–200 kg');
        if (data.age < 13    || data.age > 100)      errors.push('Age must be between 13–100 years');
        if (data.days_per_week < 1 || data.days_per_week > 7) errors.push('Days per week must be 1–7');
        if (data.session_duration < 30 || data.session_duration > 180) errors.push('Session duration must be 30–180 minutes');
        if (!data.equipment || data.equipment.trim() === '') errors.push('Please specify available equipment');
        return errors;
    }
};

// ============================================
// API Communication
// ============================================
const API = {
    async generateWorkout(formData) {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
    }
};

// ============================================
// UI Rendering
// ============================================
const UI = {
    showValidationSuccess(message) {
        const el = document.getElementById('modelValidationOutput');
        if (el) el.innerHTML = `<div class="alert alert-success"><strong>✅ </strong>${this.escapeHtml(message)}</div>`;
    },

    // Alias kept for Navigation.toWorkoutForm compatibility
    showModelValidationSuccess(message) { this.showValidationSuccess(message); },

    showValidationError(message, details = null) {
        const el = document.getElementById('modelValidationOutput');
        if (!el) return;
        let html = `<div class="alert alert-error"><strong>❌ </strong>${this.escapeHtml(message)}`;
        if (details && details.hint) html += `<br><br><strong>💡 Hint:</strong> ${this.escapeHtml(details.hint)}`;
        html += '</div>';
        el.innerHTML = html;
    },

    showModelValidationError(message, details = null) { this.showValidationError(message, details); },

    showLoading() {
        DOM.outputArea.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <p>Generating your personalized workout plan...</p>
                <p style="color: var(--text-tertiary); font-size: 0.95em;">This may take 30–60 seconds</p>
            </div>`;
    },

    showError(message) {
        DOM.outputArea.innerHTML = `<div class="alert alert-error"><strong>❌ Error:</strong> ${this.escapeHtml(message)}</div>`;
    },

    showValidationErrors(errors) {
        const list = errors.map(e => `<li>${this.escapeHtml(e)}</li>`).join('');
        DOM.outputArea.innerHTML = `<div class="alert alert-error"><strong>❌ Validation Errors:</strong><ul style="margin-top:10px;margin-left:20px;">${list}</ul></div>`;
    },

    displayWorkoutPlan(plan) {
        let html = '<div class="workout-plan">';
        const workoutGroups = plan.workoutGroups || plan.workout_days || [];

        if (workoutGroups.length === 0) {
            html += '<p>No workout groups found in the plan.</p></div>';
            DOM.outputArea.innerHTML = html;
            return;
        }

        html += `<h3>${workoutGroups.length}-Day Workout Plan</h3>`;

        workoutGroups.forEach((group, index) => {
            const groupName = group.groupName || group.day_name || `Day ${index + 1}`;
            const exercises = group.selectedExercises || group.main_workout || [];

            html += `<div class="workout-day"><h3>${this.escapeHtml(groupName)}</h3>
                     <p><strong>Total Exercises:</strong> ${exercises.length}</p><h4>Exercises:</h4>`;

            exercises.forEach(exercise => {
                const name         = exercise.exerciseName || exercise.name || 'Unknown Exercise';
                const targetMuscles = exercise.targetMuscles || (exercise.target_muscles ? exercise.target_muscles.join(', ') : 'N/A');
                const bodyPart     = exercise.bodyPart || 'N/A';
                const equipment    = exercise.equipments || 'N/A';
                const description  = exercise.description || '';
                const instructions = description.split('$$').map(s => s.trim()).filter(s => s);

                html += `<div class="exercise">
                    <div class="exercise-name">${this.escapeHtml(name)}</div>
                    <div class="exercise-details">
                        <span>🎯 ${this.escapeHtml(targetMuscles)}</span>
                        <span>💪 ${this.escapeHtml(bodyPart)}</span>
                        <span>🏋️ ${this.escapeHtml(equipment)}</span>
                    </div>`;

                if (instructions.length > 0) {
                    html += '<div class="exercise-instructions"><strong>Instructions:</strong><ol>';
                    instructions.forEach(inst => { html += `<li>${this.escapeHtml(inst)}</li>`; });
                    html += '</ol></div>';
                }

                if (exercise.mediaUrl) {
                    html += `<div class="exercise-media"><img src="${this.escapeHtml(exercise.mediaUrl)}" alt="${this.escapeHtml(name)}" style="max-width:200px;border-radius:8px;"></div>`;
                }

                html += '</div>';
            });

            html += '</div>';
        });

        html += '</div>';
        DOM.outputArea.innerHTML = html;
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = String(text ?? '');
        return div.innerHTML;
    }
};

// ============================================
// Main Application Logic
// ============================================
const App = {
    init() {
        console.log('🏋️ Gym Workout RAG - Initializing...');
        DOM.init();
        this.setupEventListeners();
        // Show first tab
        ModelConfig.switchTab('gguf');
        console.log('✅ Application initialized successfully');
    },

    setupEventListeners() {
        if (DOM.workoutForm) {
            DOM.workoutForm.addEventListener('submit', e => this.handleFormSubmit(e));
        }
    },

    async handleFormSubmit(event) {
        event.preventDefault();
        if (AppState.isGenerating) return;

        try {
            AppState.isGenerating = true;
            DOM.generateBtn.disabled = true;

            const formData = FormHandler.collectFormData();
            const errors   = FormHandler.validate(formData);

            if (errors.length > 0) {
                UI.showValidationErrors(errors);
                return;
            }

            UI.showLoading();
            console.log('📤 Sending request to API...');
            const response = await API.generateWorkout(formData);

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
// Password Visibility Toggle
// ============================================
window.togglePasswordVisibility = (inputId, button) => {
    const input = document.getElementById(inputId);
    if (!input) return;
    if (input.type === 'password') {
        input.type = 'text';
        button.textContent = '🙈 Hide';
    } else {
        input.type = 'password';
        button.textContent = '👁️ Show';
    }
};

// ============================================
// Global function aliases (used by HTML onclick)
// ============================================
window.updateModelOptions  = () => {};  // no-op, kept for safety
window.proceedToWorkoutForm = () => Navigation.toWorkoutForm();
window.backToModelSelection = () => Navigation.toModelSelection();
window.generateWorkout      = (e) => App.handleFormSubmit(e);

// ============================================
// Initialize on DOM Ready
// ============================================
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => App.init());
} else {
    App.init();
}

// ============================================
// Export for testing
// ============================================
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { App, ModelConfig, FormHandler, UI, API };
}

// Made with Bob
