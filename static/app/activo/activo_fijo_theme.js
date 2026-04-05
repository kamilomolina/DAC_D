// activo_fijo_theme.js - MNT CONTROL Style Logic

document.addEventListener('DOMContentLoaded', () => {
    const themeBtn = document.getElementById('theme-toggle-btn');
    const themeIcon = document.getElementById('theme-icon');
    
    // Obtener tema actual de localStorage (por defecto es 'dark' para este nuevo estilo)
    let currentTheme = localStorage.getItem('theme_activo_fijo') || 'dark';
    
    // Aplicar tema inicial
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeUI(currentTheme);

    // Event Listener Toggle
    if(themeBtn) {
        themeBtn.addEventListener('click', () => {
            let activeTheme = document.documentElement.getAttribute('data-theme');
            let newTheme = activeTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme_activo_fijo', newTheme);
            updateThemeUI(newTheme);
            
            // Dispatch event for components that might need a refresh
            window.dispatchEvent(new Event('themeChanged'));
        });
    }

    function updateThemeUI(theme) {
        if (!themeIcon) return;
        
        // Estilo CWS Style (FontAwesome icons)
        if (theme === 'dark') {
            themeIcon.classList.remove('fa-sun');
            themeIcon.classList.add('fa-moon');
            themeIcon.style.color = '#f8fafc';
        } else {
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
            themeIcon.style.color = '#fbbf24'; // Sol Amarillo
        }
    }

    // Toggle para mobile Sidebar
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('app-sidebar');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            sidebar.classList.toggle('show');
        });
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth < 992 && !sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                sidebar.classList.remove('show');
            }
        });
    }

    // Active Link Highlighting and Parent Expansion
    const links = document.querySelectorAll('.sidebar-menu .nav-link');
    const currentUrl = window.location.pathname;
    
    links.forEach(link => {
        const linkHref = link.getAttribute('href');
        if (linkHref && linkHref !== '#' && currentUrl.includes(linkHref)) {
            link.classList.add('active');
            
            // Expand parent if it's a submenu item
            const parentCollapse = link.closest('.collapse');
            if (parentCollapse) {
                // Initialize collapse if not already done
                const bsCollapse = bootstrap.Collapse.getOrCreateInstance(parentCollapse, { toggle: false });
                bsCollapse.show();
                
                // Also highlight the parent toggle link
                const parentToggle = document.querySelector(`[href="#${parentCollapse.id}"]`);
                if (parentToggle) {
                    parentToggle.classList.remove('collapsed');
                    parentToggle.setAttribute('aria-expanded', 'true');
                }
            }
        } else {
            if (!link.hasAttribute('data-bs-toggle')) {
                link.classList.remove('active');
            }
        }
    });
});
