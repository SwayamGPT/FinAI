import React from 'react';
import { Trash2 } from 'lucide-react';

const DeleteModal = ({ onConfirm, onCancel }) => (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
        <div className="glass-panel w-full max-w-xs p-6 rounded-3xl border border-red-500/30 text-center animate-in zoom-in-95">
            <div className="bg-red-500/20 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
                <Trash2 className="text-red-400" size={24} />
            </div>
            <h3 className="text-white font-bold text-lg">Delete this item?</h3>
            <p className="text-slate-400 text-sm mt-2 mb-6">This action cannot be undone.</p>
            <div className="flex gap-3">
                <button onClick={onCancel} className="flex-1 py-3 bg-slate-700 hover:bg-slate-600 rounded-xl font-bold text-white text-sm">Cancel</button>
                <button onClick={onConfirm} className="flex-1 py-3 bg-red-600 hover:bg-red-500 rounded-xl font-bold text-white text-sm">Delete</button>
            </div>
        </div>
    </div>
);

export default DeleteModal;