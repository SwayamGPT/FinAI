import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { Trash2, AlertTriangle, TrendingUp, ShieldCheck } from 'lucide-react';

const Overview = ({ data, onAddExpense, onDelete }) => {
    const expenses = data.lists?.expenses || [];
    const health = data.health || {};
    const profile = data.user_profile || {};
    const strategy = health.debt_strategy || {};

    const totalSpent = expenses.reduce((acc, curr) => acc + (curr.amount || 0), 0);
    const isOverspending = (health.surplus || 0) < 0;

    const chartData = [
        { name: 'Rent', value: profile.rent || 0, color: '#f87171' },
        { name: 'Spent', value: totalSpent, color: '#fbbf24' },
        { name: 'Investable', value: Math.max(0, health.surplus || 0), color: '#34d399' }
    ];

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

            {/* Overspending Warning */}
            {isOverspending && (
                <div className="bg-red-500/10 border border-red-500/50 rounded-2xl p-4 flex items-center gap-4">
                    <div className="bg-red-500/20 p-2 rounded-full text-red-400"><AlertTriangle size={24} /></div>
                    <div>
                        <h3 className="text-red-200 font-bold">You are overspending!</h3>
                        <p className="text-red-300/80 text-xs">Deficit of <span className="font-bold text-red-200">₹{Math.abs(health.surplus).toLocaleString()}</span> this month.</p>
                    </div>
                </div>
            )}

            {/* Main Budget Card */}
            <div className="bg-gradient-to-br from-indigo-900 to-slate-900 rounded-3xl p-6 border border-indigo-500/30 shadow-lg">
                <div className="flex justify-between">
                    <div>
                        <p className="text-indigo-200 text-xs uppercase tracking-widest font-semibold">Available to Spend</p>
                        <h2 className="text-3xl font-bold text-white mt-1">₹{(health.surplus || 0).toLocaleString()}</h2>
                    </div>
                    <div className="text-right">
                        <p className="text-emerald-400 text-xs uppercase tracking-widest font-semibold">Should Invest</p>
                        <h2 className="text-xl font-bold text-emerald-400 mt-1">₹{(health.recommended_investment || 0).toLocaleString()}</h2>
                    </div>
                </div>
                <div className="mt-4 flex gap-4 text-xs">
                    <div className="text-slate-400">Monthly Burn: ₹{(health.monthly_burn || 0).toLocaleString()}</div>
                    <div className="text-slate-400">Net Worth: <span className={(health.net_worth || 0) >= 0 ? "text-emerald-400" : "text-red-400"}>₹{(health.net_worth || 0).toLocaleString()}</span></div>
                </div>
            </div>

            {/* STRATEGY & PROJECTION ROW (New) */}
            <div className="grid grid-cols-2 gap-4">
                {/* Debt Strategy */}
                <div className="glass-panel p-4 rounded-2xl border-l-4 border-blue-500">
                    <div className="flex items-center gap-2 mb-2">
                        <ShieldCheck size={16} className="text-blue-400" />
                        <h3 className="text-white text-sm font-bold">Debt Strategy</h3>
                    </div>
                    {strategy.strategy === "Avalanche" ? (
                        <div>
                            <div className="text-xs text-slate-400">Pay extra ₹{Math.round(strategy.recommended_extra_payment)}/mo to highest interest loan.</div>
                            <div className="mt-2 text-xs font-bold text-emerald-400">Debt Free by: {strategy.freedom_date}</div>
                        </div>
                    ) : (
                        <div className="text-xs text-slate-500">No active high-interest debt found. Good job!</div>
                    )}
                </div>

                {/* Projection */}
                <div className="glass-panel p-4 rounded-2xl border-l-4 border-purple-500">
                    <div className="flex items-center gap-2 mb-2">
                        <TrendingUp size={16} className="text-purple-400" />
                        <h3 className="text-white text-sm font-bold">1-Year Forecast</h3>
                    </div>
                    <div className="text-xs text-slate-400">Projected Net Worth:</div>
                    {health.projections && health.projections.length > 0 ? (
                        <div className="text-lg font-bold text-white mt-1">
                            ₹{Math.round(health.projections[11].net_worth).toLocaleString()}
                        </div>
                    ) : (
                        <div className="text-xs text-slate-500">Insufficient data</div>
                    )}
                </div>
            </div>

            {/* Chart */}
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

            {/* Transactions List */}
            <div>
                <div className="flex justify-between items-center mb-3">
                    <h3 className="text-white font-bold">Recent Activity</h3>
                    <button onClick={onAddExpense} className="text-xs bg-blue-600/20 text-blue-400 px-3 py-1 rounded-full">+ Expense</button>
                </div>
                <div className="space-y-2">
                    {expenses.slice(0, 5).map((exp, i) => (
                        <div key={i} className="glass-panel p-3 rounded-xl flex justify-between items-center">
                            <div><div className="text-slate-200 text-sm">{exp.title}</div></div>
                            <div className="flex items-center gap-3">
                                <span className="text-white font-bold">₹{exp.amount}</span>
                                <button onClick={() => onDelete('expenses', exp.id)} className="text-slate-600 hover:text-red-500"><Trash2 size={14} /></button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default Overview;