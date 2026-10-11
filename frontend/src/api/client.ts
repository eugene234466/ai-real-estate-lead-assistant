const API_BASE_URL = 'http://127.0.0.1:5000/api';
const WIDGET_KEY = import.meta.env.VITE_WIDGET_KEY;
const TOKEN_STORAGE_KEY = 'conversation_token';

async function sendMessage(text: string) {
    if(!WIDGET_KEY){
        throw new Error('VITE_WIDGET_KEY is not set');
    }



    const token = sessionStorage.getItem(TOKEN_STORAGE_KEY);
    const response = await fetch(`${API_BASE_URL}/chat/message`, {
        method: 'POST',
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, widget_key: WIDGET_KEY, conversation_token: token   })
    });

    if(response.status === 404 && token){
        sessionStorage.removeItem(TOKEN_STORAGE_KEY);
        throw new Error('Conversation expired');
    }

    if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
    }

    const data = await response.json();

    if(data.conversation_token) {
        sessionStorage.setItem(TOKEN_STORAGE_KEY, data.conversation_token);
    }

    return data;
}

export { sendMessage };