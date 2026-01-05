import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { LayoutDashboard, Plus, LogOut, Sparkles, X, Trash2, Target, CheckCircle, AlertTriangle, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const Dashboard = () => {
    const navigate = useNavigate();
    const [view, setView] = useState('dashboard');

    // --- STATE ---
    // Added safety defaults to prevent "cannot read property of undefined" errors
    const [data, setData] = useState({
        user_profile: { salary: 0, rent: 0 },
        health: { score: 0, net_worth: 0, emergency_months: 0, debt_ratio: 0, surplus: 0, allocation: {}, monthly_burn: 0 },
        lists: { expenses: [], assets: [], liabilities: [], goals: [] }
    });

    // UI States
    const [showModal, setShowModal] = useState(null);
    const [deleteConfirm, setDeleteConfirm] = useState(null);
    const [toast, setToast] = useState(null);

    // Forms
    const [expenseForm, setExpenseForm] = useState({ amount: '', title: '', category: 'Food' });
    const [assetForm, setAssetForm] = useState({ name: '', type: 'Mutual Fund', value: '', liquidity_score: 5 });
    const [goalForm, setGoalForm] = useState({ name: '', target_amount: '', target_date: '', priority: 'Medium' });
    const [liabForm, setLiabForm] = useState({ name: '', type: 'Credit Card', outstanding_amount: '', interest_rate: '', monthly_payment: '' });

    // Chat
    const [chatLog, setChatLog] = useState([]);
    const [aiQuery, setAiQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const chatEndRef = useRef(null);

    useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [chatLog]);
    useEffect(() => { fetchData(); }, []);

    // --- HELPERS ---
    const logout = () => { localStorage.removeItem('token'); navigate('/'); };
    const preventMinus = (e) => { if (["-", "+", "e", "E"].includes(e.key)) e.preventDefault(); };

    const showToast = (msg, type = 'success') => {
        setToast({ msg, type });
        setTimeout(() => setToast(null), 3000);
    };

    // --- DATA ACTIONS ---
    const fetchData = async () => {
        const token = localStorage.getItem('token');
        if (!token) return navigate('/');
        try {
            const res = await axios.get(`${API_URL}/data`, { headers: { Authorization: `Bearer ${token}` } });
            // SAFETY CHECK: Ensure data structure exists before setting
            if (res.data && res.data.health) {
                setData(res.data);
            }
        } catch (err) {
            if (err.response?.status === 401) logout();
            // Don't toast on every fetch error to avoid spamming the user
            console.error("Fetch error:", err);
        }
    };

    const postData = async (endpoint, payload) => {
        try {
            await axios.post(`${API_URL}/${endpoint}`, payload, { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });
            setShowModal(null);
            fetchData();
            showToast("Saved successfully!");
        } catch (e) { showToast("Error saving data", "error"); }
    };

    const executeDelete = async () => {
        if (!deleteConfirm) return;
        try {
            await axios.delete(`${API_URL}/${deleteConfirm.endpoint}/${deleteConfirm.id}`, {
                headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
            });
            setDeleteConfirm(null);
            fetchData();
            showToast("Deleted successfully");
        } catch (e) { showToast("Failed to delete", "error"); }
    };

    const handleAi = async (query = aiQuery) => {
        if (!query) return;

        // 1. Update UI immediately
        const newLog = [...chatLog.slice(-20), { role: 'user', content: query }];
        setChatLog(newLog);
        setAiQuery('');
        setLoading(true);

        try {
            const res = await axios.post(`${API_URL}/advisor`, { query },
                { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });

            // 2. CRITICAL SAFETY CHECK: Verify response structure before accessing .content
            // If res.data is null or content is missing, use a fallback string to prevent CRASH.
            const aiResponse = res.data?.content || "I couldn't generate a response. Please try again.";

            setChatLog([...newLog, { role: 'ai', content: aiResponse }]);
        } catch (err) {
            console.error("AI Error:", err);
            setChatLog([...newLog, { role: 'ai', content: "Error: Could not reach the advisor." }]);
        }
        setLoading(false);
    };

    // --- RENDER HELPERS ---
    // Safety check: Ensure lists.expenses exists, default to [] if undefined
    const totalSpent = (data.lists?.expenses || []).reduce((acc, curr) => acc + (curr.amount || 0), 0);

    const chartData = [
        { name: 'Rent', value: data.user_profile?.rent || 0, color: '#f87171' },
        { name: 'Spent', value: totalSpent, color: '#fbbf24' },
        { name: 'Investable', value: Math.max(0, data.health?.surplus || 0), color: '#34d399' }
    ];

    const isOverspending = (data.health?.surplus || 0) < 0;
    const overspendAmount = Math.abs(data.health?.surplus || 0);

    return (
        <div className="pb-28 max-w-lg mx-auto relative z-10 min-h-screen flex flex-col">

            {/* --- TOAST NOTIFICATION --- */}
            {toast && (
                <div className={`fixed top-6 left-1/2 -translate-x-1/2 z-[60] px-4 py-3 rounded-xl shadow-2xl flex items-center gap-3 backdrop-blur-md border animate-in slide-in-from-top-4 duration-300 ${toast.type === 'error' ? 'bg-red-900/80 border-red-500/50 text-red-200' : 'bg-emerald-900/80 border-emerald-500/50 text-emerald-200'}`}>
                    {toast.type === 'error' ? <AlertCircle size={18} /> : <CheckCircle size={18} />}
                    <span className="text-sm font-medium">{toast.msg}</span>
                </div>
            )}

            {/* --- DELETE CONFIRMATION MODAL --- */}
            {deleteConfirm && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                    <div className="glass-panel w-full max-w-xs p-6 rounded-3xl border border-red-500/30 text-center animate-in zoom-in-95">
                        <div className="bg-red-500/20 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Trash2 className="text-red-400" size={24} />
                        </div>
                        <h3 className="text-white font-bold text-lg">Delete this item?</h3>
                        <p className="text-slate-400 text-sm mt-2 mb-6">This action cannot be undone.</p>
                        <div className="flex gap-3">
                            <button onClick={() => setDeleteConfirm(null)} className="flex-1 py-3 bg-slate-700 hover:bg-slate-600 rounded-xl font-bold text-white text-sm">Cancel</button>
                            <button onClick={executeDelete} className="flex-1 py-3 bg-red-600 hover:bg-red-500 rounded-xl font-bold text-white text-sm">Delete</button>
                        </div>
                    </div>
                </div>
            )}

            {/* --- INPUT MODALS --- */}
            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                    <div className="glass-panel w-full max-w-sm p-6 rounded-3xl border border-slate-600 animate-in zoom-in-95 duration-200">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-white font-bold capitalize">Add {showModal}</h3>
                            <button onClick={() => setShowModal(null)}><X className="text-slate-400" /></button>
                        </div>
                        {/* EXPENSE FORM */}
                        {showModal === 'expense' && <div className="space-y-3">
                            <input className="glass-input w-full p-3 rounded-xl" placeholder="Title" onChange={e => setExpenseForm({ ...expenseForm, title: e.target.value })} />
                            <input className="glass-input w-full p-3 rounded-xl" type="number" onKeyDown={preventMinus} placeholder="Amount" onChange={e => setExpenseForm({ ...expenseForm, amount: Number(e.target.value) })} />
                            <button onClick={() => postData('expenses', expenseForm)} className="w-full bg-blue-600 p-3 rounded-xl font-bold text-white">Save</button>
                        </div>}
                        {/* ASSET FORM */}
                        {showModal === 'asset' && <div className="space-y-3">
                            <input className="glass-input w-full p-3 rounded-xl" placeholder="Name" onChange={e => setAssetForm({ ...assetForm, name: e.target.value })} />
                            <select className="glass-input w-full p-3 rounded-xl bg-slate-800" onChange={e => setAssetForm({ ...assetForm, type: e.target.value })}>
                                {['Mutual Fund', 'Stock', 'Gold', 'Real Estate', 'Crypto', 'Bank'].map(t => <option key={t} value={t}>{t}</option>)}
                            </select>
                            <input className="glass-input w-full p-3 rounded-xl" type="number" onKeyDown={preventMinus} placeholder="Value" onChange={e => setAssetForm({ ...assetForm, value: Number(e.target.value) })} />
                            <select className="glass-input w-full p-3 rounded-xl bg-slate-800" onChange={e => setAssetForm({ ...assetForm, liquidity_score: Number(e.target.value) })}>
                                <option value="5">High Liquidity (Cash/Bank)</option>
                                <option value="4">Good Liquidity (MF/Stocks)</option>
                                <option value="1">Locked (Real Estate/PF)</option>
                            </select>
                            <button onClick={() => postData('assets', assetForm)} className="w-full bg-emerald-600 p-3 rounded-xl font-bold text-white">Save Asset</button>
                        </div>}
                        {/* LIABILITY FORM */}
                        {showModal === 'liability' && <div className="space-y-3">
                            <input className="glass-input w-full p-3 rounded-xl" placeholder="Name" onChange={e => setLiabForm({ ...liabForm, name: e.target.value })} />
                            <select className="glass-input w-full p-3 rounded-xl bg-slate-800" value={liabForm.type} onChange={e => setLiabForm({ ...liabForm, type: e.target.value })}>
                                {['Credit Card', 'Personal Loan', 'Home Loan', 'Car Loan', 'EMI'].map(t => <option key={t} value={t}>{t}</option>)}
                            </select>
                            <input className="glass-input w-full p-3 rounded-xl" type="number" onKeyDown={preventMinus} placeholder="Outstanding Amount" onChange={e => setLiabForm({ ...liabForm, outstanding_amount: Number(e.target.value) })} />
                            <input className="glass-input w-full p-3 rounded-xl" type="number" onKeyDown={preventMinus} placeholder="Interest Rate %" onChange={e => setLiabForm({ ...liabForm, interest_rate: Number(e.target.value) })} />
                            <input className="glass-input w-full p-3 rounded-xl" type="number" onKeyDown={preventMinus} placeholder="Monthly EMI" onChange={e => setLiabForm({ ...liabForm, monthly_payment: Number(e.target.value) })} />
                            <button onClick={() => postData('liabilities', liabForm)} className="w-full bg-red-600 p-3 rounded-xl font-bold text-white">Add Debt</button>
                        </div>}
                        {/* GOAL FORM */}
                        {showModal === 'goal' && <div className="space-y-3">
                            <input className="glass-input w-full p-3 rounded-xl" placeholder="Goal Name" onChange={e => setGoalForm({ ...goalForm, name: e.target.value })} />
                            <input className="glass-input w-full p-3 rounded-xl" type="number" onKeyDown={preventMinus} placeholder="Target Amount" onChange={e => setGoalForm({ ...goalForm, target_amount: Number(e.target.value) })} />
                            <input className="glass-input w-full p-3 rounded-xl text-slate-400" type="date" onChange={e => setGoalForm({ ...goalForm, target_date: e.target.value })} />
                            <button onClick={() => postData('goals', goalForm)} className="w-full bg-purple-600 p-3 rounded-xl font-bold text-white">Set Goal</button>
                        </div>}
                    </div>
                </div>
            )}

            <header className="px-6 py-5 flex justify-between items-center bg-slate-950/80 backdrop-blur-md sticky top-0 z-20">
                <div className="flex items-center gap-2">
                    <div className="bg-blue-600 p-1.5 rounded-lg"><Sparkles size={16} className="text-white" /></div>
                    <span className="font-bold text-white">Score: {data.health?.score || 0}/100</span>
                </div>
                <button onClick={logout}><LogOut size={18} className="text-slate-400 hover:text-red-400" /></button>
            </header>

            <main className="px-5 flex-1 space-y-6 mt-2">
                {/* DASHBOARD VIEW */}
                {view === 'dashboard' && (
                    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

                        {/* OVERSPENDING WARNING CARD */}
                        {isOverspending && (
                            <div className="bg-red-500/10 border border-red-500/50 rounded-2xl p-4 flex items-center gap-4">
                                <div className="bg-red-500/20 p-2 rounded-full text-red-400">
                                    <AlertTriangle size={24} />
                                </div>
                                <div>
                                    <h3 className="text-red-200 font-bold">You are overspending!</h3>
                                    <p className="text-red-300/80 text-xs">
                                        Deficit of <span className="font-bold text-red-200">₹{overspendAmount.toLocaleString()}</span> this month.
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* Main Budget Card */}
                        <div className="bg-gradient-to-br from-indigo-900 to-slate-900 rounded-3xl p-6 border border-indigo-500/30 shadow-lg">
                            <div className="flex justify-between">
                                <div>
                                    <p className="text-indigo-200 text-xs uppercase tracking-widest font-semibold">Available to Spend</p>
                                    <h2 className="text-3xl font-bold text-white mt-1">₹{(data.health?.surplus || 0).toLocaleString()}</h2>
                                </div>
                                <div className="text-right">
                                    <p className="text-emerald-400 text-xs uppercase tracking-widest font-semibold">Should Invest</p>
                                    <h2 className="text-xl font-bold text-emerald-400 mt-1">₹{(data.health?.recommended_investment || 0).toLocaleString()}</h2>
                                </div>
                            </div>
                            <div className="mt-4 flex gap-4 text-xs">
                                <div className="text-slate-400">Monthly Burn: ₹{(data.health?.monthly_burn || 0).toLocaleString()}</div>
                                <div className="text-slate-400">Net Worth: <span className={(data.health?.net_worth || 0) >= 0 ? "text-emerald-400" : "text-red-400"}>₹{(data.health?.net_worth || 0).toLocaleString()}</span></div>
                            </div>
                        </div>

                        <div className="glass-panel p-5 rounded-3xl h-64 relative">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie data={chartData} innerRadius={60} outerRadius={80} dataKey="value" stroke="none">
                                        {chartData.map((e, i) => <Cell key={i} fill={e.color} />)}
                                    </Pie>
                                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', border: 'none' }} />
                                </PieChart>
                            </ResponsiveContainer>
                            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                                <div className="text-center">
                                    <div className="text-xs text-slate-500">Total Spent</div>
                                    <div className="text-xl font-bold text-amber-400">₹{totalSpent}</div>
                                </div>
                            </div>
                        </div>

                        {/* Recent Activity */}
                        <div>
                            <div className="flex justify-between items-center mb-3">
                                <h3 className="text-white font-bold">Recent Activity</h3>
                                <button onClick={() => setShowModal('expense')} className="text-xs bg-blue-600/20 text-blue-400 px-3 py-1 rounded-full">+ Expense</button>
                            </div>
                            <div className="space-y-2">
                                {(data.lists?.expenses || []).slice(0, 5).map((exp, i) => (
                                    <div key={i} className="glass-panel p-3 rounded-xl flex justify-between items-center">
                                        <div><div className="text-slate-200 text-sm">{exp.title}</div></div>
                                        <div className="flex items-center gap-3">
                                            <span className="text-white font-bold">₹{exp.amount}</span>
                                            <button onClick={() => setDeleteConfirm({ endpoint: 'expenses', id: exp.id })} className="text-slate-600 hover:text-red-500"><Trash2 size={14} /></button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* ASSETS VIEW */}
                {view === 'assets' && (
                    <div className="space-y-6 animate-in fade-in slide-in-from-right duration-300">
                        <div>
                            <div className="flex justify-between items-center mb-3">
                                <h2 className="text-xl font-bold text-white">Assets</h2>
                                <button onClick={() => setShowModal('asset')} className="bg-emerald-600 p-2 rounded-lg text-white"><Plus size={18} /></button>
                            </div>
                            {(data.lists?.assets || []).map((a, i) => (
                                <div key={i} className="glass-panel p-4 rounded-xl border-l-4 border-emerald-500 flex justify-between mb-2">
                                    <div><div className="font-bold">{a.name}</div><div className="text-xs text-slate-400">{a.type}</div></div>
                                    <div className="text-right"><div className="font-bold">₹{a.value}</div><button onClick={() => setDeleteConfirm({ endpoint: 'assets', id: a.id })} className="text-xs text-red-400">Remove</button></div>
                                </div>
                            ))}
                        </div>
                        <div>
                            <div className="flex justify-between items-center mb-3">
                                <h2 className="text-xl font-bold text-white">Liabilities</h2>
                                <button onClick={() => setShowModal('liability')} className="bg-red-600 p-2 rounded-lg text-white"><Plus size={18} /></button>
                            </div>
                            {(data.lists?.liabilities || []).map((l, i) => (
                                <div key={i} className="glass-panel p-4 rounded-xl border-l-4 border-red-500 flex justify-between mb-2">
                                    <div><div className="font-bold">{l.name}</div><div className="text-xs text-slate-400">EMI: ₹{l.monthly_payment}</div></div>
                                    <div className="text-right"><div className="font-bold text-red-400">₹{l.outstanding_amount}</div><button onClick={() => setDeleteConfirm({ endpoint: 'liabilities', id: l.id })} className="text-xs text-red-400">Remove</button></div>
                                </div>
                            ))}
                        </div>
                        <div>
                            <div className="flex justify-between items-center mb-3">
                                <h2 className="text-xl font-bold text-white">Goals</h2>
                                <button onClick={() => setShowModal('goal')} className="bg-purple-600 p-2 rounded-lg text-white"><Plus size={18} /></button>
                            </div>
                            {(data.lists?.goals || []).map((g, i) => (
                                <div key={i} className="glass-panel p-4 rounded-xl border-l-4 border-purple-500 mb-2">
                                    <div className="flex justify-between mb-1">
                                        <span className="font-bold">{g.name}</span>
                                        <span className={`text-xs px-2 py-0.5 rounded ${g.status === 'On Track' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>{g.status}</span>
                                    </div>
                                    <div className="flex justify-between text-xs text-slate-400 mt-2">
                                        <span>Target: ₹{g.target_amount}</span>
                                        <span>Save: <span className="text-white font-bold">₹{Math.round(g.required_monthly)}/mo</span></span>
                                    </div>
                                    <button onClick={() => setDeleteConfirm({ endpoint: 'goals', id: g.id })} className="text-xs text-red-400 mt-2">Delete</button>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* ADVISOR VIEW */}
                {view === 'advisor' && (
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
                                <div key={i} className={`p-3 my-2 rounded-xl text-sm max-w-[85%] ${msg.role === 'user' ? 'bg-blue-600 ml-auto text-white' : 'bg-slate-800 text-slate-200'}`}>{msg.content}</div>
                            ))}
                            {loading && <div className="text-xs text-slate-500 animate-pulse">Analyzing financials...</div>}
                            <div ref={chatEndRef} />
                        </div>
                        <div className="relative">
                            <input className="w-full p-4 pr-12 rounded-full glass-input shadow-lg" value={aiQuery} onChange={e => setAiQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleAi()} placeholder="Ask advisor..." />
                            <button onClick={() => handleAi()} className="absolute right-2 top-2 p-2 bg-blue-600 rounded-full text-white"><Send size={18} /></button>
                        </div>
                    </div>
                )}
            </main>

            {/* Bottom Navigation */}
            <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 w-[90%] max-w-sm z-50">
                <div className="glass-panel rounded-full px-6 py-3 flex justify-between items-center shadow-2xl backdrop-blur-xl border border-white/10">
                    <button onClick={() => setView('dashboard')} className={view === 'dashboard' ? 'text-white' : 'text-slate-500 hover:text-slate-300'}><LayoutDashboard /></button>
                    <button onClick={() => setView('assets')} className={view === 'assets' ? 'text-white' : 'text-slate-500 hover:text-slate-300'}><Target /></button>
                    <button onClick={() => setShowModal('expense')} className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-4 rounded-full -mt-8 shadow-lg shadow-blue-900/50 border-4 border-slate-950 hover:scale-105 transition-transform"><Plus size={28} /></button>
                    <button onClick={() => setView('advisor')} className={view === 'advisor' ? 'text-white' : 'text-slate-500 hover:text-slate-300'}><Sparkles /></button>
                </div>
            </div>
        </div>
    );
};
export default Dashboard;