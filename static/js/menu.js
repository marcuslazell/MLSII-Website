document.addEventListener('DOMContentLoaded', function () {
    if (window.innerWidth <= 768) {
        const menuButton = document.createElement('div');
        menuButton.className = 'menu-button';
        menuButton.innerHTML = '<span></span>';
        document.body.appendChild(menuButton);

        const nav = document.querySelector('nav');

        menuButton.addEventListener('click', function () {
            menuButton.classList.toggle('active');
            nav.classList.toggle('active');

            if (menuButton.classList.contains('active')) {
                menuButton.querySelector('span').style.background = 'transparent';
                menuButton.querySelector('span').style.transform = 'rotate(45deg)';
            } else {
                menuButton.querySelector('span').style.background = 'white';
                menuButton.querySelector('span').style.transform = 'none';
            }
        });
    }
});