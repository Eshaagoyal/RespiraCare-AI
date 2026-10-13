import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { 
  Bot, 
  User, 
  Send, 
  RefreshCw, 
  AlertTriangle, 
  AlertCircle, 
  ShieldAlert, 
  HelpCircle, 
  ExternalLink,
  HeartPulse,
  Mic,
  MicOff
} from 'lucide-react';

function Chat() {
  const [messages, setMessages] = useState([
    { 
      role: 'ai', 
      content: "Hello. I am the RespiraCare AI Assistant. How can I help you with your asthma symptoms or management today?" 
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [expandedChips, setExpandedChips] = useState({});
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);

  const messagesEndRef = useRef(null);
  const USER_ID = 1;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, expandedChips]);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await axios.get(`http://localhost:8000/api/history/${USER_ID}`);
        if (Array.isArray(res.data) && res.data.length > 0) {
          // Normalize old history as plain text messages
          const historyMessages = res.data.map(item => ({
            role: item.role === 'user' ? 'user' : 'ai',
            content: item.content || item.text || item.response || ''
          }));
          setMessages(historyMessages);
        }
      } catch (err) {
        console.warn('No history found or server unavailable');
      }
    };
    fetchHistory();
  }, []);

  const clearChat = async () => {
    try {
      await axios.delete(`http://localhost:8000/api/history/${USER_ID}`);
      setMessages([
        { 
          role: 'ai', 
          content: "Hello. I am the RespiraCare AI Assistant. How can I help you with your asthma symptoms or management today?" 
        }
      ]);
      setExpandedChips({});
    } catch (err) {
      console.error('Failed to clear chat', err);
    }
  };

  const toggleChip = (msgIndex, chipIndex) => {
    const key = `${msgIndex}-${chipIndex}`;
    setExpandedChips(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const toggleListening = () => {
    if (isListening) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsListening(false);
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Voice input is not supported in this browser. Please open in Google Chrome or Microsoft Edge.");
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = 'en-US';
      recognition.interimResults = false;
      recognition.continuous = false;

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (transcript) {
          setInput(prev => (prev ? `${prev.trim()} ${transcript}` : transcript));
        }
      };

      recognition.onerror = (event) => {
        console.warn("Speech recognition error:", event.error);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.error("Speech recognition error:", err);
      setIsListening(false);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }

    const userMessage = input.trim();
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post('http://localhost:8000/api/chat', {
        user_id: USER_ID,
        query: userMessage
      });

      const data = response.data;
      const status = data.status;
      
      // Bot message text: if status == "clarify" show question, otherwise show answer
      let botContent = '';
      if (status === 'clarify') {
        botContent = data.question || data.answer || data.response || '';
      } else {
        botContent = data.answer || data.response || '';
      }

      setMessages(prev => [
        ...prev,
        {
          role: 'ai',
          status: status,
          content: botContent,
          citations: data.citations || []
        }
      ]);
    } catch (error) {
      setMessages(prev => [
        ...prev,
        {
          role: 'ai',
          status: 'error',
          content: "I'm having trouble connecting to the medical server. Please check your connection and try again."
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const renderAiMessage = (msg, index) => {
    const { status, content, citations } = msg;

    // 1. Emergency status: red banner at top labeled "Urgent: seek medical help now"
    if (status === 'emergency') {
      return (
        <div className="rounded-2xl overflow-hidden border border-red-300 shadow-md bg-white">
          <div className="bg-red-600 text-white font-bold text-sm px-5 py-2.5 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>Urgent: seek medical help now</span>
          </div>
          <div className="p-5 bg-red-50/70 text-red-950 font-medium">
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
                strong: ({ children }) => <strong className="font-bold text-red-900">{children}</strong>,
                ul: ({ children }) => <ul className="list-disc pl-5 mb-2 space-y-1">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal pl-5 mb-2 space-y-1">{children}</ol>,
                li: ({ children }) => <li className="leading-relaxed">{children}</li>,
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        </div>
      );
    }

    // 2. Clarify status: blue bubble labelled "Follow-up question"
    if (status === 'clarify') {
      return (
        <div className="bg-blue-50 border border-blue-200 text-blue-950 rounded-3xl rounded-tl-sm px-6 py-4 shadow-sm">
          <div className="text-xs font-bold uppercase tracking-wider text-blue-700 mb-2 flex items-center gap-1.5">
            <HelpCircle className="w-4 h-4" />
            <span>Follow-up question</span>
          </div>
          <div className="text-[15px] leading-relaxed font-medium">
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
                strong: ({ children }) => <strong className="font-bold text-blue-900">{children}</strong>,
                ul: ({ children }) => <ul className="list-disc pl-5 mb-2 space-y-1">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal pl-5 mb-2 space-y-1">{children}</ol>,
                li: ({ children }) => <li className="leading-relaxed">{children}</li>,
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        </div>
      );
    }

    // 3. No match status: amber card labelled "No reliable answer"
    if (status === 'no_match') {
      return (
        <div className="bg-amber-50 border border-amber-200 text-amber-950 rounded-2xl p-5 shadow-sm">
          <div className="text-xs font-bold uppercase tracking-wider text-amber-800 mb-2 flex items-center gap-1.5">
            <AlertCircle className="w-4 h-4" />
            <span>No reliable answer</span>
          </div>
          <div className="text-[15px] leading-relaxed">
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
                strong: ({ children }) => <strong className="font-bold text-amber-900">{children}</strong>,
                ul: ({ children }) => <ul className="list-disc pl-5 mb-2 space-y-1">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal pl-5 mb-2 space-y-1">{children}</ol>,
                li: ({ children }) => <li className="leading-relaxed">{children}</li>,
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        </div>
      );
    }

    // 4. Blocked status: grey card
    if (status === 'blocked') {
      return (
        <div className="bg-slate-100 border border-slate-300 text-slate-800 rounded-2xl p-5 shadow-sm">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-2 flex items-center gap-1.5">
            <ShieldAlert className="w-4 h-4" />
            <span>Request Blocked</span>
          </div>
          <div className="text-[15px] leading-relaxed">
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
                strong: ({ children }) => <strong className="font-bold text-slate-900">{children}</strong>,
                ul: ({ children }) => <ul className="list-disc pl-5 mb-2 space-y-1">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal pl-5 mb-2 space-y-1">{children}</ol>,
                li: ({ children }) => <li className="leading-relaxed">{children}</li>,
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        </div>
      );
    }

    // 5. Default/Answer status: standard bubble with optional citations
    return (
      <div className="bg-white text-slate-800 rounded-3xl rounded-tl-sm border border-slate-200 px-6 py-4 shadow-sm">
        <div className="text-[15px] leading-relaxed">
          <ReactMarkdown
            components={{
              p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
              strong: ({ children }) => <strong className="font-semibold text-slate-900">{children}</strong>,
              ul: ({ children }) => <ul className="list-disc pl-5 mb-2 space-y-1">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal pl-5 mb-2 space-y-1">{children}</ol>,
              li: ({ children }) => <li className="leading-relaxed">{children}</li>,
            }}
          >
            {content}
          </ReactMarkdown>
        </div>

        {/* Numbered source chips under the message for status "answer" */}
        {status === 'answer' && Array.isArray(citations) && citations.length > 0 && (
          <div className="mt-4 pt-3 border-t border-slate-100">
            <div className="text-xs font-semibold text-slate-500 mb-2 flex items-center gap-1.5">
              <span>Sources ({citations.length}):</span>
            </div>
            <div className="flex flex-col gap-2">
              <div className="flex flex-wrap gap-2">
                {citations.map((cit, cIdx) => {
                  const isExpanded = expandedChips[`${index}-${cIdx}`];
                  return (
                    <button
                      key={cIdx}
                      type="button"
                      onClick={() => toggleChip(index, cIdx)}
                      className={`text-xs px-3 py-1.5 rounded-xl border font-medium flex items-center gap-1.5 transition-all text-left ${
                        isExpanded
                          ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                          : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                      }`}
                    >
                      <span className="font-bold">[{cIdx + 1}]</span>
                      <span>{cit.source ? `${cit.source}: ` : ''}{cit.title || 'Reference'}</span>
                    </button>
                  );
                })}
              </div>

              {/* Expanded details below the chips */}
              {citations.map((cit, cIdx) => {
                const isExpanded = expandedChips[`${index}-${cIdx}`];
                if (!isExpanded) return null;

                return (
                  <div key={`exp-${cIdx}`} className="p-4 bg-slate-50 rounded-2xl border border-slate-200 text-xs text-slate-700 space-y-2 mt-1">
                    <div className="font-bold text-slate-900 flex items-center justify-between">
                      <span>[{cIdx + 1}] {cit.source}: {cit.title}</span>
                      {cit.url && (
                        <a
                          href={cit.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-blue-600 hover:underline"
                        >
                          <span>Open link</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                    <p className="leading-relaxed whitespace-pre-wrap text-slate-600 border-t border-slate-200/60 pt-2">
                      {cit.text}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-50 relative overflow-hidden py-8">
      {/* Decorative background */}
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-blue-100 rounded-full mix-blend-multiply filter blur-[100px] opacity-40"></div>
      <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-indigo-100 rounded-full mix-blend-multiply filter blur-[100px] opacity-40"></div>

      <div className="max-w-4xl mx-auto px-4 relative z-10">
        
        {/* Permanent Banner above the chat */}
        <div className="bg-amber-50/90 border border-amber-200 text-amber-900 px-4 py-3 rounded-2xl mb-4 text-xs sm:text-sm font-medium flex items-center gap-2.5 shadow-sm">
          <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />
          <span>General information only, not a diagnosis. In an emergency call your local emergency number.</span>
        </div>

        {/* Dashboard Header */}
        <div className="mb-6 flex justify-between items-center bg-white/60 backdrop-blur-md p-6 rounded-3xl shadow-sm border border-white">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-blue-600 rounded-2xl shadow-sm text-white">
              <HeartPulse className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900 tracking-tight">RespiraCare AI</h1>
              <p className="text-slate-500 font-medium text-xs sm:text-sm">Asthma Information Assistant</p>
            </div>
          </div>

          <button 
            onClick={clearChat}
            className="group bg-white text-slate-600 border border-slate-200 px-4 py-2.5 rounded-2xl font-semibold hover:bg-slate-50 hover:text-slate-900 transition-all shadow-sm flex items-center gap-2 text-sm"
          >
            <RefreshCw className="w-4 h-4 group-hover:rotate-180 transition-transform duration-500" />
            <span>New Chat</span>
          </button>
        </div>

        {/* Chat Window */}
        <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-sm border border-white/80 overflow-hidden flex flex-col h-[650px]">
          
          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.map((msg, index) => (
              <div 
                key={index} 
                className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
              >
                {/* Avatar */}
                <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm ${
                  msg.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-blue-100 text-blue-600'
                }`}>
                  {msg.role === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
                </div>

                {/* Message Body */}
                <div className="max-w-[85%] sm:max-w-[78%]">
                  {msg.role === 'user' ? (
                    <div className="bg-indigo-600 text-white rounded-3xl rounded-tr-sm px-6 py-4 shadow-sm text-[15px] font-medium leading-relaxed">
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  ) : (
                    renderAiMessage(msg, index)
                  )}
                </div>
              </div>
            ))}

            {/* Loading Indicator */}
            {isLoading && (
              <div className="flex gap-4 flex-row items-center">
                <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center shadow-sm text-blue-600">
                  <Bot className="w-5 h-5" />
                </div>
                <div className="bg-white text-slate-600 rounded-3xl rounded-tl-sm px-6 py-4 shadow-sm border border-slate-100 flex items-center gap-3">
                  <span className="text-sm font-medium">Checking safety, searching sources, verifying answer</span>
                  <div className="flex gap-1 items-center">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-bounce"></span>
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-bounce [animation-delay:0.2s]"></span>
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-bounce [animation-delay:0.4s]"></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-4 bg-white border-t border-slate-100">
            {isListening && (
              <div className="mb-2 px-3.5 py-2 bg-red-50 border border-red-200 rounded-xl flex items-center justify-between text-xs text-red-700 font-semibold animate-pulse">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-red-600 animate-ping"></span>
                  <span>Listening... Speak clearly. Tap mic or Send when done.</span>
                </div>
                <button
                  type="button"
                  onClick={toggleListening}
                  className="text-red-600 hover:text-red-800 underline text-xs font-bold"
                >
                  Cancel
                </button>
              </div>
            )}
            <form onSubmit={handleSend} className="flex gap-2 sm:gap-3 items-center">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={isListening ? "Listening... speak now" : "Ask about asthma symptoms, triggers, or management..."}
                className="flex-1 bg-slate-50 border border-slate-200 rounded-2xl px-5 py-3.5 text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:bg-white transition-all shadow-inner disabled:bg-slate-100 disabled:cursor-not-allowed text-sm sm:text-base"
                disabled={isLoading}
              />
              <button 
                type="button"
                onClick={toggleListening}
                disabled={isLoading}
                title={isListening ? "Stop listening" : "Click to speak (Voice Input)"}
                className={`p-3.5 rounded-2xl font-semibold transition-all shadow-sm flex items-center justify-center flex-shrink-0 ${
                  isListening 
                    ? 'bg-red-500 text-white animate-pulse shadow-md ring-2 ring-red-300' 
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-800'
                }`}
              >
                {isListening ? <MicOff className="w-5 h-5 text-white" /> : <Mic className="w-5 h-5" />}
              </button>
              <button 
                type="submit"
                disabled={isLoading || !input.trim()}
                className="bg-blue-600 text-white px-5 py-3.5 rounded-2xl font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:hover:bg-blue-600 transition-all shadow-sm flex items-center justify-center gap-2 flex-shrink-0"
                title="Send Message"
              >
                <Send className="w-5 h-5" />
              </button>
            </form>
          </div>
        </div>

      </div>
    </div>
  );
}

export default Chat;
