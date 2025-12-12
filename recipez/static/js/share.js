/**
 * Share Recipe Modal System
 * Handles email input, validation, and sending recipe via API
 */

class ShareRecipeManager {
    constructor() {
        this.modal = document.getElementById('shareRecipeModal');
        this.emailInput = document.getElementById('share-email-input');
        this.errorDiv = document.getElementById('share-email-error');
        this.sendBtn = document.getElementById('share-send-btn');
        this.openBtn = document.getElementById('share-recipe-btn');

        this.recipeData = {};
        this.jwtToken = null;

        this.init();
    }

    init() {
        if (!this.modal) return;

        this.loadRecipeData();
        this.loadJwtToken();
        this.setupEmailInput();
        this.setupModalHandlers();
        this.setupSendButton();
    }

    loadRecipeData() {
        if (this.modal) {
            this.recipeData = {
                recipe_name: this.modal.dataset.recipeName || '',
                recipe_description: this.modal.dataset.recipeDescription || '',
                recipe_ingredients: [],
                recipe_steps: [],
                sender_name: this.modal.dataset.senderName || ''
            };

            try {
                this.recipeData.recipe_ingredients = JSON.parse(this.modal.dataset.recipeIngredients || '[]');
            } catch (e) {
                console.warn('Failed to parse recipe ingredients:', e);
            }

            try {
                this.recipeData.recipe_steps = JSON.parse(this.modal.dataset.recipeSteps || '[]');
            } catch (e) {
                console.warn('Failed to parse recipe steps:', e);
            }
        }
    }

    loadJwtToken() {
        if (this.modal && this.modal.dataset.jwt) {
            this.jwtToken = this.modal.dataset.jwt;
        }
    }

    setupEmailInput() {
        if (!this.emailInput) return;

        // Validate on input with debounce
        let inputTimeout;
        this.emailInput.addEventListener('input', () => {
            clearTimeout(inputTimeout);
            inputTimeout = setTimeout(() => {
                this.validateEmail();
            }, 300);
        });

        // Also validate on blur
        this.emailInput.addEventListener('blur', () => {
            this.validateEmail();
        });

        // Enable/disable send button based on input
        this.emailInput.addEventListener('keyup', () => {
            this.updateSendButtonState();
        });

        // Submit on Enter key
        this.emailInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !this.sendBtn.disabled) {
                e.preventDefault();
                this.sendBtn.click();
            }
        });
    }

    validateEmail() {
        const email = this.emailInput.value.trim();
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!email) {
            this.showError('');
            return false;
        }

        if (!emailRegex.test(email)) {
            this.showError('Please enter a valid email address');
            return false;
        }

        this.showError('');
        return true;
    }

    showError(message) {
        if (this.errorDiv) {
            if (message) {
                this.errorDiv.textContent = message;
                this.errorDiv.classList.remove('hidden');
                this.emailInput.classList.add('border-red-500');
            } else {
                this.errorDiv.textContent = '';
                this.errorDiv.classList.add('hidden');
                this.emailInput.classList.remove('border-red-500');
            }
        }
        this.updateSendButtonState();
    }

    updateSendButtonState() {
        if (this.sendBtn && this.emailInput) {
            const email = this.emailInput.value.trim();
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            this.sendBtn.disabled = !email || !emailRegex.test(email);
        }
    }

    setupModalHandlers() {
        // Open modal button
        if (this.openBtn) {
            this.openBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.openModal();
            });
        }

        // Close modal handlers
        if (this.modal) {
            // Click on backdrop
            const backdrop = this.modal.querySelector('.modal-backdrop');
            if (backdrop) {
                backdrop.addEventListener('click', () => this.closeModal());
            }

            // Close buttons
            this.modal.querySelectorAll('.close-modal').forEach(btn => {
                btn.addEventListener('click', () => this.closeModal());
            });

            // Escape key
            this.modal.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') this.closeModal();
            });
        }
    }

    openModal() {
        // Reset state
        if (this.emailInput) this.emailInput.value = '';
        this.showError('');
        this.updateSendButtonState();

        // Show modal
        if (this.modal) {
            this.modal.classList.add('show');
            this.modal.style.display = 'block';
            document.body.style.overflow = 'hidden';
            // Focus email input
            setTimeout(() => this.emailInput?.focus(), 100);
        }
    }

    closeModal() {
        if (this.modal) {
            this.modal.classList.remove('show');
            this.modal.style.display = 'none';
            document.body.style.overflow = '';
        }
    }

    setupSendButton() {
        if (!this.sendBtn) return;

        this.sendBtn.addEventListener('click', async () => {
            if (!this.validateEmail()) return;

            const email = this.emailInput.value.trim();
            const originalText = this.sendBtn.innerHTML;
            this.sendBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i>Sending...';
            this.sendBtn.disabled = true;

            // Format ingredients for API
            const formattedIngredients = this.recipeData.recipe_ingredients.map(ing => ({
                quantity: ing.ingredient_quantity || '',
                measurement: ing.ingredient_measurement || '',
                name: ing.ingredient_name || ''
            }));

            // Format steps for API
            const formattedSteps = this.recipeData.recipe_steps.map(step =>
                step.step_text || step
            );

            try {
                const response = await fetch('/api/email/recipe-share-full', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${this.jwtToken}`
                    },
                    body: JSON.stringify({
                        email: email,
                        recipe_name: this.recipeData.recipe_name,
                        recipe_description: this.recipeData.recipe_description,
                        recipe_ingredients: formattedIngredients,
                        recipe_steps: formattedSteps,
                        sender_name: this.recipeData.sender_name
                    })
                });

                const data = await response.json();

                if (response.ok && data.response) {
                    this.closeModal();
                    this.showNotification('Recipe shared successfully!', 'success');
                } else {
                    throw new Error(data.error || 'Failed to share recipe');
                }
            } catch (error) {
                console.error('Share recipe error:', error);
                this.showNotification(error.message || 'Failed to share recipe', 'error');
            } finally {
                this.sendBtn.innerHTML = originalText;
                this.updateSendButtonState();
            }
        });
    }

    showNotification(message, type) {
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

    escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    new ShareRecipeManager();
});
