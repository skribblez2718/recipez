/**
 * API Key Management System
 * Handles creation, listing, and deletion of API keys on the profile page
 */

class ApiKeyManager {
    constructor() {
        this.createModal = document.getElementById('createApiKeyModal');
        this.successModal = document.getElementById('apiKeySuccessModal');
        this.revokeModal = document.getElementById('revokeApiKeyModal');
        this.createForm = document.getElementById('create-api-key-form');
        this.jwtToken = document.getElementById('api-key')?.value;
        this.pendingRevokeId = null;
        this.pendingRevokeName = null;

        this.init();
    }

    init() {
        this.setupCreateForm();
        this.setupExpirationToggle();
        this.setupRevokeButtons();
        this.setupCopyButton();
        this.setupSuccessModalClose();
    }

    /**
     * Toggle date picker based on "Never Expires" checkbox
     */
    setupExpirationToggle() {
        const neverExpiresCheckbox = document.getElementById('never-expires');
        const expiresInput = document.getElementById('api-key-expires');

        if (neverExpiresCheckbox && expiresInput) {
            neverExpiresCheckbox.addEventListener('change', (e) => {
                expiresInput.disabled = e.target.checked;
                if (e.target.checked) {
                    expiresInput.value = '';
                }
            });
        }
    }

    /**
     * Handle form submission for creating API keys
     */
    setupCreateForm() {
        if (!this.createForm) return;

        this.createForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.createApiKey();
        });
    }

    /**
     * Create a new API key via the API
     */
    async createApiKey() {
        const submitBtn = document.getElementById('create-api-key-submit');
        const originalHTML = submitBtn.innerHTML;

        try {
            submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i>Creating...';
            submitBtn.disabled = true;

            // Gather form data
            const name = document.getElementById('api-key-name').value.trim();
            const neverExpires = document.getElementById('never-expires').checked;
            const expiresAtValue = document.getElementById('api-key-expires').value;

            // Gather selected scopes
            const scopeCheckboxes = document.querySelectorAll('.scope-checkbox:checked');
            const scopes = Array.from(scopeCheckboxes).map(cb => cb.value);

            // Validate
            if (!name) {
                this.showNotification('Please enter a name for the API key', 'error');
                return;
            }

            if (scopes.length === 0) {
                this.showNotification('Please select at least one permission', 'error');
                return;
            }

            // Prepare expiration
            let expiresAt = null;
            if (!neverExpires && expiresAtValue) {
                // Convert date to ISO string with time set to end of day
                expiresAt = new Date(expiresAtValue + 'T23:59:59').toISOString();
            }

            const response = await fetch('/api/profile/api-keys', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.jwtToken}`
                },
                body: JSON.stringify({
                    name: name,
                    scopes: scopes,
                    never_expires: neverExpires,
                    expires_at: expiresAt
                })
            });

            const data = await response.json();

            if (response.ok && data.response) {
                // Close create modal
                this.closeModal(this.createModal);

                // Show success modal with token
                const tokenInput = document.getElementById('new-api-key-token');
                if (tokenInput) {
                    tokenInput.value = data.response.token;
                }
                this.openModal(this.successModal);

                // Reset form
                this.createForm.reset();
                document.getElementById('never-expires').checked = true;
                document.getElementById('api-key-expires').disabled = true;

            } else {
                throw new Error(data.error || 'Failed to create API key');
            }

        } catch (error) {
            console.error('Create API key error:', error);
            this.showNotification(error.message || 'Failed to create API key', 'error');
        } finally {
            submitBtn.innerHTML = originalHTML;
            submitBtn.disabled = false;
        }
    }

    /**
     * Setup delete button event handlers
     */
    setupRevokeButtons() {
        document.querySelectorAll('.revoke-api-key-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.pendingRevokeId = btn.dataset.apiKeyId;
                this.pendingRevokeName = btn.dataset.apiKeyName;
                this.openModal(this.revokeModal);
            });
        });

        // Confirm delete button
        const confirmBtn = document.getElementById('confirm-revoke-btn');
        if (confirmBtn) {
            confirmBtn.addEventListener('click', async () => {
                await this.deleteApiKey();
            });
        }
    }

    /**
     * Delete an API key via the API
     */
    async deleteApiKey() {
        if (!this.pendingRevokeId) return;

        const confirmBtn = document.getElementById('confirm-revoke-btn');
        const originalHTML = confirmBtn.innerHTML;

        try {
            confirmBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i>Deleting...';
            confirmBtn.disabled = true;

            const response = await fetch(`/api/profile/api-keys/${this.pendingRevokeId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${this.jwtToken}`
                }
            });

            const data = await response.json();

            if (response.ok) {
                this.closeModal(this.revokeModal);
                this.showNotification(`API key "${this.pendingRevokeName}" deleted`, 'success');

                // Remove the key element from the DOM
                const keyElement = document.querySelector(`[data-api-key-id="${this.pendingRevokeId}"]`);
                if (keyElement) {
                    keyElement.remove();

                    // Check if there are any remaining keys
                    const keysList = document.getElementById('api-keys-list');
                    if (keysList && keysList.children.length === 0) {
                        // Show "no keys" message
                        const noKeysMsg = document.createElement('p');
                        noKeysMsg.className = 'text-[color:var(--text-secondary)] mb-4';
                        noKeysMsg.id = 'no-api-keys-message';
                        noKeysMsg.textContent = "You haven't created any API keys yet.";
                        keysList.parentNode.insertBefore(noKeysMsg, keysList);
                        keysList.remove();
                    }
                }
            } else {
                throw new Error(data.error || 'Failed to delete API key');
            }

        } catch (error) {
            console.error('Delete API key error:', error);
            this.showNotification(error.message || 'Failed to delete API key', 'error');
        } finally {
            confirmBtn.innerHTML = originalHTML;
            confirmBtn.disabled = false;
            this.pendingRevokeId = null;
            this.pendingRevokeName = null;
        }
    }

    /**
     * Setup copy to clipboard functionality for new API key
     */
    setupCopyButton() {
        const copyBtn = document.getElementById('copy-new-api-key');
        if (!copyBtn) return;

        copyBtn.addEventListener('click', async () => {
            const tokenInput = document.getElementById('new-api-key-token');
            const statusEl = document.getElementById('copy-status');

            if (!tokenInput || !tokenInput.value) return;

            try {
                await navigator.clipboard.writeText(tokenInput.value);
                statusEl.textContent = 'Copied to clipboard!';
                statusEl.className = 'text-xs text-green-500';
                copyBtn.innerHTML = '<i class="fa-solid fa-check mr-2"></i>Copied!';

                setTimeout(() => {
                    copyBtn.innerHTML = '<i class="fa-solid fa-copy mr-2"></i>Copy to Clipboard';
                }, 2000);
            } catch (err) {
                // Fallback for older browsers
                tokenInput.select();
                document.execCommand('copy');
                statusEl.textContent = 'Copied to clipboard!';
                statusEl.className = 'text-xs text-green-500';
            }
        });
    }

    /**
     * Setup success modal close handler to refresh page
     */
    setupSuccessModalClose() {
        if (this.successModal) {
            const closeBtn = document.getElementById('close-success-modal');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => {
                    window.location.reload();
                });
            }

            // Also handle backdrop click and close button
            const closeModalBtns = this.successModal.querySelectorAll('.close-modal');
            closeModalBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    window.location.reload();
                });
            });

            const backdrop = this.successModal.querySelector('.modal-backdrop');
            if (backdrop) {
                backdrop.addEventListener('click', () => {
                    window.location.reload();
                });
            }
        }
    }

    /**
     * Open a modal
     */
    openModal(modal) {
        if (modal) {
            modal.classList.add('show');
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden';
        }
    }

    /**
     * Close a modal
     */
    closeModal(modal) {
        if (modal) {
            modal.classList.remove('show');
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }
    }

    /**
     * Show a toast notification
     */
    showNotification(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        const iconMap = {
            'success': 'fa-check-circle',
            'error': 'fa-exclamation-circle',
            'info': 'fa-circle-info',
            'warning': 'fa-exclamation-triangle'
        };

        const bgMap = {
            'success': 'bg-green-600',
            'error': 'bg-red-600',
            'info': 'bg-blue-600',
            'warning': 'bg-yellow-600'
        };

        toast.innerHTML = `
            <div class="fixed bottom-4 right-4 ${bgMap[type]} text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 z-50 animate-pulse">
                <i class="fa-solid ${iconMap[type] || 'fa-circle-info'}"></i>
                <span>${this.escapeHtml(message)}</span>
            </div>
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s ease-out';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    new ApiKeyManager();
});
