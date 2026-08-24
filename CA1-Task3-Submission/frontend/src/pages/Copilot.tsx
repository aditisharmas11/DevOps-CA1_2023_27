import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Send, 
  Sparkles, 
  MapPin, 
  Wrench, 
  Calendar, 
  User, 
  Bot, 
  Loader2,
  Trash2,
  ChevronRight,
  School,
  Building
} from 'lucide-react';
import api from '../services/api';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: Date;
  action?: {
    type: string;
    target?: string;
    room?: string;
    ticket?: string;
    details?: any;
  } | null;
}

const Copilot: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: "Hello! I am **CampusIQ**, your AI Smart Campus Copilot. 👋\n\nI can help you search for classrooms, locate campus buildings, check scheduled events, report maintenance tickets, or check occupancy levels. What can I do for you today?",
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [sending, setSending] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const suggestionChips = [
    "Find me a classroom for 40 students with a projector.",
    "Where is the library?",
    "The AC in B204 is broken.",
    "What events are happening today?",
    "How busy is the canteen?"
  ];

  // Auto-scroll to bottom of chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, sending]);

  const handleSend = async (textToSend: string) => {
    if (!textToSend.trim()) return;

    const userMsg: Message = {
      id: `msg-${Date.now()}-user`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setSending(true);

    try {
      const response = await api.post('/copilot', { query: textToSend });
      const reply = response.data;
      
      const assistantMsg: Message = {
        id: `msg-${Date.now()}-assistant`,
        sender: 'assistant',
        text: reply.message,
        timestamp: new Date(),
        action: reply.action
      };

      setMessages(prev => [...prev, assistantMsg]);
    } catch (err) {
      console.error('Error sending query to Copilot:', err);
      const errorMsg: Message = {
        id: `msg-${Date.now()}-error`,
        sender: 'assistant',
        text: "I'm sorry, I'm having trouble connecting to the AI brain right now. Please ensure the backend is running.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setSending(false);
    }
  };

  const handleActionClick = (action: any) => {
    if (!action) return;

    if (action.type === 'viewMap') {
      // Navigate to Map page and pass highlighted building/room
      navigate('/map', { 
        state: { 
          highlight: action.target,
          room: action.room 
        } 
      });
    } else if (action.type === 'viewMaintenance') {
      navigate('/maintenance', { 
        state: { 
          highlightTicket: action.ticket 
        } 
      });
    } else if (action.type === 'viewEvents') {
      navigate('/events');
    } else if (action.type === 'viewOccupancy') {
      navigate('/classrooms'); // Occupancies & Classroom view
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: 'welcome',
        sender: 'assistant',
        text: "Hello! I am **CampusIQ**, your AI Smart Campus Copilot. 👋\n\nI can help you search for classrooms, locate campus buildings, check scheduled events, report maintenance tickets, or check occupancy levels. What can I do for you today?",
        timestamp: new Date()
      }
    ]);
  };

  // Helper function to render text with basic Markdown tags (bolding and linebreaks)
  const renderFormattedText = (text: string) => {
    return text.split('\n').map((line, i) => {
      // Replace **text** with <strong>text</strong>
      const boldPattern = /\*\*(.*?)\*\*/g;
      const codePattern = /`(.*?)`/g;
      
      let htmlContent = line;
      htmlContent = htmlContent.replace(boldPattern, '<strong>$1</strong>');
      htmlContent = htmlContent.replace(codePattern, '<code class="px-1.5 py-0.5 bg-slate-100 dark:bg-dark-800 rounded font-mono text-xs text-brand-600 dark:text-brand-400">$1</code>');
      
      return (
        <p 
          key={i} 
          className="mb-2 leading-relaxed"
          dangerouslySetInnerHTML={{ __html: htmlContent }}
        />
      );
    });
  };

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-4rem)] md:h-screen bg-slate-50/50 dark:bg-dark-950 transition-colors duration-300">
      
      {/* Copilot Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-white dark:bg-dark-900 border-b border-slate-200/60 dark:border-slate-800/60 transition-colors shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl gradient-primary text-white shadow-md shadow-brand-500/20">
            <Sparkles size={20} className="animate-pulse" />
          </div>
          <div>
            <h3 className="font-extrabold text-slate-800 dark:text-white">AI Campus Copilot</h3>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-ping"></span>
              <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">Online</span>
            </div>
          </div>
        </div>

        <button 
          onClick={clearChat}
          title="Clear Conversation"
          className="p-2.5 rounded-xl text-slate-400 dark:text-slate-500 hover:text-red-500 dark:hover:text-red-400 hover:bg-slate-50 dark:hover:bg-dark-800/50 transition-all border border-transparent hover:border-slate-100 dark:hover:border-dark-800"
        >
          <Trash2 size={16} />
        </button>
      </div>

      {/* Messages Pane */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.map((msg) => {
            const isUser = msg.sender === 'user';
            return (
              <div 
                key={msg.id} 
                className={`flex gap-4 ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start`}
              >
                {/* Avatar */}
                <div className={`flex items-center justify-center w-9 h-9 rounded-2xl shrink-0 shadow-sm border ${
                  isUser 
                    ? 'bg-brand-50 dark:bg-dark-800 text-brand-600 dark:text-brand-400 border-brand-100 dark:border-dark-700' 
                    : 'bg-indigo-600 text-white border-transparent'
                }`}>
                  {isUser ? <User size={16} /> : <Bot size={16} />}
                </div>

                {/* Bubble Container */}
                <div className="max-w-[85%] sm:max-w-[75%] space-y-2">
                  <div className={`p-4 rounded-3xl text-sm ${
                    isUser 
                      ? 'bg-brand-600 text-white shadow-md shadow-brand-500/10 rounded-tr-none' 
                      : 'bg-white dark:bg-dark-900 text-slate-800 dark:text-slate-200 border border-slate-200/50 dark:border-slate-800/40 rounded-tl-none shadow-sm'
                  }`}>
                    {isUser ? <p className="leading-relaxed">{msg.text}</p> : renderFormattedText(msg.text)}
                  </div>

                  {/* Embed Action Button if returned */}
                  {msg.action && (
                    <div className="flex pl-1">
                      <button
                        onClick={() => handleActionClick(msg.action)}
                        className="inline-flex items-center gap-2 px-4 py-2.5 bg-white dark:bg-dark-900 border border-slate-200 dark:border-slate-800 hover:border-brand-500/30 dark:hover:border-brand-500/30 text-xs font-extrabold text-brand-600 dark:text-brand-400 rounded-2xl shadow-sm hover:shadow transition-all group"
                      >
                        {msg.action.type === 'viewMap' && <MapPin size={14} className="text-brand-500" />}
                        {msg.action.type === 'viewMaintenance' && <Wrench size={14} className="text-brand-500" />}
                        {msg.action.type === 'viewEvents' && <Calendar size={14} className="text-brand-500" />}
                        {msg.action.type === 'viewOccupancy' && <Building size={14} className="text-brand-500" />}
                        
                        <span>
                          {msg.action.type === 'viewMap' && `View ${msg.action.room || msg.action.target} on Map`}
                          {msg.action.type === 'viewMaintenance' && `View Ticket #${msg.action.ticket}`}
                          {msg.action.type === 'viewEvents' && `View Today's Events`}
                          {msg.action.type === 'viewOccupancy' && `View Building Occupancy`}
                        </span>
                        <ChevronRight size={12} className="group-hover:translate-x-0.5 transition-transform" />
                      </button>
                    </div>
                  )}

                  {/* Timestamp */}
                  <p className={`text-[10px] text-slate-400 dark:text-slate-500 ${isUser ? 'text-right pr-2' : 'pl-2'}`}>
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            );
          })}

          {/* Typing Indicator */}
          {sending && (
            <div className="flex gap-4 items-start">
              <div className="flex items-center justify-center w-9 h-9 rounded-2xl bg-indigo-600 text-white shrink-0 shadow-sm border border-transparent">
                <Bot size={16} />
              </div>
              <div className="bg-white dark:bg-dark-900 border border-slate-200/50 dark:border-slate-800/40 p-4 rounded-3xl rounded-tl-none flex items-center gap-1.5 shadow-sm">
                <span className="w-2 h-2 bg-slate-300 dark:bg-slate-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                <span className="w-2 h-2 bg-slate-300 dark:bg-slate-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                <span className="w-2 h-2 bg-slate-300 dark:bg-slate-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Suggestion Chips & Chat Input Footer */}
      <div className="px-6 py-4 bg-white dark:bg-dark-900 border-t border-slate-200/60 dark:border-slate-800/60 transition-colors shadow-lg z-10">
        <div className="max-w-3xl mx-auto space-y-4">
          
          {/* Chips list */}
          {messages.length === 1 && !sending && (
            <div className="flex items-center gap-2 overflow-x-auto pb-1.5 scrollbar-thin scrollbar-thumb-rounded">
              {suggestionChips.map((chip, index) => (
                <button
                  key={index}
                  onClick={() => handleSend(chip)}
                  className="px-4 py-2 bg-slate-50 dark:bg-dark-800/50 hover:bg-brand-50 dark:hover:bg-brand-950/20 hover:text-brand-600 dark:hover:text-brand-400 text-xs font-semibold text-slate-600 dark:text-slate-400 rounded-full border border-slate-200/60 dark:border-slate-800/60 hover:border-brand-500/20 shrink-0 transition-all"
                >
                  {chip}
                </button>
              ))}
            </div>
          )}

          {/* Form Input */}
          <form 
            onSubmit={(e) => { e.preventDefault(); handleSend(inputValue); }}
            className="flex items-center gap-3 relative"
          >
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask Copilot: 'Find classroom B204' or 'Report broken AC'..."
              disabled={sending}
              className="block w-full pl-5 pr-14 py-4 bg-slate-50 dark:bg-dark-950 border border-slate-200/80 dark:border-slate-850 rounded-2xl text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 dark:focus:ring-brand-500 focus:border-transparent dark:text-slate-100 transition-all shadow-inner"
            />
            <button
              type="submit"
              disabled={!inputValue.trim() || sending}
              className="absolute right-2 p-3 bg-brand-600 hover:bg-brand-500 text-white rounded-xl shadow-md shadow-brand-500/15 disabled:opacity-40 disabled:hover:bg-brand-600 transition-all"
            >
              {sending ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            </button>
          </form>
        </div>
      </div>

    </div>
  );
};

export default Copilot;
