// Main JavaScript file for Cosmeta: Incarnate

document.addEventListener('DOMContentLoaded', function() {
    // Flash message close button functionality
    const closeButtons = document.querySelectorAll('.flash-message .close-btn');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const flashMessage = this.parentElement;
            flashMessage.style.opacity = '0';
            setTimeout(() => {
                flashMessage.style.display = 'none';
            }, 300);
        });
    });

    // Auto-hide flash messages after 5 seconds
    setTimeout(() => {
        const flashMessages = document.querySelectorAll('.flash-message');
        flashMessages.forEach(message => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.style.display = 'none';
            }, 300);
        });
    }, 5000);

    // Add current year to footer copyright
    const copyrightYear = document.querySelector('.copyright p');
    if (copyrightYear) {
        const year = new Date().getFullYear();
        copyrightYear.innerHTML = copyrightYear.innerHTML.replace('{{ now.year }}', year);
    }

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth'
                    });
                }
            }
        });
    });

    // Mobile navigation toggle
    const navToggle = document.querySelector('.nav-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (navToggle && navLinks) {
        navToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            navToggle.classList.toggle('active');
        });
    }

    // Chapter content enhancement
    const chapterContent = document.querySelector('.chapter-content');
    if (chapterContent) {
        // Add proper paragraph spacing
        const paragraphs = chapterContent.querySelectorAll('p');
        paragraphs.forEach(p => {
            if (p.innerHTML.trim() === '') {
                p.classList.add('paragraph-break');
            }
        });

        // Add reading time estimate
        const text = chapterContent.textContent;
        const wordCount = text.split(/\s+/).length;
        const readingTime = Math.ceil(wordCount / 200); // Average reading speed: 200 words per minute
        
        const chapterMeta = document.querySelector('.chapter-meta');
        if (chapterMeta) {
            const readingTimeSpan = document.createElement('span');
            readingTimeSpan.classList.add('reading-time');
            readingTimeSpan.innerHTML = `<i class="fas fa-clock"></i> ${readingTime} min read`;
            chapterMeta.appendChild(readingTimeSpan);
        }
    }

    // Comment form character counter
    const commentTextarea = document.querySelector('.comment-form textarea');
    if (commentTextarea) {
        const maxLength = 1000;
        const counterDiv = document.createElement('div');
        counterDiv.classList.add('character-counter');
        counterDiv.textContent = `0/${maxLength}`;
        
        commentTextarea.parentNode.insertBefore(counterDiv, commentTextarea.nextSibling);
        
        commentTextarea.addEventListener('input', function() {
            const currentLength = this.value.length;
            counterDiv.textContent = `${currentLength}/${maxLength}`;
            
            if (currentLength > maxLength) {
                counterDiv.classList.add('over-limit');
            } else {
                counterDiv.classList.remove('over-limit');
            }
        });
    }
});