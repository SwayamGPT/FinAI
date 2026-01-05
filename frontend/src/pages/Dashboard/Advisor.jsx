import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, Bot, User, Lock } from 'lucide-react'; // Added Lock icon

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const Advisor = () => {
    const [query, setQuery] = useState('');
    const [chatLog, setChatLog] = useState([]);
    const [loading, setLoading] = useState(false);
    const chatEndRef = useRef(null);

    // 1. Fetch History on Load
    useEffect(() => {
        const fetchHistory = async () => {
            const token = localStorage.getItem('token');
            if (!token) return;
            try {
                const res = await axios.get(`${API_URL}/advisor/history`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                if (res.data && Array.isArray(res.data)) {
                    setChatLog(res.data);
                }
            } catch (err) {
                console.error("Failed to load history", err);
            }
        };
        fetchHistory();
    }, []);

    // Scroll to bottom when log updates
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [chatLog]);

    const handleSend = async () => {
        if (!query.trim()) return;

        const currentQuery = query;
        setQuery('');
        setLoading(true);

        const newLog = [...chatLog, { role: 'user', content: currentQuery }];
        setChatLog(newLog);

        try {
            const token = localStorage.getItem('token');
            const res = await axios.post(
                `${API_URL}/advisor`,
                { query: currentQuery },
                { headers: { Authorization: `Bearer ${token}` } }
            );

            const aiResponse = res.data?.content || "No response.";
            setChatLog([...newLog, { role: 'ai', content: aiResponse }]);
        } catch (err) {
            setChatLog([...newLog, { role: 'ai', content: "Connection error." }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-[70vh]">
            {/* Header with Encryption Badge */}
            <div className="flex justify-center mb-2">
                <span className="text-[10px] text-emerald-500/60 flex items-center gap-1 bg-emerald-900/10 px-2 py-1 rounded-full border border-emerald-900/20">
                    <Lock size={10} /> End-to-End Encrypted Storage
                </span>
            </div>

            <div className="glass-panel flex-1 rounded-3xl p-4 overflow-y-auto mb-4 no-scrollbar flex flex-col gap-3">
                {chatLog.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-slate-500 space-y-4">
                        <div className="bg-slate-800 p-4 rounded-full mb-2"><Bot size={40} className="text-blue-400" /></div>
                        <p>Your history is empty. Start a secured conversation!</p>
                    </div>
                )}

                {chatLog.map((msg, i) => (
                    <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-blue-600' : 'bg-emerald-600'}`}>
                            {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                        </div>
                        <div className={`p-3 rounded-2xl text-sm max-w-[80%] ${msg.role === 'user' ? 'bg-blue-600/20 text-blue-100 rounded-tr-none' : 'bg-slate-800 text-slate-200 rounded-tl-none'}`}>
                            {msg.content}
                        </div>
                    </div>
                ))}

                {loading && (
                    <div className="flex gap-3">
                        <div className="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center"><Bot size={16} /></div>
                        <div className="bg-slate-800 p-4 rounded-2xl rounded-tl-none flex gap-2 items-center">
                            <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" />
                            <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce delay-75" />
                            <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce delay-150" />
                        </div>
                    </div>
                )}
                <div ref={chatEndRef} />
            </div>

            <div className="relative">
                <input
                    className="w-full p-4 pr-12 rounded-full glass-input shadow-lg focus:ring-2 focus:ring-blue-500/50"
                    value={query}
                    onChange={e => setQuery(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleSend()}
                    placeholder="Ask safely..."
                    disabled={loading}
                />
                <button
                    onClick={handleSend}
                    disabled={loading || !query.trim()}
                    className="absolute right-2 top-2 p-2 bg-blue-600 hover:bg-blue-500 rounded-full text-white"
                >
                    <Send size={18} />
                </button>
            </div>
        </div>
    );
};

export default Advisor;