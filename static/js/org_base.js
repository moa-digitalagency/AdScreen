document.addEventListener('DOMContentLoaded', function() {
    const overlay = document.getElementById('mobile-overlay');
    if (overlay) {
        overlay.addEventListener('click', toggleMobileMenu);
    }

    const toggleBtn = document.getElementById('mobile-menu-toggle-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleMobileMenu);
    }

    window.addEventListener('resize', function() {
        if (window.innerWidth >= 1024) {
            closeMobileMenu();
        }
    });

    document.body.style.overflow = '';
});

function toggleMobileMenu() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('mobile-overlay');
    if (!sidebar || !overlay) return;

    const isOpen = sidebar.classList.contains('sidebar-mobile-visible');

    if (isOpen) {
        closeMobileMenu();
    } else {
        sidebar.classList.remove('sidebar-mobile-hidden');
        sidebar.classList.add('sidebar-mobile-visible');
        overlay.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
}

function closeMobileMenu() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('mobile-overlay');
    if (!sidebar || !overlay) return;

    sidebar.classList.remove('sidebar-mobile-visible');
    sidebar.classList.add('sidebar-mobile-hidden');
    overlay.classList.add('hidden');
    document.body.style.overflow = '';
}
