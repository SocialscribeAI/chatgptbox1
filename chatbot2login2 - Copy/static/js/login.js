window.onload = function() {
    var loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            event.preventDefault();
            var username = document.getElementById('username').value;
            var password = document.getElementById('password').value;
            var serverUrl = 'http://127.0.0.1:5000/login';

            fetch(serverUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`,
                credentials: 'same-origin'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                window.location.href = '/index';
            })
            .catch((error) => {
                console.error('Error:', error);
                alert('Login failed: ' + error.message);
            });
        });
    }
};
