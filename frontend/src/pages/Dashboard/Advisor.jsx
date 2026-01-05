import React, { useRef, useEffect } from 'react';
import { Send } from 'lucide-react';

const Advisor = ({ chatLog, aiQuery, setAiQuery, handleAi, loading }) => {
    const chatEndRef = useRef(null);

    useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [chatLog]);

    return (
        <div className="flex flex-col h-[70vh]">
            <div className="glass-panel flex-1 rounded-3xl p-4 overflow-y-auto mb-4 no-scrollbar">
                {chatLog.length === 0 && (
                    <div className="space-y-4 mt-8">
                        <p className="text-center text-slate-500">Quick Actions</p>
                        <div className="grid grid-cols-2 gap-2">
                            <button onClick={() => handleAi("How is my financial health?")} className="bg-slate-800 p-3 rounded-xl text-xs text-left hover:bg-slate-700">🩺 Check Health</button>
                            <button onClick={() => handleAi("Can I afford a vacation?")} className="bg-slate-800 p-3 rounded-xl text-xs text-left hover:bg-slate-700">✈️ Can I afford it?</button>
                            <button onClick={() => handleAi("How to reduce my debt?")} className="bg-slate-800 p-3 rounded-xl text-xs text-left hover:bg-slate-700">📉 Reduce Debt</button>
                            <button onClick={() => handleAi("Best investment for 30k?")} className="bg-slate-800 p-3 rounded-xl text-xs text-left hover:bg-slate-700">📈 Invest 30k</button>
                        </div>
                    </div>
                )}
                {chatLog.map((msg, i) => (
                    <div key={i} className={`p-3 my-2 rounded-xl text-sm max-w-[85%] ${msg.role === 'user' ? 'bg-blue-600 ml-auto text-white' : 'bg-slate-800 text-slate-200'}`}>
                        {msg.content}
                    </div>
                ))}
                {loading && <div className="text-xs text-slate-500 animate-pulse">Analyzing financials...</div>}
                <div ref={chatEndRef} />
            </div>
            <div className="relative">
                <input
                    className="w-full p-4 pr-12 rounded-full glass-input shadow-lg"
                    value={aiQuery}
                    onChange={e => setAiQuery(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleAi()}
                    placeholder="Ask advisor..."
                />
                <button onClick={() => handleAi()} className="absolute right-2 top-2 p-2 bg-blue-600 rounded-full text-white">
                    <Send size={18} />
                </button>
            </div>
        </div>
    );
};

export default Advisor;