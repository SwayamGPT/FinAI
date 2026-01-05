import React, { useState } from 'react';
import api from '../services/api'; // <--- NEW IMPORT
import { GoogleLogin } from '@react-oauth/google';
import { Wallet } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const Auth = () => {
    const navigate = useNavigate();
    const [mode, setMode] = useState('login');
    const [input, setInput] = useState({ username: '', password: '' });

    const handleSuccess = (data) => {
        localStorage.setItem('token', data.access_token);
        if (data.has_onboarded) navigate('/dashboard');
        else navigate('/onboarding');
    };

    const handleAuth = async () => {
        try {
            const endpoint = mode === 'login' ? '/login' : '/register';
            // 🚀 FIX: Uses /v1/auth prefix automatically
            const res = await api.post(`/auth${endpoint}`, input);
            if (mode === 'register') { alert("Registered! Now Login."); setMode('login'); }
            else { handleSuccess(res.data); }
        } catch (e) { alert("Auth Failed"); }
    };

    const googleSuccess = async (res) => {
        try {
            const backendRes = await api.post('/auth/google-login', { token: res.credential });
            handleSuccess(backendRes.data);
        } catch (e) { alert("Google Login Failed"); }
    };

    return (
        <div className="flex items-center justify-center min-h-screen p-4">
            <div className="glass-panel p-8 rounded-3xl w-full max-w-sm border border-slate-700/50">
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg mb-4">
                        <Wallet className="text-white w-8 h-8" />
                    </div>
                    <h1 className="text-3xl font-bold text-white">FinAI</h1>
                </div>
                <div className="space-y-4">
                    <input className="w-full p-3.5 rounded-xl glass-input text-sm" placeholder="Email" onChange={e => setInput({ ...input, username: e.target.value })} />
                    <input className="w-full p-3.5 rounded-xl glass-input text-sm" type="password" placeholder="Password" onChange={e => setInput({ ...input, password: e.target.value })} />
                    <button onClick={handleAuth} className="w-full bg-blue-600 hover:bg-blue-500 text-white p-3.5 rounded-xl font-bold transition-all">{mode === 'login' ? 'Sign In' : 'Sign Up'}</button>
                    <div className="flex justify-center mt-4"><GoogleLogin theme="filled_black" shape="pill" onSuccess={googleSuccess} /></div>
                    <p className="text-center text-xs text-slate-400 mt-4 cursor-pointer" onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
                        {mode === 'login' ? "New here? Create account" : "Login instead"}
                    </p>
                </div>
            </div>
        </div>
    );
};
export default Auth;