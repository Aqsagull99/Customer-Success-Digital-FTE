import { useState, useEffect, useRef } from 'react';

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

const API_BASE = '/api';

export default function Chat() {
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [showNewChat, setShowNewChat] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'auto' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  // Load messages when conversation is selected
  useEffect(() => {
    if (activeConversation) {
      loadMessages(activeConversation);
    }
  }, [activeConversation]);

  const loadConversations = async () => {
    try {
      // Get conversations from localStorage (for demo)
      const saved = localStorage.getItem('chat_conversations');
      if (saved) {
        setConversations(JSON.parse(saved));
      }
    } catch (error) {
      console.error('Error loading conversations:', error);
    }
  };

  const loadMessages = async (conversationId) => {
    try {
      // Try to load from API first
      const response = await fetch(`${API_BASE}/conversations/${conversationId}`);
      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages || []);
        return;
      }
      
      // Fallback to localStorage
      const saved = localStorage.getItem(`chat_messages_${conversationId}`);
      if (saved) {
        setMessages(JSON.parse(saved));
      }
    } catch (error) {
      console.error('Error loading messages:', error);
      // Fallback to localStorage
      const saved = localStorage.getItem(`chat_messages_${conversationId}`);
      if (saved) {
        setMessages(JSON.parse(saved));
      }
    }
  };

  const deleteConversation = (convId, e) => {
    e.stopPropagation(); // Prevent opening the conversation
    
    // Remove from conversations list
    const updated = conversations.filter(c => c.id !== convId);
    setConversations(updated);
    localStorage.setItem('chat_conversations', JSON.stringify(updated));
    
    // Remove messages
    localStorage.removeItem(`chat_messages_${convId}`);
    
    // If this was the active conversation, reset
    if (activeConversation?.id === convId) {
      setActiveConversation(null);
      setMessages([]);
    }
  };

  const createNewConversation = async () => {
    const newConv = {
      id: `chat_${Date.now()}`,
      subject: 'New Conversation',
      created_at: new Date().toISOString(),
      status: 'active',
    };
    
    const updated = [newConv, ...conversations];
    setConversations(updated);
    localStorage.setItem('chat_conversations', JSON.stringify(updated));
    
    setActiveConversation(newConv);
    setMessages([]);
    setShowNewChat(false);
    setInputMessage('');
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

    // Save to localStorage
    if (activeConversation) {
      localStorage.setItem(`chat_messages_${activeConversation.id}`, JSON.stringify(updatedMessages));
    }

    try {
      // Send to API
      const response = await fetch(`${API_BASE}/support/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'Chat User',
          email: 'chat@example.com',
          subject: activeConversation?.subject || 'Chat Message',
          category: 'general',
          message: userMessage.content,
          channel: 'web',
          metadata: {
            conversation_id: activeConversation?.id,
            is_chat: true,
          },
        }),
      });

      const data = await response.json();

      // Simulate AI response (in real implementation, this would come from WebSocket or polling)
      setTimeout(() => {
        const aiMessage = {
          id: `msg_${Date.now() + 1}`,
          role: 'agent',
          content: generateAIResponse(userMessage.content),
          created_at: new Date().toISOString(),
        };

        const finalMessages = [...updatedMessages, aiMessage];
        setMessages(finalMessages);
        setIsTyping(false);
        setIsLoading(false);

        // Save to localStorage
        if (activeConversation) {
          localStorage.setItem(`chat_messages_${activeConversation.id}`, JSON.stringify(finalMessages));
        }
      }, 1500);

    } catch (error) {
      console.error('Error sending message:', error);
      
      // Fallback: Generate local AI response
      setTimeout(() => {
        const aiMessage = {
          id: `msg_${Date.now() + 1}`,
          role: 'agent',
          content: generateAIResponse(userMessage.content),
          created_at: new Date().toISOString(),
        };

        const finalMessages = [...updatedMessages, aiMessage];
        setMessages(finalMessages);
        setIsTyping(false);
        setIsLoading(false);

        if (activeConversation) {
          localStorage.setItem(`chat_messages_${activeConversation.id}`, JSON.stringify(finalMessages));
        }
      }, 1500);
    }
  };

  // Simple AI response generator (replace with actual API call)
  const generateAIResponse = (userMessage) => {
    const lowerMessage = userMessage.toLowerCase();
    
    if (lowerMessage.includes('hello') || lowerMessage.includes('hi')) {
      return "Hello! 👋 How can I assist you today?";
    }
    if (lowerMessage.includes('help')) {
      return "I'm here to help! Please tell me more about your issue and I'll do my best to assist you.";
    }
    if (lowerMessage.includes('billing') || lowerMessage.includes('payment')) {
      return "I understand you have a billing question. Could you please provide more details about your concern? I can help with invoices, refunds, or payment issues.";
    }
    if (lowerMessage.includes('technical') || lowerMessage.includes('bug')) {
      return "I'm sorry to hear you're experiencing technical difficulties. Let me help you troubleshoot. Can you describe what's happening?";
    }
    if (lowerMessage.includes('thank')) {
      return "You're welcome! Is there anything else I can help you with?";
    }
    
    return "Thank you for reaching out! I've received your message and I'm here to help. Could you provide more details about your issue so I can assist you better?";
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="page-transition" style={{ overflow: 'auto', position: 'relative' }}>
      <div className="max-w-6xl mx-auto px-4 py-8" style={{ position: 'relative', zIndex: 1 }}>
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mb-8">
          <p className="pill">LIVE CHAT</p>
          <button
            type="button"
            onClick={createNewConversation}
            className="btn-primary"
          >
            + New Chat
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar - Conversations List */}
          <div className="lg:col-span-1">
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">Recent Chats</h3>
              {conversations.length === 0 ? (
                <p className="text-sm muted text-center py-8">
                  No conversations yet.<br />Click "New Chat" to start!
                </p>
              ) : (
                <div className="space-y-2">
                  {conversations.map((conv) => (
                    <div
                      key={conv.id}
                      className={`group flex items-center gap-2 p-3 rounded-lg transition-colors cursor-pointer ${
                        activeConversation?.id === conv.id
                          ? 'bg-[color:var(--accent)]/10'
                          : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                      }`}
                      onClick={() => setActiveConversation(conv)}
                    >
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm truncate">{conv.subject}</p>
                        <p className="text-xs muted">{formatTime(conv.created_at)}</p>
                      </div>
                      <button
                        type="button"
                        onClick={(e) => deleteConversation(conv.id, e)}
                        className="opacity-0 group-hover:opacity-100 p-2 hover:bg-red-100 dark:hover:bg-red-900/20 rounded-lg transition-all text-red-600 dark:text-red-400"
                        aria-label="Delete conversation"
                        title="Delete conversation"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Chat Area */}
          <div className="lg:col-span-3">
            <div className="card h-[600px] flex flex-col" style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)' }}>
              {!activeConversation ? (
                <div className="flex-1 flex items-center justify-center text-center p-8">
                  <div>
                    <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-[color:var(--accent)]/10 flex items-center justify-center">
                      <IconBot className="w-10 h-10 text-[color:var(--accent)]" />
                    </div>
                    <h3 className="text-2xl font-bold mb-3" style={{ color: 'var(--text)' }}>Welcome to Live Chat</h3>
                    <p className="muted mb-6" style={{ color: 'var(--muted)' }}>Start a conversation with our AI assistant</p>
                    <button
                      type="button"
                      onClick={createNewConversation}
                      className="btn-primary"
                    >
                      Start New Chat
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  {/* Chat Header */}
                  <div className="border-b pb-4 mb-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
                          <IconBot className="w-6 h-6 text-primary-600 dark:text-primary-400" />
                        </div>
                        <div>
                          <h3 className="font-semibold">{activeConversation.subject}</h3>
                          <p className="text-xs muted flex items-center gap-1">
                            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                            AI Assistant is online
                          </p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => setActiveConversation(null)}
                        className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
                        aria-label="Close chat"
                      >
                        <IconX className="w-5 h-5" />
                      </button>
                    </div>
                  </div>

                  {/* Messages */}
                  <div className="flex-1 overflow-y-auto mb-4 space-y-4">
                    {messages.length === 0 ? (
                      <div className="text-center py-12">
                        <p className="muted">Start the conversation!</p>
                        <p className="text-sm muted mt-1">Ask a question or describe your issue</p>
                      </div>
                    ) : (
                      messages.map((msg) => (
                        <div
                          key={msg.id}
                          className={`flex gap-3 ${
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
                              <IconUser className="w-5 h-5" style={{ color: 'var(--accent)' }} />
                            ) : (
                              <IconBot className="w-5 h-5" style={{ color: 'var(--accent)' }} />
                            )}
                          </div>
                          <div
                            className={`max-w-[70%] rounded-2xl px-4 py-3 ${
                              msg.role === 'user'
                                ? 'text-white rounded-br-none'
                                : 'rounded-bl-none'
                            }`}
                            style={{
                              backgroundColor: msg.role === 'user' ? 'var(--accent)' : 'var(--surface-2)',
                              color: msg.role === 'user' ? '#fff' : 'var(--text)',
                            }}
                          >
                            <p className="text-sm">{msg.content}</p>
                            <p
                              className={`text-xs mt-1 ${
                                msg.role === 'user' ? 'text-white/70' : 'text-muted'
                              }`}
                            >
                              {formatTime(msg.created_at)}
                            </p>
                          </div>
                        </div>
                      ))
                    )}
                    
                    {isTyping && (
                      <div className="flex gap-3">
                        <div className="w-8 h-8 rounded-full bg-[color:var(--accent)]/10 flex items-center justify-center">
                          <IconBot className="w-5 h-5" style={{ color: 'var(--accent)' }} />
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
                  <form onSubmit={sendMessage} className="border-t pt-4">
                    <div className="flex gap-3">
                      <input
                        type="text"
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        placeholder="Type your message..."
                        disabled={isLoading}
                        className="field flex-1"
                        autoFocus
                      />
                      <button
                        type="submit"
                        disabled={isLoading || !inputMessage.trim()}
                        className={`btn-primary ${
                          isLoading || !inputMessage.trim() ? 'is-disabled' : ''
                        }`}
                      >
                        <IconSend className="w-5 h-5" />
                      </button>
                    </div>
                    <p className="text-xs muted mt-2 text-center">
                      AI-powered support • Responses typically within seconds
                    </p>
                  </form>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
