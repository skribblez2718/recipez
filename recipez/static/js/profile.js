/**
 * Profile page functionality - API key copy handler
 */
document.getElementById('copy-key')?.addEventListener('click', async () => {
  const keyInput = document.getElementById('api-key');
  const key = keyInput?.value;

  if (!key) {
    console.error('No API key to copy');
    return;
  }

  try {
    // Try modern clipboard API first
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(key);
      console.log('API key copied to clipboard');

      // Visual feedback
      const button = document.getElementById('copy-key');
      const originalText = button.textContent;
      button.textContent = 'Copied!';
      setTimeout(() => {
        button.textContent = originalText;
      }, 2000);
    } else {
      // Fallback for older browsers
      keyInput.type = 'text';
      keyInput.select();
      document.execCommand('copy');
      keyInput.type = 'password';
      console.log('API key copied to clipboard (fallback)');

      // Visual feedback
      const button = document.getElementById('copy-key');
      const originalText = button.textContent;
      button.textContent = 'Copied!';
      setTimeout(() => {
        button.textContent = originalText;
      }, 2000);
    }
  } catch (err) {
    console.error('Failed to copy API key:', err);
    alert('Failed to copy API key to clipboard');
  }
});
