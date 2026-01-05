import React from 'react';
import { Plus } from 'lucide-react';

const Assets = ({ data, onAdd, onDelete }) => {
    const assets = data.lists?.assets || [];
    const liabilities = data.lists?.liabilities || [];
    const goals = data.lists?.goals || [];

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-right duration-300">

            {/* Assets */}
            <div>
                <div className="flex justify-between items-center mb-3">
                    <h2 className="text-xl font-bold text-white">Assets</h2>
                    <button onClick={() => onAdd('asset')} className="bg-emerald-600 p-2 rounded-lg text-white"><Plus size={18} /></button>
                </div>
                {assets.map((a, i) => (
                    <div key={i} className="glass-panel p-4 rounded-xl border-l-4 border-emerald-500 flex justify-between mb-2">
                        <div><div className="font-bold">{a.name}</div><div className="text-xs text-slate-400">{a.type}</div></div>
                        <div className="text-right"><div className="font-bold">₹{a.value}</div><button onClick={() => onDelete('assets', a.id)} className="text-xs text-red-400">Remove</button></div>
                    </div>
                ))}
            </div>

            {/* Liabilities */}
            <div>
                <div className="flex justify-between items-center mb-3">
                    <h2 className="text-xl font-bold text-white">Liabilities</h2>
                    <button onClick={() => onAdd('liability')} className="bg-red-600 p-2 rounded-lg text-white"><Plus size={18} /></button>
                </div>
                {liabilities.map((l, i) => (
                    <div key={i} className="glass-panel p-4 rounded-xl border-l-4 border-red-500 flex justify-between mb-2">
                        <div><div className="font-bold">{l.name}</div><div className="text-xs text-slate-400">EMI: ₹{l.monthly_payment}</div></div>
                        <div className="text-right"><div className="font-bold text-red-400">₹{l.outstanding_amount}</div><button onClick={() => onDelete('liabilities', l.id)} className="text-xs text-red-400">Remove</button></div>
                    </div>
                ))}
            </div>

            {/* Goals */}
            <div>
                <div className="flex justify-between items-center mb-3">
                    <h2 className="text-xl font-bold text-white">Goals</h2>
                    <button onClick={() => onAdd('goal')} className="bg-purple-600 p-2 rounded-lg text-white"><Plus size={18} /></button>
                </div>
                {goals.map((g, i) => (
                    <div key={i} className="glass-panel p-4 rounded-xl border-l-4 border-purple-500 mb-2">
                        <div className="flex justify-between mb-1">
                            <span className="font-bold">{g.name}</span>
                            <span className={`text-xs px-2 py-0.5 rounded ${g.status === 'On Track' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>{g.status}</span>
                        </div>
                        <div className="flex justify-between text-xs text-slate-400 mt-2">
                            <span>Target: ₹{g.target_amount}</span>
                            <span>Save: <span className="text-white font-bold">₹{Math.round(g.required_monthly)}/mo</span></span>
                        </div>
                        <button onClick={() => onDelete('goals', g.id)} className="text-xs text-red-400 mt-2">Delete</button>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Assets;