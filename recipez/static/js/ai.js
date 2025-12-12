/**
 * AI Assistant Dropdown System
 * Comprehensive implementation with voice input, recipe parsing, and accessibility
 */

/**
 * Check if sessionStorage is available and functional.
 * Handles private browsing mode and storage-disabled scenarios.
 * @returns {boolean} True if sessionStorage is available, false otherwise
 */
function isSessionStorageAvailable() {
    try {
        const test = '__storage_test__';
        sessionStorage.setItem(test, test);
        sessionStorage.removeItem(test);
        return true;
    } catch (e) {
        return false;
    }
}

/**
 * Safe sessionStorage getter with error handling.
 * @param {string} key - The storage key to retrieve
 * @returns {string|null} The stored value or null if unavailable/error
 */
function getSessionItem(key) {
    if (!isSessionStorageAvailable()) return null;
    try {
        return sessionStorage.getItem(key);
    } catch (e) {
        console.warn('SessionStorage read failed:', e);
        return null;
    }
}

/**
 * Safe sessionStorage setter with error handling.
 * @param {string} key - The storage key to set
 * @param {string} value - The value to store
 * @returns {boolean} True if successful, false otherwise
 */
function setSessionItem(key, value) {
    if (!isSessionStorageAvailable()) return false;
    try {
        sessionStorage.setItem(key, value);
        return true;
    } catch (e) {
        console.warn('SessionStorage write failed:', e);
        return false;
    }
}

/**
 * Safe sessionStorage remover with error handling.
 * @param {string} key - The storage key to remove
 * @returns {boolean} True if successful, false otherwise
 */
function removeSessionItem(key) {
    if (!isSessionStorageAvailable()) return false;
    try {
        sessionStorage.removeItem(key);
        return true;
    } catch (e) {
        console.warn('SessionStorage remove failed:', e);
        return false;
    }
}

class AIAssistant {
    constructor() {
        // Core elements - updated for FAB design
        this.dropdown = document.getElementById('ai-fab');
        this.dropdownMenu = document.getElementById('ai-fab-panel');
        this.toggleButton = document.getElementById('ai-assist-btn');
        this.closeButton = document.getElementById('ai-fab-close');
        this.isOpen = false;

        // Voice input elements
        this.micButton = null;
        this.recordingIndicator = null;
        this.transcriptionDisplay = null;
        this.transcriptionText = null;

        // Voice recording state
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;

        // Current workflow state
        this.currentWorkflow = null; // 'create', 'modify', or null

        // Recipe data
        this.recipesData = [];

        // Category data
        this.categoriesData = [];

        this.init();
    }

    init() {
        if (!this.dropdown || !this.dropdownMenu || !this.toggleButton) {
            console.warn('AI Assistant elements not found');
            return;
        }

        this.setupDropdownToggle();
        this.setupDropdownContent();
        this.setupVoiceInput();
        this.setupClickOutside();
        this.setupKeyboardNavigation();
        this.createErrorDisplay();
        this.loadRecipeData();
        this.setupModalCloseHandlers();

        // Check for AI error state on page load
        this.checkForErrorState();
    }

    setupModalCloseHandlers() {
        // Close button handlers for AI recipe modal
        document.querySelectorAll('.close-ai-modal').forEach(btn => {
            btn.addEventListener('click', () => this.hideRecipeModal());
        });

        // Close modal on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const modal = document.getElementById('ai-recipe-modal');
                if (modal && modal.classList.contains('show')) {
                    this.hideRecipeModal();
                }
            }
        });

        // Close modal on backdrop click
        const modal = document.getElementById('ai-recipe-modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideRecipeModal();
                }
            });
        }
    }

    /**
     * Check for AI-related errors on page load and reopen dropdown if needed.
     * This preserves user context when form submission errors occur.
     */
    checkForErrorState() {
        // Check if there are flash messages indicating AI error
        const flashMessages = document.querySelectorAll('.alert-danger, .alert-error');

        // Define AI-specific patterns using word boundaries to prevent false positives
        // (e.g., "ai" won't match "daily", "available", "email")
        const aiErrorPatterns = [
            /\bai\b/i,                    // Word boundary for "ai"
            /\brecipe\s+request\b/i,      // "recipe request"
            /\brecipe\s+modification\b/i, // "recipe modification"
            /\brecipe\s+description\b/i   // "recipe description"
        ];

        // Check if any message contains AI keywords
        const hasAIError = Array.from(flashMessages).some(msg => {
            const text = msg.textContent;
            return aiErrorPatterns.some(pattern => pattern.test(text));
        });

        // Only reopen if AI error AND not manually closed by user
        if (hasAIError && !getSessionItem('ai_dropdown_manually_closed')) {
            // Reopen dropdown with slight delay for smooth UX
            setTimeout(() => {
                this.open();

                // Check stored context first (most reliable)
                const storedContext = getSessionItem('ai_workflow_context');

                if (storedContext === 'create') {
                    this.showCreateOptions();
                } else if (storedContext === 'modify') {
                    this.showModifyOptions();
                } else {
                    // Fallback to URL/referrer detection
                    const urlParams = new URLSearchParams(window.location.search);
                    const referrer = document.referrer || '';

                    if (urlParams.has('create') || referrer.includes('/ai/create')) {
                        this.showCreateOptions();
                    } else if (urlParams.has('modify') || referrer.includes('/ai/modify')) {
                        this.showModifyOptions();
                    } else {
                        // Fallback: show main options if context unclear
                        this.showMainOptions();
                    }
                }

                // Clear context after use
                removeSessionItem('ai_workflow_context');
            }, 300); // 300ms delay makes reopen feel intentional, not jarring
        }
    }

    // === DROPDOWN FUNCTIONALITY ===

    setupDropdownToggle() {
        this.toggleButton.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggle();
        });

        // Close button for FAB panel
        this.closeButton?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.close();
        });
    }

    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    open() {
        this.dropdownMenu.classList.add('open');
        this.toggleButton.setAttribute('aria-expanded', 'true');
        this.isOpen = true;

        // Focus management for accessibility
        requestAnimationFrame(() => {
            const firstFocusable = this.dropdownMenu.querySelector('button:not([disabled]), [tabindex="0"]');
            if (firstFocusable) {
                firstFocusable.focus();
            }
        });
    }

    close() {
        // Track manual close to prevent auto-reopen on next page load
        setSessionItem('ai_dropdown_manually_closed', 'true');

        this.dropdownMenu.classList.remove('open');
        this.toggleButton.setAttribute('aria-expanded', 'false');
        this.isOpen = false;

        // Stop any ongoing recording
        if (this.isRecording) {
            this.stopRecording();
        }

        // Reset to main options
        this.showMainOptions();
    }

    setupClickOutside() {
        document.addEventListener('click', (e) => {
            if (this.isOpen && !this.dropdown.contains(e.target)) {
                this.close();
            }
        });
    }

    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
                this.toggleButton.focus();
            }
        });
    }

    // === DROPDOWN CONTENT SETUP ===

    setupDropdownContent() {
        // Main navigation buttons
        document.getElementById('create-recipe-btn')?.addEventListener('click', () => {
            this.showCreateOptions();
        });

        document.getElementById('modify-recipe-btn')?.addEventListener('click', () => {
            this.showModifyOptions();
        });

        // Back buttons
        document.getElementById('back-to-options-create')?.addEventListener('click', () => {
            this.showMainOptions();
        });

        document.getElementById('back-to-options-modify')?.addEventListener('click', () => {
            this.showMainOptions();
        });

        // Send buttons
        document.getElementById('send-create-btn')?.addEventListener('click', () => {
            this.handleCreateRequest();
        });

        document.getElementById('send-request-btn')?.addEventListener('click', () => {
            this.handleModifyRequest();
        });

        // Result buttons
        document.getElementById('ai-try-again-btn')?.addEventListener('click', () => {
            this.showMainOptions();
        });

        document.getElementById('ai-save-btn')?.addEventListener('click', () => {
            this.handleSaveRecipe();
        });
    }

    showMainOptions() {
        this.hideAllSections();
        document.getElementById('chat-options')?.classList.remove('hidden');
        this.currentWorkflow = null;
    }

    showCreateOptions() {
        this.hideAllSections();
        document.getElementById('create-recipe-options')?.classList.remove('hidden');
        this.currentWorkflow = 'create';
    }

    showModifyOptions() {
        this.hideAllSections();
        document.getElementById('modify-recipe-options')?.classList.remove('hidden');
        this.currentWorkflow = 'modify';
        this.createSearchableRecipeDropdown();
    }

    showResultSection() {
        this.hideAllSections();
        document.getElementById('ai-result')?.classList.remove('hidden');
    }

    hideAllSections() {
        const sections = ['chat-options', 'create-recipe-options', 'modify-recipe-options', 'ai-result'];
        sections.forEach(id => {
            document.getElementById(id)?.classList.add('hidden');
        });
    }

    // === VOICE INPUT FUNCTIONALITY ===

    setupVoiceInput() {
        this.createVoiceInputUI();
        this.checkMicrophoneSupport();
    }

    createVoiceInputUI() {
        const voiceSection = document.createElement('div');
        voiceSection.className = 'ai-voice-input-section';
        voiceSection.innerHTML = `
            <h6 class="ai-section-title">Voice Input</h6>
            <div class="ai-voice-controls">
                <button class="ai-mic-button" id="ai-mic-btn" aria-label="Start voice input">
                    <i class="fa-solid fa-microphone"></i>
                </button>
                <div class="ai-recording-indicator" id="ai-recording-indicator">
                    <span>Recording</span>
                    <div class="ai-recording-dots">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            </div>
            <div class="ai-transcription-display" id="ai-transcription-display">
                <div class="ai-transcription-text" id="ai-transcription-text"></div>
                <div class="ai-transcription-controls">
                    <button class="btn btn-sm btn-outline-secondary" id="ai-retry-btn">
                        <i class="fa-solid fa-redo me-1"></i>Retry
                    </button>
                    <button class="btn btn-sm btn-outline-primary" id="ai-approve-btn">
                        <i class="fa-solid fa-check me-1"></i>Use This
                    </button>
                </div>
            </div>
        `;

        this.dropdownMenu.insertBefore(voiceSection, this.dropdownMenu.firstChild);

        // Cache elements
        this.micButton = document.getElementById('ai-mic-btn');
        this.recordingIndicator = document.getElementById('ai-recording-indicator');
        this.transcriptionDisplay = document.getElementById('ai-transcription-display');
        this.transcriptionText = document.getElementById('ai-transcription-text');

        // Attach event listeners
        this.micButton?.addEventListener('click', () => this.toggleRecording());
        document.getElementById('ai-retry-btn')?.addEventListener('click', () => this.retryRecording());
        document.getElementById('ai-approve-btn')?.addEventListener('click', () => this.approveTranscription());
    }

    async checkMicrophoneSupport() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !window.MediaRecorder) {
            this.micButton.disabled = true;
            this.micButton.title = 'Voice input not supported in this browser';
            this.showFallbackMessage();
            return false;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop());
            this.micButton.disabled = false;
            return true;
        } catch (error) {
            console.warn('Microphone access denied or not supported:', error);
            this.micButton.disabled = true;
            this.micButton.title = 'Microphone access required for voice input';
            return false;
        }
    }

    showFallbackMessage() {
        const fallbackDiv = document.createElement('div');
        fallbackDiv.className = 'ai-fallback-message alert alert-info';
        fallbackDiv.innerHTML = `
            <i class="fa-solid fa-info-circle me-2"></i>
            Voice input not supported in this browser. Please type your request below.
        `;

        const voiceSection = this.dropdownMenu.querySelector('.ai-voice-input-section');
        if (voiceSection) {
            voiceSection.classList.add('hidden');
            this.dropdownMenu.insertBefore(fallbackDiv, voiceSection.nextSibling);
        }
    }

    async toggleRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    }

    async startRecording() {
        let stream = null;
        try {
            // CSP Compliance check - ensure microphone permissions are properly handled
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('MediaDevices API not available or blocked by CSP');
            }

            stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            // Store stream reference for proper cleanup
            this.currentStream = stream;

            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });

            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                try {
                    this.processRecording();
                } finally {
                    // Ensure stream cleanup even if processing fails
                    this.cleanupAudioStream();
                }
            };

            this.mediaRecorder.start(250); // Collect data every 250ms
            this.isRecording = true;

            this.updateRecordingUI(true);

            // Auto-stop after 30 seconds
            this.recordingTimeout = setTimeout(() => {
                if (this.isRecording) {
                    this.stopRecording();
                }
            }, 30000);

        } catch (error) {
            console.error('Failed to start recording:', error);
            // Cleanup stream if initialization failed
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
            this.showError('Failed to access microphone. Please check permissions.');
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.updateRecordingUI(false);

            if (this.recordingTimeout) {
                clearTimeout(this.recordingTimeout);
                this.recordingTimeout = null;
            }
        }
    }

    cleanupAudioStream() {
        // Secure cleanup of audio stream resources
        if (this.currentStream) {
            this.currentStream.getTracks().forEach(track => {
                track.stop();
                // Clear track references for security
                track.enabled = false;
            });
            this.currentStream = null;
        }

        // Clear audio data for security
        if (this.audioChunks) {
            this.audioChunks.length = 0;
        }

        // Clear MediaRecorder reference
        if (this.mediaRecorder) {
            this.mediaRecorder = null;
        }
    }

    updateRecordingUI(recording) {
        if (recording) {
            this.micButton.classList.add('recording');
            this.micButton.innerHTML = '<i class="fa-solid fa-stop"></i>';
            this.micButton.setAttribute('aria-label', 'Stop recording');
            this.recordingIndicator?.classList.add('active');
            this.transcriptionDisplay?.classList.remove('show');
        } else {
            this.micButton.classList.remove('recording');
            this.micButton.innerHTML = '<i class="fa-solid fa-microphone"></i>';
            this.micButton.setAttribute('aria-label', 'Start voice input');
            this.recordingIndicator?.classList.remove('active');
        }
    }

    async processRecording() {
        if (this.audioChunks.length === 0) {
            this.showError('No audio recorded. Please try again.');
            return;
        }

        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });

        // Audio blob integrity validation
        if (!this.validateAudioBlob(audioBlob)) {
            this.showError('Invalid audio data. Please try recording again.');
            return;
        }

        try {
            this.showProcessingState();
            const transcription = await this.transcribeAudio(audioBlob);
            this.displayTranscription(transcription);
        } catch (error) {
            console.error('Transcription failed:', error);
            this.showError('Failed to transcribe audio. Please try again.');
        }
    }

    validateAudioBlob(blob) {
        // Basic audio blob validation for security
        if (!blob || blob.size === 0) {
            return false;
        }

        // Check blob size is reasonable (max 10MB for 30 seconds audio)
        const maxSize = 10 * 1024 * 1024; // 10MB
        if (blob.size > maxSize) {
            console.warn('Audio blob exceeds maximum size limit');
            return false;
        }

        // Validate MIME type
        if (!blob.type || !blob.type.startsWith('audio/')) {
            console.warn('Invalid audio blob MIME type:', blob.type);
            return false;
        }

        return true;
    }

    async transcribeAudio(audioBlob) {
        // Validate CSRF token before making request
        if (!this.validateCsrfToken()) {
            throw new Error('CSRF token validation failed. Please refresh the page.');
        }

        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        formData.append('csrf_token', this.getCsrfToken());

        const response = await fetch('/api/ai/stt', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();

        if (result.error) {
            throw new Error(result.error);
        }

        return result.transcription;
    }

    displayTranscription(text) {
        this.transcriptionText.textContent = text;
        this.transcriptionDisplay?.classList.add('show');
    }

    showProcessingState() {
        this.transcriptionText.textContent = 'Processing audio...';
        this.transcriptionDisplay?.classList.add('show');
    }

    retryRecording() {
        this.transcriptionDisplay?.classList.remove('show');
        this.toggleRecording();
    }

    approveTranscription() {
        const text = this.transcriptionText.textContent;
        if (text && !text.startsWith('Error:') && text !== 'Processing audio...') {
            this.fillTextArea(text);
            this.transcriptionDisplay?.classList.remove('show');
        }
    }

    fillTextArea(text) {
        // Determine which text area to fill based on current workflow
        if (this.currentWorkflow === 'create') {
            const createText = document.getElementById('create-text');
            if (createText) {
                createText.value = text;
                createText.focus();
            }
        } else if (this.currentWorkflow === 'modify') {
            const modificationText = document.getElementById('modification-text');
            if (modificationText) {
                modificationText.value = text;
                modificationText.focus();
            }
        }
    }

    // === RECIPE DATA MANAGEMENT ===

    loadRecipeData() {
        try {
            const recipesAttribute = this.dropdownMenu?.dataset.recipes;
            this.recipesData = recipesAttribute ? JSON.parse(recipesAttribute) : [];
        } catch (error) {
            console.error('Failed to parse recipes data:', error);
            this.recipesData = [];
        }
    }

    loadCategoryData() {
        try {
            const categoriesAttribute = this.dropdownMenu?.dataset.categories;
            this.categoriesData = categoriesAttribute ? JSON.parse(categoriesAttribute) : [];
        } catch (error) {
            console.error('Failed to parse categories data:', error);
            this.categoriesData = [];
        }
    }

    normalizeText(text) {
        /**
         * Normalize text by converting Unicode characters to ASCII equivalents
         * and cleaning corrupted UTF-8 sequences.
         * This prevents validation errors when LLM generates Unicode variants
         * or when text gets corrupted during transmission.
         *
         * @param {string} text - The text to normalize
         * @returns {string} Normalized text with ASCII characters
         */
        if (!text) return text;

        let normalized = text;

        // Step 1: Clean common corrupted UTF-8 patterns
        // These often result from double-encoding or improper character conversion

        // Remove Unicode replacement character
        normalized = normalized.replace(/\uFFFD/g, '');  // Replacement character �

        // Handle common multi-byte corruption patterns
        // These appear when UTF-8 is misinterpreted as Latin-1 or Windows-1252
        normalized = normalized.replace(/Ã¢â‚¬â€œ/g, '–');  // en-dash corruption
        normalized = normalized.replace(/Ã¢â‚¬â€�/g, '—');  // em-dash corruption
        normalized = normalized.replace(/Ã¢â‚¬â„¢/g, "'");  // right single quote
        normalized = normalized.replace(/Ã¢â‚¬Ëœ/g, "'");  // left single quote
        normalized = normalized.replace(/Ã¢â‚¬Å"/g, '"');  // left double quote
        normalized = normalized.replace(/Ã¢â‚¬\u009d/g, '"');  // right double quote
        normalized = normalized.replace(/Ã¢â‚¬Â¦/g, '...');  // ellipsis

        // Simpler 2-byte patterns that are more common
        normalized = normalized.replace(/â€"/g, '–');  // en-dash variant 1
        normalized = normalized.replace(/â€"/g, '—');  // em-dash variant 1
        normalized = normalized.replace(/â€™/g, "'");  // right single quote variant
        normalized = normalized.replace(/â€œ/g, '"');  // left double quote variant
        normalized = normalized.replace(/â€�/g, '"');  // right double quote variant

        // Handle the specific corruption from the actual failing case
        // "glutenâ��free" pattern - this is â + null bytes/control chars + �
        normalized = normalized.replace(/â[\x80-\xFF]{0,2}/g, '-');  // Catch â followed by any high bytes

        // Step 2: Replace Unicode hyphens (U+2010 through U+2015, U+2212) with ASCII hyphen (U+002D)
        normalized = normalized.replace(/[\u2010-\u2015\u2212]/g, '-');

        // Step 3: Replace Unicode apostrophes/quotes with ASCII apostrophe (U+0027)
        // U+2018 ('), U+2019 ('), U+201B (‛), U+2032 (′)
        normalized = normalized.replace(/[\u2018\u2019\u201B\u2032]/g, "'");

        // Step 4: Replace Unicode double quotes with ASCII double quote (U+0022)
        // U+201C ("), U+201D ("), U+201E („), U+2033 (″)
        normalized = normalized.replace(/[\u201C\u201D\u201E\u2033]/g, '"');

        // Step 5: Clean up any remaining problematic characters
        // Replace non-printable control characters (except newlines and tabs)
        normalized = normalized.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '');

        // Step 6: Normalize multiple spaces to single space
        normalized = normalized.replace(/\s+/g, ' ');

        return normalized.trim();
    }

    normalizeMeasurement(measurement) {
        /**
         * Normalize measurement units to match valid form choices.
         * This prevents validation errors when LLM generates variations like "tbsp"
         * but form validators only accept exact values like "Tbsp".
         *
         * Valid measurements: gram, ounce, cup, pint, quart, gallon, tsp, Tbsp, pinch, dollop
         *
         * @param {string} measurement - The measurement unit to normalize
         * @returns {string} Normalized measurement unit
         */
        if (!measurement) return measurement;

        // Measurement normalization map - handles common LLM variations
        const measurementMap = {
            // Tablespoon variations
            'tbsp': 'tablespoon',
            'tablespoon': 'tablespoon',
            'tablespoons': 'tablespoon',
            'tbs': 'tablespoon',
            // Teaspoon variations
            'teaspoon': 'teaspoon',
            'teaspoons': 'teaspoon',
            // Weight - Gram variations
            'grams': 'gram',
            'g': 'gram',
            'gr': 'gram',
            // Weight - Ounce variations
            'ounces': 'ounce',
            'oz': 'ounce',
            'oz.': 'ounce',
            // Weight - Pound variations
            'pound': 'pound',
            'pounds': 'pound',
            'lb': 'pound',
            'lbs': 'pound',
            'lbs.': 'pound',
            // Weight - Kilogram variations
            'kilogram': 'kilogram',
            'kilograms': 'kilogram',
            'kg': 'kilogram',
            // Volume - Fluid ounce variations
            'fluid ounce': 'fluid ounce',
            'fluid ounces': 'fluid ounce',
            'fl oz': 'fluid ounce',
            'fl. oz.': 'fluid ounce',
            'fl oz.': 'fluid ounce',
            'floz': 'fluid ounce',
            // Volume - Cup variations
            'cups': 'cup',
            'c': 'cup',
            'c.': 'cup',
            // Volume - Pint variations
            'pints': 'pint',
            'pt': 'pint',
            'pt.': 'pint',
            // Volume - Quart variations
            'quarts': 'quart',
            'qt': 'quart',
            'qt.': 'quart',
            // Volume - Gallon variations
            'gallons': 'gallon',
            'gal': 'gallon',
            'gal.': 'gallon',
            // Volume - Milliliter variations
            'milliliter': 'milliliter',
            'milliliters': 'milliliter',
            'ml': 'milliliter',
            'mL': 'milliliter',
            // Volume - Liter variations
            'liter': 'liter',
            'liters': 'liter',
            'l': 'liter',
            'L': 'liter',
            // Approximate - Pinch variations
            'pinches': 'pinch',
            // Approximate - Dash variations
            'dashes': 'dash',
            // Approximate - Dollop variations
            'dollops': 'dollop',
            // Approximate - Handful variations
            'handfuls': 'handful',
            // Item-based - Clove variations
            'cloves': 'clove',
            // Item-based - Sprig variations
            'sprigs': 'sprig',
            // Item-based - Piece variations
            'pieces': 'piece',
            'pcs': 'piece',
            // Item-based - Slice variations
            'slices': 'slice',
            // Item-based - Whole variations
            'wholes': 'whole',
            // Legacy compatibility (map old abbreviations to new full names)
            'Tbsp': 'tablespoon',
            'tsp': 'teaspoon'
        };

        // Normalize to lowercase for case-insensitive lookup
        const normalized = measurementMap[measurement.toLowerCase()];

        // Return normalized value if found, otherwise return original
        return normalized || measurement;
    }

    generateMeasurementSelect(selectedValue, index) {
        /**
         * Generate a select dropdown for measurement units.
         * This matches the form structure expected by the backend SelectField validation.
         *
         * @param {string} selectedValue - The value to pre-select in the dropdown
         * @param {number} index - The ingredient index for proper form field naming
         * @returns {string} HTML for select dropdown with measurement options
         */
        const measurements = [
            // Weight measurements
            'gram', 'ounce', 'pound', 'kilogram',
            // Volume measurements
            'teaspoon', 'tablespoon', 'fluid ounce', 'cup', 'pint', 'quart', 'gallon', 'milliliter', 'liter',
            // Abbreviations (kept for compatibility)
            'tsp', 'Tbsp',
            // Approximate/colloquial measurements
            'pinch', 'dash', 'dollop', 'handful',
            // Item-based measurements
            'clove', 'sprig', 'piece', 'slice', 'whole'
        ];

        // Normalize the selected value to ensure it matches a valid option
        const normalized = this.normalizeMeasurement(selectedValue);

        return `
            <select class="form-control" name="ingredients-${index}-measurement" required>
                ${measurements.map(m =>
                    `<option value="${m}" ${m === normalized ? 'selected' : ''}>${m}</option>`
                ).join('')}
            </select>
        `;
    }

    populateRecipeDropdown() {
        const dropdown = document.getElementById('recipe-dropdown');
        if (!dropdown) return;

        // Clear existing options except the first one
        while (dropdown.children.length > 1) {
            dropdown.removeChild(dropdown.lastChild);
        }

        // Add recipes
        this.recipesData.forEach(recipe => {
            if (!recipe.recipe_id || !recipe.recipe_name) return;
            const option = document.createElement('option');
            option.value = recipe.recipe_id;
            option.textContent = recipe.recipe_name;
            dropdown.appendChild(option);
        });
    }

    createSearchableRecipeDropdown() {
        const modifyOptions = document.getElementById('modify-recipe-options');
        const recipeDropdown = document.getElementById('recipe-dropdown');

        if (!modifyOptions || !recipeDropdown) return;

        // Check if already converted to searchable
        if (document.getElementById('recipe-search-input')) {
            return; // Already converted
        }

        // Replace select with searchable input + dropdown
        const searchContainer = document.createElement('div');
        searchContainer.className = 'recipe-search-container position-relative';
        searchContainer.innerHTML = `
            <input type="text" class="form-control" id="recipe-search-input"
                   placeholder="Search recipes..." autocomplete="off"
                   aria-label="Search for recipes">
            <div class="recipe-search-dropdown hidden" id="recipe-search-dropdown" role="listbox"></div>
            <input type="hidden" id="selected-recipe-id" name="recipe_id">
        `;

        // Replace the select element
        const dropdownContainer = recipeDropdown.parentNode;
        dropdownContainer.replaceChild(searchContainer, recipeDropdown);

        this.setupRecipeSearch();
    }

    setupRecipeSearch() {
        const searchInput = document.getElementById('recipe-search-input');
        const searchDropdown = document.getElementById('recipe-search-dropdown');
        const selectedIdInput = document.getElementById('selected-recipe-id');

        if (!searchInput || !searchDropdown || !selectedIdInput) return;

        // Debounce search input
        let searchTimeout;

        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                const query = e.target.value.toLowerCase();
                this.filterRecipes(query, searchDropdown, selectedIdInput);
            }, 300);
        });

        searchInput.addEventListener('focus', () => {
            this.filterRecipes('', searchDropdown, selectedIdInput);
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
                searchDropdown.classList.add('hidden');
            }
        });

        // Keyboard navigation
        searchInput.addEventListener('keydown', (e) => {
            const items = searchDropdown.querySelectorAll('.recipe-search-item');
            const focusedItem = searchDropdown.querySelector('.recipe-search-item.focused');

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                this.navigateSearchResults(items, focusedItem, 1);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                this.navigateSearchResults(items, focusedItem, -1);
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (focusedItem) {
                    focusedItem.click();
                }
            } else if (e.key === 'Escape') {
                searchDropdown.classList.add('hidden');
            }
        });
    }

    navigateSearchResults(items, focusedItem, direction) {
        if (items.length === 0) return;

        // Remove current focus
        if (focusedItem) {
            focusedItem.classList.remove('focused');
        }

        let newIndex = 0;
        if (focusedItem) {
            const currentIndex = Array.from(items).indexOf(focusedItem);
            newIndex = currentIndex + direction;
        }

        // Wrap around
        if (newIndex < 0) newIndex = items.length - 1;
        if (newIndex >= items.length) newIndex = 0;

        // Focus new item
        items[newIndex].classList.add('focused');
        items[newIndex].scrollIntoView({ block: 'nearest' });
    }

    filterRecipes(query, dropdown, hiddenInput) {
        const filtered = this.recipesData.filter(recipe =>
            recipe.recipe_name && recipe.recipe_name.toLowerCase().includes(query)
        );

        if (filtered.length === 0) {
            dropdown.innerHTML = '<div class="recipe-search-item no-results">No recipes found</div>';
            dropdown.classList.remove('hidden');
            return;
        }

        dropdown.innerHTML = filtered.map(recipe => `
            <div class="recipe-search-item" data-id="${this.escapeHtml(recipe.recipe_id)}" role="option" tabindex="-1">
                <div class="recipe-search-name">${this.escapeHtml(recipe.recipe_name)}</div>
                ${recipe.recipe_description ? `<div class="recipe-search-desc">${this.escapeHtml(recipe.recipe_description)}</div>` : ''}
            </div>
        `).join('');

        dropdown.classList.remove('hidden');

        // Attach click and hover handlers
        dropdown.querySelectorAll('.recipe-search-item').forEach(item => {
            if (!item.classList.contains('no-results')) {
                item.addEventListener('click', () => {
                    const recipeId = item.dataset.id;
                    const recipeName = item.querySelector('.recipe-search-name').textContent;

                    document.getElementById('recipe-search-input').value = recipeName;
                    hiddenInput.value = recipeId;
                    dropdown.classList.add('hidden');
                });

                item.addEventListener('mouseenter', () => {
                    // Remove focus from other items
                    dropdown.querySelectorAll('.recipe-search-item.focused').forEach(focused => {
                        focused.classList.remove('focused');
                    });
                    item.classList.add('focused');
                });
            }
        });
    }

    // === REQUEST HANDLING ===

    async handleCreateRequest() {
        const form = document.getElementById('ai-create-form');
        const createText = document.getElementById('create-text');
        const message = createText?.value.trim();

        // Client-side validation
        if (!message) {
            this.showError('Please enter a recipe description.');
            return;
        }

        // Validate message length (matching server-side validation)
        if (message.length < 2) {
            this.showError('Recipe description must be at least 2 characters');
            return;
        }

        if (message.length > 500) {
            this.showError('Recipe description must be 500 characters or less');
            return;
        }

        try {
            // Validate CSRF token before submission
            if (!this.validateCsrfToken()) {
                throw new Error('CSRF token validation failed. Please refresh the page.');
            }

            // Prepare form data for AJAX submission
            const formData = new FormData(form);

            // Show info notification that AI is processing
            this.showToast('AI is generating your recipe. This may take a moment...', 'info');

            // Make AJAX request to view endpoint
            const response = await fetch('/ai/create', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success && data.recipe) {
                // Show success notification
                this.showToast('Recipe generated successfully!', 'success');
                // Display recipe in modal
                this.displayRecipeInModal(data.recipe, 'create');
            } else if (data.error) {
                this.showToast(data.error, 'error');
                this.showError(data.error);
            } else {
                this.showToast('Failed to generate recipe. Please try again.', 'error');
                this.showError('Failed to generate recipe. Please try again.');
            }

        } catch (error) {
            console.error('Create request failed:', error);
            this.showToast(`Failed to generate recipe: ${error.message}`, 'error');
            this.showError(`Failed to generate recipe: ${error.message}`);
        }
    }

    async handleModifyRequest() {
        const form = document.getElementById('ai-modify-form');
        const recipeIdInput = document.getElementById('selected-recipe-id');
        const modificationText = document.getElementById('modification-text');

        const recipeId = recipeIdInput?.value.trim();
        const message = modificationText?.value.trim();

        // Client-side validation - recipe selection
        if (!recipeId || recipeId === '' || recipeId === 'null') {
            this.showError('Please select a recipe to modify.');
            return;
        }

        // Client-side validation - message presence
        if (!message) {
            this.showError('Please describe your modifications.');
            return;
        }

        // Validate message length (matching server-side validation)
        if (message.length < 2) {
            this.showError('Modification description must be at least 2 characters');
            return;
        }

        if (message.length > 500) {
            this.showError('Modification description must be 500 characters or less');
            return;
        }

        // Validate UUID format (basic check)
        const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
        if (!uuidPattern.test(recipeId)) {
            this.showError('Invalid recipe selected. Please select again.');
            return;
        }

        try {
            // Validate CSRF token before submission
            if (!this.validateCsrfToken()) {
                throw new Error('CSRF token validation failed. Please refresh the page.');
            }

            // Prepare form data for AJAX submission
            const formData = new FormData(form);

            // Show info notification that AI is processing
            this.showToast('AI is modifying your recipe. This may take a moment...', 'info');

            // Make AJAX request to view endpoint
            const response = await fetch('/ai/modify', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success && data.recipe) {
                // Show success notification
                this.showToast('Recipe modified successfully!', 'success');
                // Display recipe in modal
                this.displayRecipeInModal(data.recipe, 'modify', data.recipe_id);
            } else if (data.error) {
                this.showToast(data.error, 'error');
                this.showError(data.error);
            } else {
                this.showToast('Failed to modify recipe. Please try again.', 'error');
                this.showError('Failed to modify recipe. Please try again.');
            }

        } catch (error) {
            console.error('Modify request failed:', error);
            this.showToast(`Failed to modify recipe: ${error.message}`, 'error');
            this.showError(`Failed to modify recipe: ${error.message}`);
        }
    }

    /**
     * Display AI-generated recipe in modal for review before saving.
     *
     * @param {Object} recipeData - Parsed recipe data from API
     * @param {string} workflow - Either 'create' or 'modify'
     * @param {string|null} recipeId - Recipe ID (for modify workflow only)
     */
    displayRecipeInModal(recipeData, workflow, recipeId = null) {
        try {
            // Load category data before generating form
            this.loadCategoryData();

            // Generate form HTML with recipe data
            this.generateRecipeForm(recipeData);

            // Set form action to always use /recipe/create (both create and modify workflows)
            const form = document.getElementById('ai-recipe-form');
            if (form) {
                form.action = '/recipe/create';
            }

            // Setup category toggle functionality
            this.setupCategoryToggle();

            // Show the modal
            this.showRecipeModal();

            // Close the AI dropdown
            this.close();

        } catch (error) {
            console.error('Failed to display recipe in modal:', error);
            this.showError('Failed to display recipe. Please try again.');
        }
    }

    /**
     * DEPRECATED: This function is no longer used after converting to native form submission.
     * Kept for backward compatibility with API endpoints if needed.
     * Forms now submit natively and server handles responses via redirects/flash messages.
     */
    async handleResponse(resp) {
        if (!resp || !resp.response || resp.response.error) {
            this.showError(resp?.response?.error || 'An error occurred');
            return;
        }

        try {
            const recipeData = this.parseRecipeResponse(resp.response.recipe);
            this.displayRecipePreview(resp.response.recipe);
            this.showResultSection();

            // Store parsed data for form generation
            this.currentRecipeData = recipeData;
        } catch (error) {
            console.error('Failed to parse recipe response:', error);
            this.showError('Failed to parse AI response. Please try again.');
        }
    }

    displayRecipePreview(recipeText) {
        const recipeContent = document.getElementById('ai-recipe-content');
        if (recipeContent) {
            recipeContent.textContent = recipeText;
        }
    }

    async handleSaveRecipe() {
        if (!this.currentRecipeData) {
            this.showError('No recipe data available to save.');
            return;
        }

        try {
            this.generateRecipeForm(this.currentRecipeData);
            this.showRecipeModal();
            this.close(); // Close dropdown
        } catch (error) {
            console.error('Failed to generate recipe form:', error);
            this.showError('Failed to generate recipe form. Please try again.');
        }
    }

    // === RECIPE PARSING ===

    parseRecipeResponse(recipeText) {
        // Input validation for security
        if (!recipeText || typeof recipeText !== 'string') {
            throw new Error('Invalid recipe text input');
        }

        // Limit maximum text length to prevent DoS attacks
        const maxLength = 50000; // 50KB limit
        if (recipeText.length > maxLength) {
            throw new Error('Recipe text exceeds maximum allowed length');
        }

        // Basic content filtering for malicious patterns
        const dangerousPatterns = /<script|javascript:|data:|vbscript:|onload=|onerror=/i;
        if (dangerousPatterns.test(recipeText)) {
            throw new Error('Recipe text contains potentially malicious content');
        }

        const lines = recipeText.split('\n').filter(line => line.trim());
        const recipe = {
            name: '',
            description: '',
            ingredients: [],
            steps: [],
            category: ''
        };

        let currentSection = '';

        for (const line of lines) {
            const trimmed = line.trim();

            if (this.isRecipeName(trimmed)) {
                recipe.name = this.extractValue(trimmed);
            } else if (this.isDescription(trimmed)) {
                recipe.description = this.extractValue(trimmed);
            } else if (this.isIngredientsSection(trimmed)) {
                currentSection = 'ingredients';
            } else if (this.isInstructionsSection(trimmed)) {
                currentSection = 'steps';
            } else if (currentSection === 'ingredients' && this.isIngredient(trimmed)) {
                const ingredient = this.parseIngredient(trimmed);
                if (ingredient) recipe.ingredients.push(ingredient);
            } else if (currentSection === 'steps' && this.isStep(trimmed)) {
                const step = this.parseStep(trimmed);
                if (step) recipe.steps.push(step);
            }
        }

        return recipe;
    }

    isRecipeName(line) {
        return line.toLowerCase().includes('recipe name:') ||
               line.toLowerCase().includes('title:') ||
               line.toLowerCase().includes('name:');
    }

    isDescription(line) {
        return line.toLowerCase().includes('description:');
    }

    isIngredientsSection(line) {
        return line.toLowerCase().includes('ingredients:');
    }

    isInstructionsSection(line) {
        return line.toLowerCase().includes('instructions:') ||
               line.toLowerCase().includes('steps:') ||
               line.toLowerCase().includes('directions:');
    }

    isIngredient(line) {
        return line.match(/^[-*•]|\d+\./) && !this.isStep(line);
    }

    isStep(line) {
        return line.match(/^\d+\./);
    }

    extractValue(line) {
        if (!line || typeof line !== 'string') return '';
        // Limit extracted value length
        const value = line.split(':').slice(1).join(':').trim();
        return value.length > 1000 ? value.substring(0, 1000) : value;
    }

    parseIngredient(text) {
        if (!text || typeof text !== 'string') return null;
        // Limit ingredient text length
        if (text.length > 500) return null;

        const cleaned = text.replace(/^[-*•]\s*|\d+\.\s*/, '').trim();
        const match = cleaned.match(/^(\d+(?:\/\d+)?(?:\.\d+)?)\s*(\w+)?\s+(.+)$/);

        if (match) {
            return {
                quantity: (match[1] || '').substring(0, 50), // Limit quantity length
                measurement: (match[2] || '').substring(0, 50), // Limit measurement length
                name: (match[3] || cleaned).substring(0, 200) // Limit ingredient name length
            };
        }

        return {
            quantity: '',
            measurement: '',
            name: cleaned.substring(0, 200)
        };
    }

    parseStep(text) {
        if (!text || typeof text !== 'string') return '';
        // Limit step text length
        const step = text.replace(/^\d+\.\s*/, '').trim();
        return step.length > 1000 ? step.substring(0, 1000) : step;
    }

    // === RECIPE FORM GENERATION ===

    generateRecipeForm(recipeData) {
        const formContainer = document.getElementById('ai-recipe-form');
        if (!formContainer) return;

        const csrfToken = this.getCsrfToken();

        const formHTML = `
            <input type="hidden" name="csrf_token" value="${csrfToken}">

            <fieldset>
                <div class="form-group mb-4">
                    <label for="ai-recipe-name" class="form-label">Recipe Name</label>
                    <input type="text" class="form-control" id="ai-recipe-name" name="recipe-name"
                           value="${this.escapeHtml(this.normalizeText(recipeData.name))}" required>
                </div>

                <div class="form-group mb-4">
                    <label for="ai-recipe-description" class="form-label">Description</label>
                    <textarea class="form-control" id="ai-recipe-description" name="description"
                              rows="3">${this.escapeHtml(recipeData.description)}</textarea>
                </div>

                <div class="form-group mb-4">
                    <label for="ai-recipe-image" class="form-label">Image</label>
                    <input type="file" class="form-control" id="ai-recipe-image" name="image" accept="image/png, image/jpeg">
                </div>

                <div id="ai-category-forms-container">
                    <div id="ai-category-selector-container" class="form-group mb-4">
                        <label for="ai-recipe-category" class="form-label">Category</label>
                        <select class="form-control" id="ai-recipe-category" name="category-selector" required>
                            <option value="">Select a category</option>
                            ${this.generateCategoryOptionsFromBackend()}
                        </select>
                        <button type="button" id="ai-show-add-category-btn" class="btn btn-coral mt-3">
                            <i class="fa-solid fa-plus mr-2"></i>Create Category
                        </button>
                    </div>
                    <div id="ai-add-category-form-container" class="w-full mx-0 my-6 justify-between hidden">
                        <div class="form-group w-full">
                            <label for="ai-category-name" class="form-label">Category Name</label>
                            <input type="text" class="form-control" id="ai-category-name" name="category-name"
                                   minlength="2" maxlength="50" pattern="^[a-zA-Z0-9_' -]+$">
                        </div>
                        <div class="flex justify-start items-center mt-4 w-1/2">
                            <button type="button" id="ai-cancel-add-category-btn" class="btn btn-danger btn-base">
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>

                <fieldset class="mb-4">
                    <legend>Ingredients</legend>
                    <ul id="ai-ingredients-list" class="space-y-3">
                        ${recipeData.ingredients.map((ing, index) => this.generateIngredientHTML(ing, index)).join('')}
                    </ul>
                    <div class="flex justify-end mt-3">
                        <button type="button" class="btn btn-coral" id="ai-add-ingredient-btn">
                            <i class="fa-solid fa-plus mr-2"></i>Add Ingredient
                        </button>
                    </div>
                </fieldset>

                <fieldset class="mb-4">
                    <legend>Instructions</legend>
                    <ol id="ai-steps-list" class="space-y-3">
                        ${recipeData.steps.map((step, index) => this.generateStepHTML(step, index)).join('')}
                    </ol>
                    <div class="flex justify-end mt-3">
                        <button type="button" class="btn btn-coral" id="ai-add-step-btn">
                            <i class="fa-solid fa-plus mr-2"></i>Add Step
                        </button>
                    </div>
                </fieldset>
            </fieldset>
        `;

        formContainer.innerHTML = formHTML;
        this.attachFormEventListeners();
    }

    generateCategoryOptions() {
        // Common recipe categories - this could be loaded from the server
        const categories = [
            'Appetizers', 'Beverages', 'Bread', 'Breakfast', 'Desserts',
            'Main Courses', 'Salads', 'Sides', 'Snacks', 'Soups'
        ];

        return categories.map(cat =>
            `<option value="${cat}">${cat}</option>`
        ).join('');
    }

    generateCategoryOptionsFromBackend() {
        // Load categories from backend data
        if (!this.categoriesData || this.categoriesData.length === 0) {
            return '';
        }

        return this.categoriesData.map(cat =>
            `<option value="${this.escapeHtml(cat.category_id)}">${this.escapeHtml(cat.category_name)}</option>`
        ).join('');
    }

    generateIngredientHTML(ingredient, index) {
        return `
            <li class="ingredient-item p-4 rounded-lg">
                <div class="flex justify-between px-0 w-full">

                    <div class="form-group mr-3">
                        <label class="form-label">Quantity</label>
                        <input type="text" class="form-control" name="ingredients-${index}-quantity"
                               value="${this.escapeHtml(ingredient.quantity)}">
                    </div>

                    <div class="form-group mr-3">
                        <label class="form-label">Measurement</label>
                        ${this.generateMeasurementSelect(ingredient.measurement, index)}
                    </div>

                    <div class="form-group flex-1 mr-3">
                        <label class="form-label">Ingredient</label>
                        <input type="text" class="form-control" name="ingredients-${index}-ingredient_name"
                               value="${this.escapeHtml(this.normalizeText(ingredient.name))}" required>
                    </div>

                    <div class="flex items-end">
                        <button type="button" class="btn btn-danger btn-sm delete-ingredient-btn">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>
                </div>
            </li>
        `;
    }

    generateStepHTML(step, index) {
        return `
            <li class="step-item p-4 rounded-lg">
                <div class="flex justify-between px-0 w-full items-center">

                    <div class="form-group flex-1 mr-3">
                        <label class="form-label ai-step-label">Step ${index + 1}</label>
                        <textarea class="form-control" name="steps-${index}-step"
                                  rows="2" required>${this.escapeHtml(this.normalizeText(step))}</textarea>
                    </div>

                    <div class="flex items-end">
                        <button type="button" class="btn btn-danger btn-sm delete-step-btn">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>
                </div>
            </li>
        `;
    }

    attachFormEventListeners() {
        // Add ingredient functionality
        document.getElementById('ai-add-ingredient-btn')?.addEventListener('click', () => {
            this.addIngredientToForm();
        });

        // Add step functionality
        document.getElementById('ai-add-step-btn')?.addEventListener('click', () => {
            this.addStepToForm();
        });

        // Delete buttons
        document.addEventListener('click', (e) => {
            if (e.target.closest('.delete-ingredient-btn')) {
                e.target.closest('.ingredient-item').remove();
                this.reindexIngredients();
            } else if (e.target.closest('.delete-step-btn')) {
                e.target.closest('.step-item').remove();
                this.reindexSteps();
            }
        });
    }

    setupCategoryToggle() {
        const showBtn = document.getElementById('ai-show-add-category-btn');
        const cancelBtn = document.getElementById('ai-cancel-add-category-btn');
        const selectorContainer = document.getElementById('ai-category-selector-container');
        const formContainer = document.getElementById('ai-add-category-form-container');
        const categoryNameInput = document.getElementById('ai-category-name');
        const categorySelect = document.getElementById('ai-recipe-category');

        // Set initial state: show selector, hide form
        if (selectorContainer) selectorContainer.classList.remove('hidden');
        if (formContainer) formContainer.classList.add('hidden');

        if (showBtn) {
            showBtn.addEventListener('click', () => {
                // Remove required from select (it's hidden, can't be focused)
                if (categorySelect) categorySelect.removeAttribute('required');
                // Add required to category name input (now visible)
                if (categoryNameInput) categoryNameInput.setAttribute('required', '');
                if (selectorContainer) selectorContainer.classList.add('hidden');
                if (formContainer) formContainer.classList.remove('hidden');
            });
        }

        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                if (formContainer) {
                    formContainer.classList.add('hidden');
                    if (categoryNameInput) {
                        categoryNameInput.value = '';
                        categoryNameInput.removeAttribute('required');
                    }
                }
                if (selectorContainer) selectorContainer.classList.remove('hidden');
                // Restore required on select (now visible again)
                if (categorySelect) categorySelect.setAttribute('required', '');
            });
        }
    }

    addIngredientToForm() {
        const ingredientsList = document.getElementById('ai-ingredients-list');
        if (!ingredientsList) return;

        const index = ingredientsList.children.length;
        const newIngredient = {
            quantity: '',
            measurement: '',
            name: ''
        };

        const ingredientHTML = this.generateIngredientHTML(newIngredient, index);
        ingredientsList.insertAdjacentHTML('beforeend', ingredientHTML);
    }

    addStepToForm() {
        const stepsList = document.getElementById('ai-steps-list');
        if (!stepsList) return;

        const index = stepsList.children.length;
        const stepHTML = this.generateStepHTML('', index);
        stepsList.insertAdjacentHTML('beforeend', stepHTML);
    }

    reindexIngredients() {
        const ingredients = document.querySelectorAll('.ingredient-item');
        ingredients.forEach((ingredient, index) => {
            const inputs = ingredient.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                const name = input.name;
                if (name && name.includes('ingredients-')) {
                    const newName = name.replace(/ingredients-\d+-/, `ingredients-${index}-`);
                    input.name = newName;
                }
            });
        });
    }

    reindexSteps() {
        const steps = document.querySelectorAll('.step-item');
        steps.forEach((step, index) => {
            const inputs = step.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                const name = input.name;
                if (name && name.includes('steps-')) {
                    const newName = name.replace(/steps-\d+-/, `steps-${index}-`);
                    input.name = newName;
                }
            });

            // Update step label
            const label = step.querySelector('.form-label');
            if (label) {
                label.textContent = `Step ${index + 1}`;
            }
        });
    }

    showRecipeModal() {
        const modal = document.getElementById('ai-recipe-modal');
        const backdrop = document.getElementById('ai-modal-backdrop');
        if (modal) {
            modal.classList.add('show');
            document.body.classList.add('modal-open');
            // Show backdrop
            if (backdrop) {
                backdrop.classList.remove('hidden');
            }
            // Focus first focusable element for accessibility
            const focusable = modal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (focusable.length > 0) focusable[0].focus();
        }
    }

    hideRecipeModal() {
        const modal = document.getElementById('ai-recipe-modal');
        const backdrop = document.getElementById('ai-modal-backdrop');
        if (modal) {
            modal.classList.remove('show');
            document.body.classList.remove('modal-open');
            // Hide backdrop
            if (backdrop) {
                backdrop.classList.add('hidden');
            }
        }
    }

    // === UTILITY FUNCTIONS ===

    /**
     * DEPRECATED: Loading state management no longer needed with native form submission.
     * Kept for backward compatibility.
     */
    showLoadingState(button, originalText) {
        if (!button) return originalText;

        button.disabled = true;
        button.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status"></span>
            Processing...
        `;
        return originalText;
    }

    /**
     * DEPRECATED: Loading state management no longer needed with native form submission.
     * Kept for backward compatibility.
     */
    hideLoadingState(button, originalText) {
        if (!button || !originalText) return;

        button.disabled = false;
        button.innerHTML = originalText;
    }

    /**
     * DEPRECATED: Direct fetch requests replaced with native form submission.
     * Kept for backward compatibility with API endpoints if needed.
     */
    async makeRequest(url, formData, button) {
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        return data;
    }

    createErrorDisplay() {
        if (!document.getElementById('ai-error-display')) {
            const errorDiv = document.createElement('div');
            errorDiv.id = 'ai-error-display';
            errorDiv.className = 'ai-error-display alert alert-danger hidden';
            this.dropdownMenu?.appendChild(errorDiv);
        }
    }

    showError(message) {
        const errorDisplay = document.getElementById('ai-error-display');
        if (errorDisplay) {
            // Sanitize error message for security
            const sanitizedMessage = this.sanitizeErrorMessage(message);
            errorDisplay.textContent = sanitizedMessage;
            errorDisplay.classList.remove('hidden');

            // Auto-hide after 5 seconds
            setTimeout(() => {
                errorDisplay.classList.add('hidden');
            }, 5000);
        }
    }

    sanitizeErrorMessage(message) {
        if (!message || typeof message !== 'string') {
            return 'An error occurred. Please try again.';
        }

        // Limit message length to prevent DoS
        const maxLength = 500;
        let sanitized = message.length > maxLength ? message.substring(0, maxLength) + '...' : message;

        // Remove potentially sensitive information patterns
        const sensitivePatterns = [
            /\/[a-zA-Z0-9_\-\/]+\.(js|html|php|py|rb|java)/g, // File paths
            /\b(?:\d{1,3}\.){3}\d{1,3}\b/g, // IP addresses
            /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, // Email addresses
            /password[:\s=]+[^\s]+/gi, // Password patterns
            /token[:\s=]+[^\s]+/gi, // Token patterns
            /key[:\s=]+[^\s]+/gi, // API key patterns
            /sql[:\s].+/gi, // SQL fragments
            /stack trace|traceback/gi // Stack trace indicators
        ];

        sensitivePatterns.forEach(pattern => {
            sanitized = sanitized.replace(pattern, '[REDACTED]');
        });

        // Generic error messages for common server errors to prevent information disclosure
        const genericErrors = {
            '500': 'Internal server error. Please try again later.',
            '503': 'Service temporarily unavailable. Please try again later.',
            '502': 'Service temporarily unavailable. Please try again later.',
            '404': 'The requested resource was not found.',
            '403': 'Access denied.',
            '401': 'Authentication required.',
            '400': 'Invalid request. Please check your input.'
        };

        // Check for HTTP error codes and use generic messages
        const httpErrorMatch = sanitized.match(/HTTP (\d{3})/);
        if (httpErrorMatch && genericErrors[httpErrorMatch[1]]) {
            return genericErrors[httpErrorMatch[1]];
        }

        // Escape HTML to prevent XSS in case textContent doesn't work as expected
        sanitized = this.escapeHtml(sanitized);

        return sanitized;
    }

    getCsrfToken() {
        const csrfInput = document.querySelector("input[name$='csrf_token']");
        const token = csrfInput ? csrfInput.value : "";

        // Validate CSRF token exists and is not empty
        if (!token || token.trim() === "") {
            console.warn('CSRF token is missing or empty');
            throw new Error('CSRF token validation failed');
        }

        // Basic token format validation (should be a reasonable length)
        if (token.length < 16) {
            console.warn('CSRF token appears to be invalid (too short)');
            throw new Error('CSRF token validation failed');
        }

        return token;
    }

    validateCsrfToken() {
        try {
            const token = this.getCsrfToken();
            return token && token.length >= 16;
        } catch (error) {
            return false;
        }
    }

    escapeHtml(text) {
        if (typeof text !== 'string') return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Show toast notification for AI processing feedback.
     * @param {string} message - The message to display
     * @param {string} type - The type of toast: 'info', 'success', or 'error'
     */
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        const iconMap = {
            'success': 'fa-check-circle',
            'error': 'fa-exclamation-circle',
            'info': 'fa-circle-info',
            'warning': 'fa-exclamation-triangle'
        };
        toast.innerHTML = `
            <div class="toast-content">
                <i class="fa-solid ${iconMap[type] || 'fa-circle-info'} mr-2"></i>
                <span>${this.escapeHtml(message)}</span>
            </div>
            <div class="toast-progress"></div>
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// Initialize AI Assistant when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AIAssistant();
});