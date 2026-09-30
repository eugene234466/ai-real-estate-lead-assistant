// frontend/src/components/chat/ChatWidget.tsx

import React, { useState } from 'react';
import { sendMessage } from '../../api/client';
import MessageBubble from './MessageBubble';

type Message = {
    sender: 'user' | 'ai';
    text: string;
};

function ChatWidget() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputText, setInputText] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [aiPaused, setAiPaused] = useState(false);

    async function handleSend() {
        if (inputText.trim() === '' || isLoading) return;

        const userMessage: Message = { sender: 'user', text: inputText };
        setMessages((prev) => [...prev, userMessage]);
        const currentInput = inputText;
        setInputText('');
        setIsLoading(true);

        try {
            const result = await sendMessage(currentInput);

            if (result.ai_paused) {
                setAiPaused(true);
            } else {
                const aiMessage: Message = { sender: 'ai', text: result.reply };
                setMessages((prev) => [...prev, aiMessage]);
            }
        } catch (error) {
            const errorMessage: Message = {
                sender: 'ai',
                text: 'Something went wrong. Please try again.'
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    }

    function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            handleSend();
        }
    }

    return (
        <div className="chat-widget">
            <div className="messages-area">
                {messages.map((message, index) => (
                    <MessageBubble key={index} sender={message.sender} text={message.text} />
                ))}

                {isLoading && <div className="typing-indicator">AI is typing...</div>}

                {aiPaused && (
                    <div className="paused-banner">
                        This conversation is now being handled by an agent.
                    </div>
                )}
            </div>

            <div className="input-area">
                <textarea
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={isLoading}
                    placeholder="Type a message..."
                />
                <button onClick={handleSend} disabled={isLoading || inputText.trim() === ''}>
                    Send
                </button>
            </div>
        </div>
    );
}

export default ChatWidget;