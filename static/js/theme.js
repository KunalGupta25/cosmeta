// Theme handling script
document.addEventListener('DOMContentLoaded', function() {
    // Check for system theme preference
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Function to set theme based on preference
    function setTheme(theme) {
        const htmlElement = document.documentElement;
        
        if (theme === 'system') {
            // Apply system preference
            if (prefersDarkScheme.matches) {
                htmlElement.setAttribute('data-theme', 'system');
                htmlElement.classList.add('dark-mode');
                htmlElement.classList.remove('light-mode');
            } else {
                htmlElement.setAttribute('data-theme', 'system');
                htmlElement.classList.add('light-mode');
                htmlElement.classList.remove('dark-mode');
            }
        } else {
            // Apply specific theme
            htmlElement.setAttribute('data-theme', theme);
            if (theme === 'dark') {
                htmlElement.classList.add('dark-mode');
                htmlElement.classList.remove('light-mode');
            } else {
                htmlElement.classList.add('light-mode');
                htmlElement.classList.remove('dark-mode');
            }
        }
    }
    
    // Get current theme
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'system';
    
    // Apply current theme
    setTheme(currentTheme);
    
    // Listen for system preference changes
    prefersDarkScheme.addEventListener('change', function(e) {
        if (document.documentElement.getAttribute('data-theme') === 'system') {
            setTheme('system');
        }
    });
    
    // Theme option handling in profile page
    const themeOptions = document.querySelectorAll('.theme-option');
    if (themeOptions.length > 0) {
        themeOptions.forEach(option => {
            option.addEventListener('click', function() {
                const theme = this.getAttribute('data-theme');
                setTheme(theme);
            });
        });
    }
});