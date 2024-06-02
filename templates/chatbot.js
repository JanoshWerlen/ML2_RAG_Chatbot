document.getElementById('register-btn').addEventListener('click', function() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    fetch('/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
    }).then(response => response.json()).then(data => {
        if (data.success) {
            alert('Registration successful!');
        } else {
            alert('Registration failed: ' + data.error);
        }
    });
});

document.getElementById('login-btn').addEventListener('click', function() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
    }).then(response => response.json()).then(data => {
        if (data.success) {
            alert('Login successful!');
            document.getElementById('auth-container').style.display = 'none';
            document.getElementById('chat-container').style.display = 'block';
        } else {
            alert('Login failed: ' + data.error);
        }
    });
});

document.getElementById('send-btn').addEventListener('click', function() {
    const message = document.getElementById('user-input').value;
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message })
    }).then(response => response.json()).then(data => {
        const chatLog = document.getElementById('chat-log');
        chatLog.innerHTML += `<div>User: ${message}</div>`;
        chatLog.innerHTML += `<div>Bot: ${data.response}</div>`;
        document.getElementById('user-input').value = '';
        document.getElementById('followup-btn').style.display = 'block';
        document.getElementById('new-question-btn').style.display = 'block';
    });
});

document.getElementById('followup-btn').addEventListener('click', function() {
    const message = document.getElementById('user-input').value;
    fetch('/followup', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message })
    }).then(response => response.json()).then(data => {
        const chatLog = document.getElementById('chat-log');
        chatLog.innerHTML += `<div>User: ${message}</div>`;
        chatLog.innerHTML += `<div>Bot: ${data.response}</div>`;
        document.getElementById('user-input').value = '';
    });
});

document.getElementById('new-question-btn').addEventListener('click', function() {
    document.getElementById('chat-log').innerHTML = '';
    document.getElementById('user-input').value = '';
    document.getElementById('followup-btn').style.display = 'none';
    document.getElementById('new-question-btn').style.display = 'none';
});
