import { useState, useEffect, useRef } from 'react';

const API_BASE = '/api';

// Inline icons to avoid import issues
const IconBot = ({ className = "icon" }) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" aria-hidden="true">
    <path strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" d="M12 8V4" />
    <path strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" d="M8 4h8" />
    <rect x="4" y="8" width="16" height="12" rx="2" strokeWidth="1.8" />
    <path strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" d="M9 14l2 2 4-4" />
  </svg>
);

const IconUser = ({ className = "icon" }) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" aria-hidden="true">
    <path strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
    <path strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" d="M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z" />
  </svg>
);

const IconX = ({ className = "icon" }) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" aria-hidden="true">
    <path strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" d="M18 6 6 18" />
    <path strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" d="m6 6 12 12" />
  </svg>
);

const IconSend = ({ className = "icon" }) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" aria-hidden="true">
    <path strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" d="m22 2-7 20-4-9-9-4Z" />
    <path strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" d="M22 2 11 13" />
  </svg>
);

const IconMessage = ({ className = "icon" }) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" aria-hidden="true">
    <path strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2Z" />
  </svg>
);

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const messagesEndRef = useRef(null);
  const widgetRef = useRef(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'auto' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (widgetRef.current && !widgetRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // Load saved conversation
  useEffect(() => {
    const saved = localStorage.getItem('chat_widget_conversation');
    if (saved) {
      setConversationId(saved);
    }
    const savedMessages = localStorage.getItem('chat_widget_messages');
    if (savedMessages) {
      setMessages(JSON.parse(savedMessages));
    }
  }, []);

  const startNewConversation = () => {
    const newId = `chat_widget_${Date.now()}`;
    setConversationId(newId);
    localStorage.setItem('chat_widget_conversation', newId);
    setMessages([]);
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: inputMessage.trim(),
      created_at: new Date().toISOString(),
    };

    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInputMessage('');
    setIsLoading(true);
    setIsTyping(true);

    // Save to localStorage optimistically
    localStorage.setItem('chat_widget_messages', JSON.stringify(updatedMessages));

    try {
      // Call real backend API
      const response = await fetch(`${API_BASE}/chat/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage.content,
          conversation_id: conversationId,
        }),
      });

      if (!response.ok) {
        throw new Error('API request failed');
      }

      const data = await response.json();
      
      // Update conversation ID if new
      if (!conversationId) {
        setConversationId(data.conversation_id);
        localStorage.setItem('chat_widget_conversation', data.conversation_id);
      }

      // Add AI response
      const aiMessage = {
        id: `msg_${Date.now() + 1}`,
        role: 'agent',
        content: data.ai_response,
        created_at: new Date().toISOString(),
      };

      const finalMessages = [...updatedMessages, aiMessage];
      setMessages(finalMessages);
      localStorage.setItem('chat_widget_messages', JSON.stringify(finalMessages));
      
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Fallback: Generate local response
      setTimeout(() => {
        const aiMessage = {
          id: `msg_${Date.now() + 1}`,
          role: 'agent',
          content: generateAIResponse(userMessage.content),
          created_at: new Date().toISOString(),
        };

        const finalMessages = [...updatedMessages, aiMessage];
        setMessages(finalMessages);
        localStorage.setItem('chat_widget_messages', JSON.stringify(finalMessages));
      }, 1500);
    } finally {
      setIsTyping(false);
      setIsLoading(false);
    }
  };

  const generateAIResponse = (userMessage) => {
    const lowerMessage = userMessage.toLowerCase();
    
    if (lowerMessage.includes('hello') || lowerMessage.includes('hi')) {
      return "Hello! 👋 How can I assist you today?";
    }
    if (lowerMessage.includes('help')) {
      return "I'm here to help! Please tell me more about your issue.";
    }
    if (lowerMessage.includes('billing') || lowerMessage.includes('payment')) {
      return "I understand you have a billing question. Could you provide more details?";
    }
    if (lowerMessage.includes('technical') || lowerMessage.includes('bug')) {
      return "Sorry to hear about the technical issue. Let me help you troubleshoot.";
    }
    if (lowerMessage.includes('thank')) {
      return "You're welcome! Anything else I can help with?";
    }
    
    return "Thanks for reaching out! I'm here to help. Could you provide more details?";
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  const clearChat = () => {
    setMessages([]);
    setConversationId(null);
    localStorage.removeItem('chat_widget_conversation');
    localStorage.removeItem('chat_widget_messages');
  };

  const deleteMessage = (msgId) => {
    const updated = messages.filter(m => m.id !== msgId);
    setMessages(updated);
    localStorage.setItem('chat_widget_messages', JSON.stringify(updated));
  };

  return (
    <>
      {/* Chat Toggle Button */}
      {!isOpen && (
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 w-14 h-14 bg-[color:var(--accent)] hover:bg-[color:var(--accent-2)] text-white rounded-full shadow-lg flex items-center justify-center transition-all hover:scale-110 z-50"
          aria-label="Open chat"
        >
          <IconMessage className="w-6 h-6" />
          {messages.length > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
              {messages.length}
            </span>
          )}
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div
          ref={widgetRef}
          className="fixed bottom-6 right-6 w-96 max-h-[600px] rounded-2xl shadow-2xl flex flex-col overflow-hidden z-50 border z-50"
          style={{
            backgroundColor: 'var(--surface)',
            borderColor: 'var(--border)',
          }}
        >
          {/* Header */}
          <div className="bg-[color:var(--accent)] text-white px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                <IconBot className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-sm">AI Support</h3>
                <p className="text-xs text-white/80 flex items-center gap-1">
                  <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                  Online
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              {messages.length > 0 && (
                <button
                  type="button"
                  onClick={clearChat}
                  className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                  aria-label="Clear chat"
                  title="Clear chat"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              )}
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                aria-label="Close chat"
              >
                <IconX className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[300px] max-h-[400px]" style={{ backgroundColor: 'var(--surface)' }}>
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center" style={{ backgroundColor: 'var(--accent)/15' }}>
                  <IconBot className="w-8 h-8" style={{ color: 'var(--accent)' }} />
                </div>
                <h4 className="font-semibold mb-2">Start a Conversation</h4>
                <p className="text-sm muted">Ask us anything! We're here to help.</p>
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-2 ${
                    msg.role === 'user' ? 'flex-row-reverse' : ''
                  }`}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                      msg.role === 'user'
                        ? 'bg-[color:var(--accent)]/10'
                        : 'bg-[color:var(--accent)]/10'
                    }`}
                  >
                    {msg.role === 'user' ? (
                      <IconUser className="w-4 h-4" style={{ color: 'var(--accent)' }} />
                    ) : (
                      <IconBot className="w-4 h-4" style={{ color: 'var(--accent)' }} />
                    )}
                  </div>
                  <div className="max-w-[75%] group relative">
                    <button
                      onClick={() => deleteMessage(msg.id)}
                      className="absolute -top-2 -right-6 opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 dark:hover:bg-red-900/20 rounded transition-all text-red-600 dark:text-red-400"
                      aria-label="Delete message"
                      title="Delete message"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                    <div
                      className={`rounded-2xl px-3 py-2 text-sm ${
                        msg.role === 'user'
                          ? 'text-white rounded-br-none'
                          : 'rounded-bl-none'
                      }`}
                      style={{
                        backgroundColor: msg.role === 'user' ? 'var(--accent)' : 'var(--surface-2)',
                        color: msg.role === 'user' ? '#fff' : 'var(--text)',
                      }}
                    >
                      {msg.content}
                    </div>
                    <p
                      className={`text-xs mt-1 ${
                        msg.role === 'user' ? 'text-right' : ''
                      } text-muted`}
                    >
                      {formatTime(msg.created_at)}
                    </p>
                  </div>
                </div>
              ))
            )}
            
            {isTyping && (
              <div className="flex gap-2">
                <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ backgroundColor: 'var(--accent)/15' }}>
                  <IconBot className="w-4 h-4" style={{ color: 'var(--accent)' }} />
                </div>
                <div className="rounded-2xl rounded-bl-none px-4 py-3" style={{ backgroundColor: 'var(--surface-2)' }}>
                  <div className="flex gap-1">
                    <span className="w-2 h-2 rounded-full animate-bounce" style={{ backgroundColor: 'var(--muted)', animationDelay: '0ms' }}></span>
                    <span className="w-2 h-2 rounded-full animate-bounce" style={{ backgroundColor: 'var(--muted)', animationDelay: '150ms' }}></span>
                    <span className="w-2 h-2 rounded-full animate-bounce" style={{ backgroundColor: 'var(--muted)', animationDelay: '300ms' }}></span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input Form */}
          <form onSubmit={sendMessage} className="border-t p-3" style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)' }}>
            <div className="flex gap-2">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Type your message..."
                disabled={isLoading}
                className="field flex-1 text-sm py-2"
                style={{
                  backgroundColor: 'var(--surface-2)',
                  color: 'var(--text)',
                  borderColor: 'var(--border)',
                }}
                autoFocus
              />
              <button
                type="submit"
                disabled={isLoading || !inputMessage.trim()}
                className={`rounded-lg py-2 px-3 transition-colors ${
                  isLoading || !inputMessage.trim() ? 'opacity-50 cursor-not-allowed' : ''
                }`}
                style={{
                  backgroundColor: isLoading || !inputMessage.trim() ? 'var(--muted)' : 'var(--accent)',
                  color: '#fff',
                }}
              >
                <IconSend className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs mt-2 text-center" style={{ color: 'var(--muted)' }}>
              AI-powered • Responses in seconds
            </p>
          </form>
        </div>
      )}
    </>
  );
}
