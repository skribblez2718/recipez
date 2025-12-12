// Reusable modal logic for confirmation dialogs
// Usage: showModal({modalId, confirmBtnId, cancelBtnId, closeBtnId, onConfirm, onCancel, onShow})

function showModal(options) {
    const modal = document.getElementById(options.modalId);
    const confirmBtn = document.getElementById(options.confirmBtnId);
    const cancelBtn = document.getElementById(options.cancelBtnId);
    const closeBtn = document.getElementById(options.closeBtnId);
    let onConfirm = options.onConfirm || function(){};
    let onCancel = options.onCancel || function(){};
    let onShow = options.onShow || function(){};

    // Show modal
    modal.classList.add('show');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('role', 'dialog');
    modal.focus && modal.focus();
    onShow();

    // Theme handling
    function applyModalTheme() {
        const isDark = document.body.classList.contains('dark-mode');
        const modalContent = modal.querySelector('.modal-content');
        if (modalContent) {
            if (isDark) {
                modalContent.classList.add('dark-mode-bg', 'dark-mode-text');
            } else {
                modalContent.classList.remove('dark-mode-bg', 'dark-mode-text');
            }
        }
    }
    applyModalTheme();
    const observer = new MutationObserver(applyModalTheme);
    observer.observe(document.body, { attributes: true, attributeFilter: ['class'] });

    function closeModal() {
        modal.classList.remove('show');
        modal.removeAttribute('aria-modal');
        modal.removeAttribute('role');
        observer.disconnect();
        // Remove event listeners safely
        confirmBtn && confirmBtn.removeEventListener('click', confirmHandler);
        cancelBtn && cancelBtn.removeEventListener('click', cancelHandler);
        closeBtn && closeBtn.removeEventListener('click', closeModalHandler);
        window.removeEventListener('click', outsideHandler);
        document.removeEventListener('keydown', escapeHandler);
        document.body.classList.remove('modal-open');
    }
    function closeModalHandler(e) {
        e.preventDefault();
        closeModal();
    }
    function escapeHandler(e) {
        if (e.key === 'Escape' && modal.classList.contains('show')) {
            closeModal();
        }
    }
    function outsideHandler(e) {
        if (e.target === modal) {
            closeModal();
        }
    }
    // Attach close listeners
    cancelBtn && cancelBtn.addEventListener('click', closeModalHandler);
    closeBtn && closeBtn.addEventListener('click', closeModalHandler);
    window.addEventListener('click', outsideHandler);
    document.addEventListener('keydown', escapeHandler);
    function confirmHandler(e) {
        // For form POST, let the form submit, don't preventDefault
        if (confirmBtn.tagName.toLowerCase() === 'button' && confirmBtn.type === 'submit') {
            closeModal();
            return;
        }
        e.preventDefault();
        closeModal();
        onConfirm();
    }
    function cancelHandler(e) {
        e.preventDefault();
        closeModal();
        onCancel();
    }
    function outsideHandler(e) {
        if (e.target === modal) {
            closeModal();
            onCancel();
        }
    }
    confirmBtn.addEventListener('click', confirmHandler);
    cancelBtn.addEventListener('click', cancelHandler);
    closeBtn.addEventListener('click', closeModal);
    window.addEventListener('click', outsideHandler);
    document.body.classList.add('modal-open');
}

// Generic Delete Modal Initialization for models (category, recipe, ...)
document.addEventListener('DOMContentLoaded', function() {
    // Map model -> config for modal and button IDs
    const modalConfigs = {
        category: {
            deleteBtnId: 'delete-category-btn',
            modalId: 'deleteModal',
            confirmBtnId: 'confirmDeleteBtn',
            cancelBtnId: 'cancelDeleteBtn',
            closeBtnId: 'closeModalBtn',
        },
        recipe: {
            deleteBtnId: 'delete-recipe-btn',
            modalId: 'confirmDeleteModal',
            confirmBtnId: 'confirm-delete-btn',
            cancelBtnId: 'cancelDeleteRecipeBtn',
            closeBtnId: 'closeRecipeModalBtn',
        },
        // Add more models here as needed
    };

    // Detect model from URL path (e.g., /category/update/..., /recipe/update/...)
    const pathParts = window.location.pathname.split('/').filter(Boolean);
    // pathParts[0] = model name (category, recipe, ...)
    const model = pathParts[0];
    const config = modalConfigs[model];
    if (config) {
        var deleteBtn = document.getElementById(config.deleteBtnId);
        var modal = document.getElementById(config.modalId);
        // Skip if modal is a Bootstrap modal (has .modal class) - let Bootstrap handle it
        if (deleteBtn && modal && !modal.classList.contains('modal')) {
            deleteBtn.addEventListener('click', function(e) {
                e.preventDefault();
                showModal({
                    modalId: config.modalId,
                    confirmBtnId: config.confirmBtnId,
                    cancelBtnId: config.cancelBtnId,
                    closeBtnId: config.closeBtnId
                    // No need for onConfirm, form submit will handle
                });
            });
        }
    }
});
