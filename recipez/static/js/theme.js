document.addEventListener('DOMContentLoaded', () => {
    // Get the theme toggle button
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    
    // Check for saved theme preference or use default
    const currentTheme = localStorage.getItem('theme') || 'dark';
    
    // Apply the saved theme or default
    if (currentTheme === 'light') {
        body.classList.remove('theme-dark');
        body.classList.add('light-theme');
        themeToggle.classList.add('light');
    }
    
    // Toggle theme when button is clicked
    themeToggle.addEventListener('click', () => {
        // Toggle light/dark theme classes
        if (body.classList.contains('light-theme')) {
            // Switch to dark theme
            body.classList.remove('light-theme');
            body.classList.add('theme-dark');
            themeToggle.classList.remove('light');
            localStorage.setItem('theme', 'dark');
        } else {
            // Switch to light theme
            body.classList.remove('theme-dark');
            body.classList.add('light-theme');
            themeToggle.classList.add('light');
            localStorage.setItem('theme', 'light');
        }
    });

    // Alert dismiss buttons (CSP-compliant replacement for inline onclick)
    document.querySelectorAll('.alert-dismiss-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const alert = this.closest('.alert');
            if (alert) {
                alert.classList.add('fade-out');
                setTimeout(() => alert.remove(), 300);
            }
        });
    });

    // Auto-dismiss alerts after timeout with progress bar
    document.querySelectorAll('[data-auto-dismiss]').forEach(alert => {
        const timeout = parseInt(alert.getAttribute('data-auto-dismiss'), 10) || 5000;

        // Add progress bar
        const progressBar = document.createElement('div');
        progressBar.className = 'alert-progress';
        progressBar.style.animationDuration = `${timeout}ms`;
        alert.appendChild(progressBar);

        // Auto-dismiss after timeout
        setTimeout(() => {
            alert.classList.add('fade-out');
            setTimeout(() => alert.remove(), 300);
        }, timeout);
    });
});
