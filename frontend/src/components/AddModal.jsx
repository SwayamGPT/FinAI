import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';

const AddModal = ({ type, onClose, onSave }) => {
    // Initialize form with smart defaults based on the modal type
    const [form, setForm] = useState({
        title: '', amount: '', category: 'Food', // Expense defaults

        name: '',
        // Dynamic Type Default: If adding liability, default to Credit Card. Else Mutual Fund.
        type: type === 'liability' ? 'Credit Card' : 'Mutual Fund',

        value: '', liquidity_score: 5, // Asset defaults

        outstanding_amount: '', interest_rate: '', monthly_payment: '', // Liability defaults

        target_amount: '', target_date: '', priority: 'Medium' // Goal defaults
    });

    // Reset form when modal type changes (just in case)
    useEffect(() => {
        setForm(prev => ({
            ...prev,
            type: type === 'liability' ? 'Credit Card' : 'Mutual Fund'
        }));
    }, [type]);

    const preventMinus = (e) => { if (["-", "+", "e", "E"].includes(e.key)) e.preventDefault(); };

    const handleSubmit = () => {
        const payload = { ...form };

        // Convert numeric strings to actual numbers
        ['amount', 'value', 'liquidity_score', 'outstanding_amount', 'interest_rate', 'monthly_payment', 'target_amount'].forEach(k => {
            if (payload[k] !== '' && payload[k] !== undefined) {
                payload[k] = Number(payload[k]);
            }
        });

        let endpoint = '';
        if (type === 'expense') endpoint = 'expenses';
        if (type === 'asset') endpoint = 'assets';
        if (type === 'liability') endpoint = 'liabilities';
        if (type === 'goal') endpoint = 'goals';

        onSave(endpoint, payload);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="glass-panel w-full max-w-sm p-6 rounded-3xl border border-slate-600 animate-in zoom-in-95 duration-200">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-white font-bold capitalize">Add {type}</h3>
                    <button onClick={onClose}><X className="text-slate-400" /></button>
                </div>

                <div className="space-y-3">
                    {/* EXPENSE FORM */}
                    {type === 'expense' && <>
                        <input className="glass-input w-full p-3 rounded-xl" placeholder="Title" onChange={e => setForm({ ...form, title: e.target.value })} />
                        <input className="glass-input w-full p-3 rounded-xl" type="number" onKeyDown={preventMinus} placeholder="Amount" onChange={e => setForm({ ...form, amount: e.target.value })} />
                    </>}

                    {/* ASSET FORM */}
                    {type === 'asset' && <>
                        <input className="glass-input w-full p-3 rounded-xl" placeholder="Name" onChange={e => setForm({ ...form, name: e.target.value })} />
                        <select className="glass-input w-full p-3 rounded-xl bg-slate-800" value={form.type} onChange={e => setForm({ ...form, type: e.target.value })}>
                            {['Mutual Fund', 'Stock', 'Gold', 'Real Estate', 'Crypto', 'Bank'].map(t => <option key={t} value={t}>{t}</option>)}
                        </select>
                        <input className="glass-input w-full p-3 rounded-xl" type="number" onKeyDown={preventMinus} placeholder="Value" onChange={e => setForm({ ...form, value: e.target.value })} />
                        <select className="glass-input w-full p-3 rounded-xl bg-slate-800" onChange={e => setForm({ ...form, liquidity_score: e.target.value })}>
                            <option value="5">High Liquidity (Cash/Bank)</option>
                            <option value="4">Good Liquidity (MF/Stocks)</option>
                            <option value="1">Locked (Real Estate/PF)</option>
                        </select>
                    </>}

                    {/* LIABILITY FORM */}
                    {type === 'liability' && <>
                        <input className="glass-input w-full p-3 rounded-xl" placeholder="Name" onChange={e => setForm({ ...form, name: e.target.value })} />
                        <select className="glass-input w-full p-3 rounded-xl bg-slate-800" value={form.type} onChange={e => setForm({ ...form, type: e.target.value })}>
                            {['Credit Card', 'Personal Loan', 'Home Loan', 'Car Loan', 'EMI'].map(t => <option key={t} value={t}>{t}</option>)}
                        </select>
                        <input className="glass-input w-full p-3 rounded-xl" type="number" onKeyDown={preventMinus} placeholder="Outstanding Amount" onChange={e => setForm({ ...form, outstanding_amount: e.target.value })} />
                        <input className="glass-input w-full p-3 rounded-xl" type="number" onKeyDown={preventMinus} placeholder="Interest Rate %" onChange={e => setForm({ ...form, interest_rate: e.target.value })} />
                        <input className="glass-input w-full p-3 rounded-xl" type="number" onKeyDown={preventMinus} placeholder="Monthly EMI" onChange={e => setForm({ ...form, monthly_payment: e.target.value })} />
                    </>}

                    {/* GOAL FORM */}
                    {type === 'goal' && <>
                        <input className="glass-input w-full p-3 rounded-xl" placeholder="Goal Name" onChange={e => setForm({ ...form, name: e.target.value })} />
                        <input className="glass-input w-full p-3 rounded-xl" type="number" onKeyDown={preventMinus} placeholder="Target Amount" onChange={e => setForm({ ...form, target_amount: e.target.value })} />
                        <input className="glass-input w-full p-3 rounded-xl text-slate-400" type="date" onChange={e => setForm({ ...form, target_date: e.target.value })} />
                    </>}

                    <button onClick={handleSubmit} className="w-full bg-blue-600 p-3 rounded-xl font-bold text-white mt-4 hover:bg-blue-500">Save</button>
                </div>
            </div>
        </div>
    );
};

export default AddModal;