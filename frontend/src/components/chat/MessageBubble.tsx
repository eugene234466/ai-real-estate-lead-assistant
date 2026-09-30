import React from 'react';

type MessageBubbleProps = {
    sender: 'user' | 'ai';
    text: string;
};

function MessageBubble({ sender, text }: MessageBubbleProps) {
    return (
        <div className={`message-bubble ${sender}`}>
            <p>{text}</p>
        </div>
    );
}

export default MessageBubble;