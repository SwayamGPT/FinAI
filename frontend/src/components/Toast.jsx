import React from 'react';
import { CheckCircle, AlertCircle } from 'lucide-react';

const Toast = ({ msg, type }) => (
    <div className={`fixed top-6 left-1/2 -translate-x-1/2 z-[60] px-4 py-3 rounded-xl shadow-2xl flex items-center gap-3 backdrop-blur-md border animate-in slide-in-from-top-4 duration-300 ${type === 'error' ? 'bg-red-900/80 border-red-500/50 text-red-200' : 'bg-emerald-900/80 border-emerald-500/50 text-emerald-200'}`}>
        {type === 'error' ? <AlertCircle size={18} /> : <CheckCircle size={18} />}
        <span className="text-sm font-medium">{msg}</span>
    </div>
);

export default Toast;