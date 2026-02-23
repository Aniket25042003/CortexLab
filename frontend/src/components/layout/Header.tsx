/**
 * Header Component
 * 
 * App header with logo, navigation, and user menu.
 */

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Beaker, LogOut, ChevronDown } from 'lucide-react';
import { authApi } from '../../lib/api';
import { useAuthStore } from '../../stores/authStore';
import { getInitials } from '../../lib/utils';

export function Header() {
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const { user, logout } = useAuthStore();
    const navigate = useNavigate();

    const handleLogout = async () => {
        try {
            await authApi.logout();
        } catch (e) {
            // Ignore errors
        }
        logout();
        localStorage.removeItem('session_token');
        navigate('/login');
    };

    return (
        <header className="glass-nav">
            <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
                {/* Logo */}
                <Link to="/dashboard" className="flex items-center gap-3 group">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/20 text-white group-hover:scale-105 transition-transform">
                        <Beaker className="w-5 h-5" />
                    </div>
                    <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-800 to-slate-600">CortexLab</span>
                </Link>

                {/* User Menu */}
                <div className="relative">
                    <button
                        onClick={() => setIsMenuOpen(!isMenuOpen)}
                        className="flex items-center gap-3 p-1.5 pr-3 rounded-full hover:bg-white/50 border border-transparent hover:border-white/60 transition-all hover:shadow-sm"
                    >
                        {user?.avatar_url ? (
                            <img
                                src={user.avatar_url}
                                alt={user.name}
                                className="w-8 h-8 rounded-full border border-white shadow-sm"
                            />
                        ) : (
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white text-sm font-bold shadow-sm">
                                {user ? getInitials(user.name) : '?'}
                            </div>
                        )}
                        <span className="text-sm font-semibold text-slate-700">
                            {user?.name || 'User'}
                        </span>
                        <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${isMenuOpen ? 'rotate-180' : ''}`} />
                    </button>

                    {isMenuOpen && (
                        <>
                            <div
                                className="fixed inset-0 z-10 cursor-default"
                                onClick={() => setIsMenuOpen(false)}
                            />
                            <div className="absolute right-0 top-full mt-2 w-56 bg-white border border-slate-200 rounded-2xl shadow-xl shadow-slate-900/10 z-50 flex flex-col gap-1 overflow-hidden">
                                <div className="px-3 py-2 border-b border-indigo-50 mb-1">
                                    <p className="text-sm font-bold text-slate-800">{user?.name}</p>
                                    <p className="text-xs text-slate-500 truncate">{user?.email}</p>
                                </div>
                                <button
                                    onClick={handleLogout}
                                    className="w-full flex items-center gap-2 px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                >
                                    <LogOut className="w-4 h-4" />
                                    Sign out
                                </button>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </header>
    );
}
