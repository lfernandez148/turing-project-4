// Basic JavaScript for the static web server
document.addEventListener('DOMContentLoaded', function() {
    console.log('Static web server loaded successfully!');
    
    // Add some basic interactivity
    const header = document.querySelector('h1');
    if (header) {
        header.addEventListener('click', function() {
            header.style.color = header.style.color === 'rgb(52, 152, 219)' ? '#2c3e50' : '#3498db';
        });
    }
});
