/**
 * Grocery List Modal System
 * Searchable multi-select dropdown with pill-style selection display
 */

class GroceryListManager {
    constructor() {
        this.modal = document.getElementById('grocery-modal');
        this.searchInput = document.getElementById('grocery-recipe-search');
        this.dropdown = document.getElementById('grocery-recipe-dropdown');
        this.pillsContainer = document.getElementById('grocery-pills-container');
        this.sendBtn = document.getElementById('grocery-send-btn');
        this.noSelectionText = document.getElementById('grocery-no-selection');
        this.openBtn = document.getElementById('grocery-list-btn');

        this.recipesData = [];
        this.selectedRecipes = new Map(); // recipe_id -> recipe_name
        this.jwtToken = null;

        this.init();
    }

    init() {
        if (!this.modal) return;

        this.loadRecipeData();
        this.loadJwtToken();
        this.setupSearchInput();
        this.setupModalHandlers();
        this.setupSendButton();
    }

    loadRecipeData() {
        // Get recipes from data attribute on the grocery modal
        if (this.modal && this.modal.dataset.recipes) {
            try {
                this.recipesData = JSON.parse(this.modal.dataset.recipes);
            } catch (e) {
                console.warn('Failed to parse recipes data from grocery-modal:', e);
                this.recipesData = [];
            }
        }
    }

    loadJwtToken() {
        // Get JWT token from data attribute on the grocery modal
        if (this.modal && this.modal.dataset.jwt) {
            this.jwtToken = this.modal.dataset.jwt;
        }
    }

    setupSearchInput() {
        if (!this.searchInput || !this.dropdown) return;

        let searchTimeout;

        // Show dropdown on focus
        this.searchInput.addEventListener('focus', () => {
            this.filterRecipes('');
        });

        // Filter on input with debounce
        this.searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.filterRecipes(e.target.value.toLowerCase());
            }, 200);
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.searchInput.contains(e.target) && !this.dropdown.contains(e.target)) {
                this.dropdown.classList.add('hidden');
            }
        });

        // Keyboard navigation
        this.searchInput.addEventListener('keydown', (e) => {
            this.handleKeyboardNavigation(e);
        });
    }

    filterRecipes(query) {
        const filtered = this.recipesData.filter(recipe => {
            // Exclude already selected recipes
            if (this.selectedRecipes.has(recipe.recipe_id)) return false;
            // Filter by query
            return recipe.recipe_name && recipe.recipe_name.toLowerCase().includes(query);
        });

        if (filtered.length === 0) {
            this.dropdown.innerHTML = '<div class="recipe-search-item no-results">No recipes found</div>';
        } else {
            this.dropdown.innerHTML = filtered.map(recipe => `
                <div class="recipe-search-item"
                     data-id="${this.escapeHtml(recipe.recipe_id)}"
                     data-name="${this.escapeHtml(recipe.recipe_name)}"
                     role="option"
                     tabindex="-1">
                    <div class="recipe-search-name">${this.escapeHtml(recipe.recipe_name)}</div>
                </div>
            `).join('');

            // Attach click handlers
            this.dropdown.querySelectorAll('.recipe-search-item:not(.no-results)').forEach(item => {
                item.addEventListener('click', () => this.selectRecipe(item));
                item.addEventListener('mouseenter', () => {
                    this.dropdown.querySelectorAll('.recipe-search-item.focused').forEach(f => f.classList.remove('focused'));
                    item.classList.add('focused');
                });
            });
        }

        this.dropdown.classList.remove('hidden');
    }

    selectRecipe(item) {
        const id = item.dataset.id;
        const name = item.dataset.name;

        if (!this.selectedRecipes.has(id)) {
            this.selectedRecipes.set(id, name);
            this.updatePillsDisplay();
            this.updateSendButtonState();
        }

        this.searchInput.value = '';
        this.dropdown.classList.add('hidden');
    }

    removeRecipe(id) {
        this.selectedRecipes.delete(id);
        this.updatePillsDisplay();
        this.updateSendButtonState();
    }

    updatePillsDisplay() {
        if (this.selectedRecipes.size === 0) {
            this.pillsContainer.innerHTML = '<p class="text-gray-500 text-sm" id="grocery-no-selection">No recipes selected</p>';
        } else {
            const pills = Array.from(this.selectedRecipes.entries()).map(([id, name]) => `
                <span class="recipe-pill" data-id="${this.escapeHtml(id)}">
                    ${this.escapeHtml(name)}
                    <button type="button" class="pill-remove" aria-label="Remove ${this.escapeHtml(name)}">
                        <i class="fa-solid fa-times"></i>
                    </button>
                </span>
            `).join('');

            this.pillsContainer.innerHTML = pills;

            // Attach remove handlers
            this.pillsContainer.querySelectorAll('.pill-remove').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const pill = e.target.closest('.recipe-pill');
                    if (pill) this.removeRecipe(pill.dataset.id);
                });
            });
        }
    }

    updateSendButtonState() {
        if (this.sendBtn) {
            this.sendBtn.disabled = this.selectedRecipes.size === 0;
        }
    }

    handleKeyboardNavigation(e) {
        const items = this.dropdown.querySelectorAll('.recipe-search-item:not(.no-results)');
        const focusedItem = this.dropdown.querySelector('.recipe-search-item.focused');

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            this.navigateItems(items, focusedItem, 1);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            this.navigateItems(items, focusedItem, -1);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (focusedItem) focusedItem.click();
        } else if (e.key === 'Escape') {
            this.dropdown.classList.add('hidden');
        }
    }

    navigateItems(items, focusedItem, direction) {
        if (items.length === 0) return;

        if (focusedItem) focusedItem.classList.remove('focused');

        let newIndex = 0;
        if (focusedItem) {
            const currentIndex = Array.from(items).indexOf(focusedItem);
            newIndex = currentIndex + direction;
        }

        if (newIndex < 0) newIndex = items.length - 1;
        if (newIndex >= items.length) newIndex = 0;

        items[newIndex].classList.add('focused');
        items[newIndex].scrollIntoView({ block: 'nearest' });
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
        this.selectedRecipes.clear();
        this.updatePillsDisplay();
        this.updateSendButtonState();
        if (this.searchInput) this.searchInput.value = '';
        if (this.dropdown) this.dropdown.classList.add('hidden');

        // Show modal
        if (this.modal) {
            this.modal.classList.add('show');
            this.modal.style.display = 'block';
            document.body.style.overflow = 'hidden';
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
            if (this.selectedRecipes.size === 0) return;

            const originalText = this.sendBtn.innerHTML;
            this.sendBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i>Sending...';
            this.sendBtn.disabled = true;

            // Show info notification that AI is processing
            this.showNotification('AI is organizing your grocery list. This may take a moment...', 'info');

            try {
                const response = await fetch('/api/grocery/send', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${this.jwtToken}`
                    },
                    body: JSON.stringify({
                        recipe_ids: Array.from(this.selectedRecipes.keys())
                    })
                });

                const data = await response.json();

                if (response.ok && data.response) {
                    // Success - close modal and show notification
                    this.closeModal();
                    this.showNotification('Grocery list sent to your email!', 'success');
                } else {
                    throw new Error(data.error || 'Failed to send grocery list');
                }
            } catch (error) {
                console.error('Grocery list error:', error);
                this.showNotification(error.message || 'Failed to send grocery list', 'error');
            } finally {
                this.sendBtn.innerHTML = originalText;
                this.updateSendButtonState();
            }
        });
    }

    showNotification(message, type) {
        // Create toast notification
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

        // Add to document
        document.body.appendChild(toast);

        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 10);

        // Auto-remove after 3 seconds
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
    new GroceryListManager();
});
