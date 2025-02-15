let authToken = localStorage.getItem('token');
let currentUser = null;
let selectedContact = null;

// Initialize the app
document.addEventListener('DOMContentLoaded', async () => {
    if (!authToken && window.location.pathname !== '/login' && window.location.pathname !== '/signup') {
        window.location.href = '/login';
        return;
    }
    
    if (window.location.pathname === '/chat') {
        await loadCurrentUser();
        await loadContacts();
        setupEventListeners();
        setInterval(loadMessages, 3000); // Refresh messages every 3 seconds
    }
});

async function loadCurrentUser() {
    const response = await fetch('/users/me', {
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    });
    currentUser = await response.json();
}

// Contacts functionality
async function loadContacts() {
    try {
        const response = await fetch('/contacts', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        const contacts = await response.json();
        renderContacts(contacts);
    } catch (error) {
        console.error('Failed to load contacts:', error);
    }
}

function renderContacts(contacts) {
    const contactsList = document.getElementById('contactsList');
    contactsList.innerHTML = contacts.map(contact => `
        <div class="contact-item ${selectedContact?.id === contact.id ? 'selected' : ''}" 
             onclick="selectContact(${contact.id}, '${contact.username}')">
            <div class="contact-avatar">${contact.username[0].toUpperCase()}</div>
            <div class="contact-info">
                <h4>${contact.username}</h4>
                <p class="last-message">${contact.lastMessage || ''}</p>
            </div>
        </div>
    `).join('');
}

async function addContact() {
    const username = document.getElementById('contactUsername').value;
    if (!username) return;

    try {
        const response = await fetch('/contacts/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ username })
        });

        if (response.ok) {
            closeAddContact();
            await loadContacts();
        } else {
            const error = await response.json();
            alert(error.detail);
        }
    } catch (error) {
        console.error('Failed to add contact:', error);
    }
}

// Messages functionality
async function loadMessages() {
    if (!selectedContact) return;

    try {
        const response = await fetch(`/messages/${selectedContact.id}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        const messages = await response.json();
        renderMessages(messages);
    } catch (error) {
        console.error('Failed to load messages:', error);
    }
}

function renderMessages(messages) {
    const container = document.getElementById('messagesContainer');
    container.innerHTML = messages.map(msg => `
        <div class="message ${msg.sender_id === currentUser.id ? 'sent' : 'received'}">
            <div class="message-content">${msg.content}</div>
            <div class="message-time">${new Date(msg.timestamp).toLocaleTimeString()}</div>
        </div>
    `).join('');
    
    // Auto-scroll to bottom
    container.scrollTop = container.scrollHeight;
}

async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    if (!message || !selectedContact) return;

    try {
        const response = await fetch('/messages/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                receiver_username: selectedContact.username,
                content: message
            })
        });

        if (response.ok) {
            input.value = '';
            await loadMessages();
        }
    } catch (error) {
        console.error('Failed to send message:', error);
    }
}

// UI Interactions
function selectContact(contactId, username) {
    selectedContact = { id: contactId, username };
    document.getElementById('currentContact').textContent = username;
    loadMessages();
    document.querySelectorAll('.contact-item').forEach(item => {
        item.classList.toggle('selected', item.dataset.contactId === contactId);
    });
}

function showAddContact() {
    document.getElementById('addContactModal').style.display = 'block';
}

function closeAddContact() {
    document.getElementById('addContactModal').style.display = 'none';
    document.getElementById('contactUsername').value = '';
}

function setupEventListeners() {
    document.getElementById('messageInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}

// Logout
function logout() {
    localStorage.removeItem('token');
    window.location.href = '/login';
}

document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail);
        }

        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        window.location.href = '/chat';
    } catch (error) {
        showError(error.message);
    }
});

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    document.body.prepend(errorDiv);
    setTimeout(() => errorDiv.remove(), 3000);
}