import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Sparkles, ArrowRight } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const Onboarding = () => {
    const navigate = useNavigate();
    const [step, setStep] = useState(1);
    const [data, setData] = useState({
        age: '', salary: '', rent: '', current_savings: '', saving_goal: ''
    });

    // BLOCK negative signs and 'e' (exponential)
    const preventMinus = (e) => {
        if (["-", "+", "e", "E"].includes(e.key)) {
            e.preventDefault();
        }
    };

    const submit = async () => {
        try {
            const token = localStorage.getItem('token');
            await axios.post(`${API_URL}/onboard`, {
                age: Number(data.age),
                salary: Number(data.salary),
                rent: Number(data.rent),
                current_savings: Number(data.current_savings),
                saving_goal: data.saving_goal
            }, { headers: { Authorization: `Bearer ${token}` } });
            navigate('/dashboard');
        } catch (e) { alert("Failed to save details"); }
    };

    return (
        <div className="flex items-center justify-center min-h-screen p-4">
            <div className="glass-panel p-8 rounded-3xl w-full max-w-md border border-slate-700/50">
                <div className="text-center mb-6">
                    <Sparkles className="mx-auto text-yellow-400 mb-2" size={40} />
                    <h1 className="text-2xl font-bold text-white">Let's get to know you</h1>
                    <p className="text-slate-400 text-sm">Step {step} of 2</p>
                </div>

                {step === 1 ? (
                    <div className="space-y-4 animate-in slide-in-from-right duration-300">
                        <div>
                            <label className="text-xs text-slate-400 ml-1">Your Age</label>
                            <input
                                type="number" min="0" onKeyDown={preventMinus}
                                className="w-full p-3 rounded-xl glass-input mt-1" placeholder="e.g. 24"
                                value={data.age} onChange={e => setData({ ...data, age: e.target.value })}
                            />
                        </div>
                        <div>
                            <label className="text-xs text-slate-400 ml-1">Monthly Salary (₹)</label>
                            <input
                                type="number" min="0" onKeyDown={preventMinus}
                                className="w-full p-3 rounded-xl glass-input mt-1" placeholder="e.g. 30000"
                                value={data.salary} onChange={e => setData({ ...data, salary: e.target.value })}
                            />
                        </div>
                        <div>
                            <label className="text-xs text-slate-400 ml-1">Monthly Rent / EMI (₹)</label>
                            <input
                                type="number" min="0" onKeyDown={preventMinus}
                                className="w-full p-3 rounded-xl glass-input mt-1" placeholder="e.g. 10000"
                                value={data.rent} onChange={e => setData({ ...data, rent: e.target.value })}
                            />
                        </div>
                        <button onClick={() => setStep(2)} className="w-full bg-blue-600 hover:bg-blue-500 text-white p-3.5 rounded-xl font-bold mt-4 flex items-center justify-center gap-2">
                            Next <ArrowRight size={18} />
                        </button>
                    </div>
                ) : (
                    <div className="space-y-4 animate-in slide-in-from-right duration-300">
                        <div>
                            <label className="text-xs text-slate-400 ml-1">Current Cash Savings (₹)</label>
                            <input
                                type="number" min="0" onKeyDown={preventMinus}
                                className="w-full p-3 rounded-xl glass-input mt-1" placeholder="e.g. 50000"
                                value={data.current_savings} onChange={e => setData({ ...data, current_savings: e.target.value })}
                            />
                        </div>
                        <div>
                            <label className="text-xs text-slate-400 ml-1">Main Financial Goal</label>
                            <input type="text" className="w-full p-3 rounded-xl glass-input mt-1" placeholder="e.g. Buy a KTM Bike"
                                value={data.saving_goal} onChange={e => setData({ ...data, saving_goal: e.target.value })} />
                        </div>
                        <div className="flex gap-3 mt-4">
                            <button onClick={() => setStep(1)} className="w-1/3 bg-slate-700 hover:bg-slate-600 text-white p-3.5 rounded-xl font-bold">Back</button>
                            <button onClick={submit} className="w-2/3 bg-emerald-600 hover:bg-emerald-500 text-white p-3.5 rounded-xl font-bold">
                                Finish Setup
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
export default Onboarding;