document.addEventListener('DOMContentLoaded', function () {
    const menuButton = document.querySelector('.menu-button');
    const nav = document.querySelector('nav');

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
});