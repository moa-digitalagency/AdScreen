document.addEventListener('DOMContentLoaded', function() {
    const overlay = document.getElementById('mobile-overlay');
    const toggleBtn = document.getElementById('admin-mobile-menu-toggle');

    if (overlay) {
        overlay.addEventListener('click', toggleMobileMenu);
    }

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
    const sidebar = document.getElementById('admin-sidebar');
    const overlay = document.getElementById('mobile-overlay');

    if (!sidebar || !overlay) return;

    const isOpen = sidebar.classList.contains('sidebar-mobile-visible');

    if (isOpen) {
        sidebar.classList.remove('sidebar-mobile-visible');
        overlay.classList.add('hidden');
        document.body.style.overflow = '';
    } else {
        sidebar.classList.add('sidebar-mobile-visible');
        overlay.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
}

function closeMobileMenu() {
    const sidebar = document.getElementById('admin-sidebar');
    const overlay = document.getElementById('mobile-overlay');

    if (!sidebar || !overlay) return;

    sidebar.classList.remove('sidebar-mobile-visible');
    overlay.classList.add('hidden');
    document.body.style.overflow = '';
}
