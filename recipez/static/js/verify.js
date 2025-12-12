document.addEventListener('DOMContentLoaded', function() {
    // Auto-focus on the first input field when the page loads
    const firstInput = document.getElementById('code1');
    if (firstInput) {
        firstInput.focus();
    }

    // Get all code input fields (use .otp-input class from template)
    const codeInputs = document.querySelectorAll('.otp-input');
    const completeCodeField = document.getElementById('complete-code');

    // Function to update the hidden complete code field
    function updateCompleteCode() {
        const code = Array.from(codeInputs).map(input => input.value).join('');
        const formattedCode = code.substring(0, 4) + '-' + code.substring(4, 8);
        completeCodeField.value = formattedCode;
    }

    // Add event listeners to each input field
    codeInputs.forEach((input, index) => {
        // Auto-navigate to next input when a character is entered
        input.addEventListener('input', function(e) {
            if (input.value.length === 1) {
                // Move to the next input field if not the last one
                if (index < codeInputs.length - 1) {
                    codeInputs[index + 1].focus();
                }
            }
            updateCompleteCode();
        });

        // Handle backspace key to navigate to previous input
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Backspace' && input.value === '' && index > 0) {
                codeInputs[index - 1].focus();
            }
        });
    });

    // Handle paste event on the OTP container
    const otpContainer = document.querySelector('.otp-container');
    if (otpContainer) {
        otpContainer.addEventListener('paste', function(e) {
            e.preventDefault();

            // Get pasted text and clean it
            const pastedText = (e.clipboardData || window.clipboardData).getData('text');
            const cleanedText = pastedText.replace(/[^a-zA-Z0-9]/g, '').substring(0, 8);

            // Distribute characters to input fields
            if (cleanedText.length === 8) {
                for (let i = 0; i < 8 && i < cleanedText.length; i++) {
                    codeInputs[i].value = cleanedText[i];
                }
                updateCompleteCode();
                // Focus on the last field after pasting
                codeInputs[7].focus();
            }
        });
    }
});
