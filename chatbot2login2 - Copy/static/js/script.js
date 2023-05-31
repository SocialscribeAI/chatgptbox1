window.onload = function() {
    var serverUrl = 'http://127.0.0.1:5000/generate_post';

    fetch(serverUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ "text": "start" }),
    })
    .then(response => response.json())
    .then(data => {
        var botResponse = data;

        var history = document.getElementById('chat-history');
        history.innerHTML += '<p><b>Bot:</b> ' + botResponse + '</p>';
    });
};

document.getElementById('chat-form').addEventListener('submit', function(event) {
    event.preventDefault();

    var message = document.getElementById('message').value;
    var history = document.getElementById('chat-history');

    history.innerHTML += '<p><b>You:</b> ' + message + '</p>';

    // Configure your server URL here
    var serverUrl = 'http://127.0.0.1:5000/generate_post';

    fetch(serverUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ "text": message }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        var botResponse = data;

        history.innerHTML += '<p><b>Bot:</b> ' + botResponse + '</p>';
        document.getElementById('message').value = '';

        // Scroll to the bottom of the chat history
        history.scrollTop = history.scrollHeight;
    })
    .catch((error) => {
        console.error('Error:', error);
        // Display the error message to the user
        history.innerHTML += '<p><b>Error:</b> ' + error.message + '</p>';
    });
});
