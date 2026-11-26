import React from 'react';
import {
    PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
    AreaChart, Area, XAxis, YAxis, CartesianGrid
} from 'recharts';
import { Trash2, AlertTriangle, TrendingUp, ShieldCheck, ArrowRight, Gauge } from 'lucide-react';

const Overview = ({ data, onAddExpense, onDelete, onViewChange }) => {
    const expenses = data.lists?.expenses || [];
    const goals = data.lists?.goals || [];
    const health = data.health || {};
    const profile = data.user_profile || {};
    const strategy = health.debt_strategy || {};
    const projections = health.projections || [];

    // All figures come from the engine; the dashboard does no maths of its own.
    const spentThisMonth = health.month_to_date_spent || 0;
    const isOverspending = (health.surplus || 0) < 0;
    const breakdown = health.score_breakdown || [];
    const rupees = (n) => `${(n || 0) < 0 ? '-' : ''}₹${Math.abs(Math.round(n || 0)).toLocaleString('en-IN')}`;

    const riskyGoal = goals.find(g => ["At Risk", "Unrealistic", "Overdue"].includes(g.status));
    const riskyMessage = riskyGoal && (riskyGoal.status === 'Overdue'
        ? `Past its date, ${rupees(riskyGoal.remaining_needed)} still needed.`
        : `You are short by ${rupees(riskyGoal.shortfall_monthly)}/mo.`);

    const chartData = [
        { name: 'Rent', value: profile.rent || 0, color: '#f87171' },
        { name: 'Expenses', value: health.monthly_expenses || 0, color: '#fbbf24' },
        { name: 'EMIs', value: health.total_emi || 0, color: '#fb923c' },
        { name: 'Spare', value: Math.max(0, health.surplus || 0), color: '#34d399' }
    ];

    const formatK = (num) => {
        const sign = num < 0 ? '-' : '';
        const abs = Math.abs(num);
        if (abs >= 100000) return `${sign}₹${(abs / 100000).toFixed(1)}L`;
        if (abs >= 1000) return `${sign}₹${(abs / 1000).toFixed(0)}k`;
        return `${sign}₹${abs}`;
    };

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

            {/* 🚀 NEW: GOAL RISK ALERT */}
            {riskyGoal && (
                <div
                    onClick={() => onViewChange('assets')}
                    className="bg-red-500/10 border border-red-500/30 rounded-2xl p-4 flex items-center justify-between cursor-pointer hover:bg-red-500/20 transition-colors"
                >
                    <div className="flex items-center gap-3">
                        <div className="bg-red-500/20 p-2 rounded-full text-red-400 animate-pulse"><AlertTriangle size={20} /></div>
                        <div>
                            <h3 className="text-white font-bold text-sm">Goal {riskyGoal.status}: {riskyGoal.name}</h3>
                            <p className="text-red-300/70 text-xs">{riskyMessage}</p>
                        </div>
                    </div>
                    <ArrowRight size={16} className="text-red-400" />
                </div>
            )}

            {/* Overspending Warning */}
            {isOverspending && (
                <div className="bg-orange-500/10 border border-orange-500/50 rounded-2xl p-4 flex items-center gap-4">
                    <div className="bg-orange-500/20 p-2 rounded-full text-orange-400"><AlertTriangle size={24} /></div>
                    <div>
                        <h3 className="text-orange-200 font-bold">Overspending Detected</h3>
                        <p className="text-orange-300/80 text-xs">Deficit of <span className="font-bold">{rupees(Math.abs(health.surplus))}</span> a month.</p>
                    </div>
                </div>
            )}

            {/* Main Budget Card */}
            <div className="bg-gradient-to-br from-indigo-900 to-slate-900 rounded-3xl p-6 border border-indigo-500/30 shadow-lg">
                <div className="flex justify-between">
                    <div>
                        <p className="text-indigo-200 text-xs uppercase tracking-widest font-semibold">Monthly Surplus</p>
                        <h2 className="text-3xl font-bold text-white mt-1">{rupees(health.surplus)}</h2>
                    </div>
                    <div className="text-right">
                        <p className="text-emerald-400 text-xs uppercase tracking-widest font-semibold">Should Invest</p>
                        <h2 className="text-xl font-bold text-emerald-400 mt-1">{rupees(health.recommended_investment)}</h2>
                        {health.investment_note && <p className="text-[10px] text-slate-400 mt-1 max-w-[9rem] ml-auto">{health.investment_note}</p>}
                    </div>
                </div>
                <div className="mt-4 flex flex-wrap gap-x-4 gap-y-1 text-xs">
                    <div className="text-slate-400">Monthly Burn: {rupees(health.monthly_burn)}</div>
                    <div className="text-slate-400">Net Worth: <span className={(health.net_worth || 0) >= 0 ? "text-emerald-400" : "text-red-400"}>{rupees(health.net_worth)}</span></div>
                    <div className="text-slate-400">Emergency Fund: {health.emergency_months || 0} mo</div>
                </div>
                {health.plan && Object.keys(health.plan).length > 0 && health.surplus > 0 && (
                    <div className="mt-4 grid grid-cols-4 gap-2 text-center text-[10px] text-slate-400">
                        {[['Emergency', health.plan.emergency_fund], ['Debt', health.plan.debt_prepayment],
                          ['Goals', health.plan.goals], ['Invest', health.plan.investment]].map(([label, v]) => (
                            <div key={label} className="bg-white/5 rounded-lg py-1.5">
                                <div>{label}</div>
                                <div className="text-white font-bold text-xs">{rupees(v)}</div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Strategy & Summary */}
            <div className="grid grid-cols-2 gap-4">
                <div className="glass-panel p-4 rounded-2xl border-l-4 border-blue-500">
                    <div className="flex items-center gap-2 mb-2">
                        <ShieldCheck size={16} className="text-blue-400" />
                        <h3 className="text-white text-sm font-bold">Debt Strategy</h3>
                    </div>
                    {strategy.strategy === "Avalanche" ? (
                        <div>
                            {strategy.recommended_extra_payment > 0
                                ? <div className="text-xs text-slate-400">Pay extra <span className="text-white font-bold">{rupees(strategy.recommended_extra_payment)}/mo</span>{strategy.payoff_order?.[0] && <> on {strategy.payoff_order[0].name}</>}</div>
                                : <div className="text-xs text-slate-400">Keep paying EMIs on time</div>}
                            <div className="mt-2 text-xs font-bold text-emerald-400">Debt-free: {strategy.freedom_date}</div>
                            {strategy.interest_saved > 0 && <div className="mt-1 text-[10px] text-slate-400">Saves {rupees(strategy.interest_saved)} interest</div>}
                        </div>
                    ) : (
                        <div className="text-xs text-slate-500">No active debt.</div>
                    )}
                </div>

                <div className="glass-panel p-4 rounded-2xl border-l-4 border-purple-500">
                    <div className="flex items-center gap-2 mb-2">
                        <TrendingUp size={16} className="text-purple-400" />
                        <h3 className="text-white text-sm font-bold">1-Year Forecast</h3>
                    </div>
                    <div className="text-xs text-slate-400">Net Worth:</div>
                    <div className="text-lg font-bold text-white mt-1">
                        {rupees(projections[projections.length - 1]?.net_worth)}
                    </div>
                    <div className="text-[10px] text-slate-500 mt-1">{rupees(projections[projections.length - 1]?.net_worth_real)} in today's money</div>
                </div>
            </div>

            {/* Wealth Projection Chart */}
            <div className="glass-panel p-5 rounded-3xl">
                <h3 className="text-white font-bold mb-4 text-sm flex items-center gap-2">
                    <TrendingUp size={16} className="text-emerald-400" /> Wealth Projection
                </h3>
                <div className="h-48 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={projections}>
                            <defs>
                                <linearGradient id="colorNw" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                            <XAxis dataKey="month" tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} tickLine={false} />
                            <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} tickFormatter={formatK} axisLine={false} tickLine={false} width={35} />
                            <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderRadius: '12px', border: '1px solid #334155' }} formatter={(value, key) => [rupees(value), key === 'net_worth_real' ? "In today's money" : 'Net Worth']} />
                            <Area type="monotone" dataKey="net_worth" stroke="#8b5cf6" strokeWidth={2} fillOpacity={1} fill="url(#colorNw)" />
                            <Area type="monotone" dataKey="net_worth_real" stroke="#64748b" strokeDasharray="4 4" strokeWidth={1.5} fill="none" />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Score Breakdown */}
            {breakdown.length > 0 && (
                <div className="glass-panel p-5 rounded-3xl">
                    <h3 className="text-white font-bold mb-4 text-sm flex items-center gap-2">
                        <Gauge size={16} className="text-blue-400" /> Why your score is {health.score}
                    </h3>
                    <div className="space-y-3">
                        {breakdown.map(b => (
                            <div key={b.key}>
                                <div className="flex justify-between text-xs">
                                    <span className="text-slate-300">{b.label}</span>
                                    <span className={b.points < 0 ? 'text-red-400 font-bold' : 'text-white font-bold'}>
                                        {b.points}{b.max > 0 && <span className="text-slate-500 font-normal">/{b.max}</span>}
                                    </span>
                                </div>
                                {b.max > 0 && (
                                    <div className="h-1.5 bg-slate-800 rounded-full mt-1 overflow-hidden">
                                        <div className="h-full bg-blue-500 rounded-full" style={{ width: `${(b.points / b.max) * 100}%` }} />
                                    </div>
                                )}
                                <div className="text-[10px] text-slate-500 mt-1">{b.detail}</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Spending Chart */}
            <div className="glass-panel p-5 rounded-3xl h-64 relative">
                <h3 className="text-white font-bold mb-2 text-sm absolute top-5 left-5">Monthly Breakdown</h3>
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie data={chartData} innerRadius={60} outerRadius={80} dataKey="value" stroke="none" paddingAngle={5}>
                            {chartData.map((e, i) => <Cell key={i} fill={e.color} />)}
                        </Pie>
                        <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', border: 'none' }} />
                    </PieChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none pt-6">
                    <div className="text-center">
                        <div className="text-xs text-slate-500">Spent this month</div>
                        <div className="text-xl font-bold text-amber-400">{rupees(spentThisMonth)}</div>
                    </div>
                </div>
            </div>

            {/* Transactions List */}
            <div>
                <div className="flex justify-between items-center mb-3">
                    <h3 className="text-white font-bold">Recent Activity</h3>
                    <button onClick={onAddExpense} className="text-xs bg-blue-600/20 text-blue-400 px-3 py-1 rounded-full hover:bg-blue-600/30">+ Expense</button>
                </div>
                <div className="space-y-2">
                    {expenses.slice(0, 5).map((exp, i) => (
                        <div key={i} className="glass-panel p-3 rounded-xl flex justify-between items-center">
                            <div><div className="text-slate-200 text-sm">{exp.title}</div></div>
                            <div className="flex items-center gap-3">
                                <span className="text-white font-bold">{rupees(exp.amount)}</span>
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