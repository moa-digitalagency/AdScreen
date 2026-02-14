document.addEventListener('DOMContentLoaded', function() {
    initDropdowns();
    initFlashMessages();
    initMobileMenu();
    initSmoothScroll();
    initScrollAnimations();
    initNavbarScroll();
    initCounterAnimations();
});

function initDropdowns() {
    const dropdowns = document.querySelectorAll('[data-dropdown]');
    
    dropdowns.forEach(dropdown => {
        const trigger = dropdown.querySelector('[data-dropdown-trigger]');
        const menu = dropdown.querySelector('[data-dropdown-menu]');
        
        if (trigger && menu) {
            trigger.addEventListener('click', (e) => {
                e.stopPropagation();
                menu.classList.toggle('show');
            });
        }
    });
    
    document.addEventListener('click', () => {
        document.querySelectorAll('[data-dropdown-menu]').forEach(menu => {
            menu.classList.remove('show');
        });
    });
}

function initFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.transition = 'opacity 0.5s, transform 0.5s';
            message.style.opacity = '0';
            message.style.transform = 'translateX(100%)';
            setTimeout(() => message.remove(), 500);
        }, 5000);
    });
}

function initMobileMenu() {
    const menuToggle = document.querySelector('[data-mobile-menu-toggle]');
    const mobileMenu = document.querySelector('[data-mobile-menu]');
    
    if (menuToggle && mobileMenu) {
        menuToggle.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }
}

function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href === '#') return;
            
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                const headerOffset = 100;
                const elementPosition = target.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

function initScrollAnimations() {
    if (typeof IntersectionObserver === 'undefined') return;
    
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in-up');
                entry.target.style.opacity = '1';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    document.querySelectorAll('[data-animate]').forEach(el => {
        el.style.opacity = '0';
        observer.observe(el);
    });

    document.querySelectorAll('.card, .pricing-card, .testimonial-card').forEach((el, index) => {
        el.style.opacity = '0';
        el.style.transitionDelay = `${index * 0.1}s`;
        observer.observe(el);
    });
}

function initNavbarScroll() {
    const navbar = document.querySelector('nav');
    if (!navbar) return;
    
    let lastScroll = 0;
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 50) {
            navbar.classList.add('shadow-md');
            navbar.style.backgroundColor = 'rgba(255, 255, 255, 0.95)';
        } else {
            navbar.classList.remove('shadow-md');
            navbar.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
        }
        
        lastScroll = currentScroll;
    });
}

function initCounterAnimations() {
    if (typeof IntersectionObserver === 'undefined') return;
    
    const counters = document.querySelectorAll('[data-counter]');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = parseInt(entry.target.dataset.counter);
                animateCounter(entry.target, target);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });
    
    counters.forEach(counter => observer.observe(counter));
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const messageSpan = document.createElement('span');
    messageSpan.textContent = message;
    
    const closeButton = document.createElement('button');
    closeButton.className = 'ml-2 hover:opacity-75';
    closeButton.onclick = function() { this.parentElement.remove(); };
    
    const closeIcon = document.createElement('i');
    closeIcon.className = 'fas fa-times';
    closeButton.appendChild(closeIcon);
    
    toast.appendChild(messageSpan);
    toast.appendChild(closeButton);
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.transition = 'opacity 0.5s, transform 0.5s';
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 500);
    }, 5000);
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
    }
}

function confirmDelete(message, form) {
    if (confirm(message || window.I18N.confirm_delete_default)) {
        form.submit();
    }
    return false;
}

function formatNumber(num) {
    return new Intl.NumberFormat(window.CURRENT_LOCALE || 'fr-FR').format(num);
}

function formatCurrency(amount) {
    return new Intl.NumberFormat(window.CURRENT_LOCALE || 'fr-FR', {
        style: 'currency',
        currency: 'EUR'
    }).format(amount);
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return new Intl.DateTimeFormat(window.CURRENT_LOCALE || 'fr-FR', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    }).format(date);
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast(window.I18N.copy_success, 'success');
    }).catch(() => {
        showToast(window.I18N.copy_error, 'error');
    });
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function animateCounter(element, target, duration = 1500) {
    const start = 0;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        const current = Math.floor(easeOutQuart * target);
        
        element.textContent = formatNumber(current);
        
        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            element.textContent = formatNumber(target);
        }
    }
    
    requestAnimationFrame(update);
}

function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

function addRippleEffect(button) {
    button.addEventListener('click', function(e) {
        const ripple = document.createElement('span');
        const rect = this.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;
        
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s linear;
            pointer-events: none;
        `;
        
        this.style.position = 'relative';
        this.style.overflow = 'hidden';
        this.appendChild(ripple);
        
        setTimeout(() => ripple.remove(), 600);
    });
}

document.querySelectorAll('.btn-primary').forEach(addRippleEffect);

const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

/* Extracted from base.html */
function toggleLangMenu() {
    const menu = document.getElementById('lang-menu');
    const chevron = document.getElementById('lang-chevron');
    if (menu && chevron) {
        menu.classList.toggle('hidden');
        chevron.classList.toggle('rotate-180');
    }
}

document.addEventListener('click', function(e) {
    const switcher = document.getElementById('lang-switcher');
    const menu = document.getElementById('lang-menu');
    const chevron = document.getElementById('lang-chevron');

    if (switcher && !switcher.contains(e.target) && menu && chevron) {
        menu.classList.add('hidden');
        chevron.classList.remove('rotate-180');
    }
});

/* Event listeners for refactored elements */
document.addEventListener('DOMContentLoaded', function() {
    // Language Switcher Toggle
    const langBtn = document.getElementById('lang-toggle-btn');
    if (langBtn) {
        langBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleLangMenu();
        });
    }

    // Flash Message Close Buttons
    document.addEventListener('click', function(e) {
        const closeBtn = e.target.closest('.flash-close-btn');
        if (closeBtn) {
            const message = closeBtn.closest('.flash-message');
            if (message) {
                message.remove();
            }
        }
    });
});
