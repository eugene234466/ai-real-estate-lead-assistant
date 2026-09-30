const API_BASE_URL = 'http://127.0.0.1:5000/api';

async function sendMessage(text: string) {
    const response = await fetch(`${API_BASE_URL}/chat/message`, {
        method: 'POST',
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
    });

    if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
    }

    const data = await response.json();

    return data;
}

export { sendMessage };