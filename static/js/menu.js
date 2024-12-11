document.addEventListener('DOMContentLoaded', function () {
    // Add class to body based on route
    const path = window.location.pathname;
    if (path === '/') {
        document.body.classList.add('index-page');
    }

    const menuButton = document.querySelector('.menu-button');
    const nav = document.querySelector('nav');

    if (menuButton && nav) {
        menuButton.addEventListener('click', function () {
            menuButton.classList.toggle('active');
            nav.classList.toggle('active');
        });

        // Close menu when clicking outside
        document.addEventListener('click', function (e) {
            if (!nav.contains(e.target) && !menuButton.contains(e.target) && nav.classList.contains('active')) {
                nav.classList.remove('active');
                menuButton.classList.remove('active');
            }
        });
    }
});