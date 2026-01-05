import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LayoutDashboard, TrendingUp, Sparkles, LogOut, Target, Plus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import Toast from '../../components/Toast';
import DeleteModal from '../../components/DeleteModal';
import AddModal from '../../components/AddModal';
import Overview from './Overview';
import Assets from './Assets';
import Advisor from './Advisor'; // Import the new Smart Component

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const Dashboard = () => {
    const navigate = useNavigate();
    const [view, setView] = useState('dashboard');

    // Dashboard State Only
    const [data, setData] = useState({
        user_profile: { salary: 0, rent: 0 },
        health: { score: 0, net_worth: 0, surplus: 0, allocation: {}, monthly_burn: 0 },
        lists: { expenses: [], assets: [], liabilities: [], goals: [] }
    });

    const [showModal, setShowModal] = useState(null);
    const [deleteConfirm, setDeleteConfirm] = useState(null);
    const [toast, setToast] = useState(null);

    // REMOVED: chatLog, aiQuery, loading (Moved to Advisor.jsx)

    const showToast = (msg, type = 'success') => {
        setToast({ msg, type });
        setTimeout(() => setToast(null), 3000);
    };

    const fetchData = async () => {
        const token = localStorage.getItem('token');
        if (!token) return navigate('/');
        try {
            const res = await axios.get(`${API_URL}/data`, { headers: { Authorization: `Bearer ${token}` } });
            if (res.data) setData(res.data);
        } catch (err) { console.error(err); }
    };

    useEffect(() => { fetchData(); }, []);

    const handleSave = async (endpoint, payload) => {
        try {
            await axios.post(`${API_URL}/${endpoint}`, payload, { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });
            setShowModal(null);
            fetchData();
            showToast('Saved successfully');
        } catch (e) { showToast('Error saving', 'error'); }
    };

    const handleDelete = async () => {
        if (!deleteConfirm) return;
        try {
            await axios.delete(`${API_URL}/${deleteConfirm.endpoint}/${deleteConfirm.id}`, { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });
            setDeleteConfirm(null);
            fetchData();
            showToast('Deleted');
        } catch (e) { showToast('Delete failed', 'error'); }
    };

    // REMOVED: handleAi (Moved to Advisor.jsx)

    return (
        <div className="pb-28 max-w-lg mx-auto relative z-10 min-h-screen flex flex-col">
            {toast && <Toast msg={toast.msg} type={toast.type} />}
            {deleteConfirm && <DeleteModal onConfirm={handleDelete} onCancel={() => setDeleteConfirm(null)} />}
            {showModal && <AddModal type={showModal} onClose={() => setShowModal(null)} onSave={handleSave} />}

            <header className="px-6 py-5 flex justify-between items-center bg-slate-950/80 backdrop-blur-md sticky top-0 z-20">
                <div className="flex items-center gap-2">
                    <div className="bg-blue-600 p-1.5 rounded-lg"><Sparkles size={16} className="text-white" /></div>
                    <span className="font-bold text-white">Score: {data.health?.score || 0}/100</span>
                </div>
                <button onClick={() => { localStorage.removeItem('token'); navigate('/') }}><LogOut size={18} className="text-slate-400 hover:text-red-400" /></button>
            </header>

            <main className="px-5 flex-1 space-y-6 mt-2">
                {view === 'dashboard' && (
                    <Overview
                        data={data}
                        onAddExpense={() => setShowModal('expense')}
                        onDelete={(endpoint, id) => setDeleteConfirm({ endpoint: endpoint, id: id })}
                    />
                )}
                {view === 'assets' && (
                    <Assets
                        data={data}
                        onAdd={(type) => setShowModal(type)}
                        onDelete={(endpoint, id) => setDeleteConfirm({ endpoint: endpoint, id: id })}
                    />
                )}
                {/* Simple Render: No props needed anymore! */}
                {view === 'advisor' && <Advisor />}
            </main>

            <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 w-[90%] max-w-sm z-50">
                <div className="glass-panel rounded-full px-6 py-3 flex justify-between items-center shadow-2xl backdrop-blur-xl border border-white/10">
                    <button onClick={() => setView('dashboard')} className={view === 'dashboard' ? 'text-white' : 'text-slate-500 hover:text-slate-300'}><LayoutDashboard /></button>
                    <button onClick={() => setView('assets')} className={view === 'assets' ? 'text-white' : 'text-slate-500 hover:text-slate-300'}><Target /></button>
                    <button onClick={() => setShowModal('expense')} className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-4 rounded-full -mt-8 shadow-lg border-4 border-slate-950 hover:scale-105 transition-transform"><Plus size={28} /></button>
                    <button onClick={() => setView('advisor')} className={view === 'advisor' ? 'text-white' : 'text-slate-500 hover:text-slate-300'}><Sparkles /></button>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;