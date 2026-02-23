/**
 * Login Page
 * Google OAuth sign-in page with authorization code flow.
 */

import { useEffect } from 'react';
import { useGoogleLogin } from '@react-oauth/google';
import { useNavigate } from 'react-router-dom';
import { Beaker, Sparkles, BookOpen, FileText, Brain, ArrowRight } from 'lucide-react';
import { authApi } from '../lib/api';
import { useAuthStore } from '../stores/authStore';

export function LoginPage() {
    const navigate = useNavigate();
    const { setUser, isAuthenticated } = useAuthStore();

    useEffect(() => {
        if (isAuthenticated) navigate('/dashboard');
    }, [isAuthenticated, navigate]);

    const login = useGoogleLogin({
        flow: 'auth-code',
        onSuccess: async (codeResponse) => {
            try {
                const response = await authApi.googleAuth(codeResponse.code);
                setUser(response.data.user);
                localStorage.setItem('session_token', response.data.session_token);
                navigate('/dashboard');
            } catch (error) {
                console.error('Login failed:', error);
            }
        },
        onError: (error) => {
            console.error('Google login error:', error);
        },
    });

    if (isAuthenticated) return null;

    return (
        <div className="min-h-screen flex">
            {/* Left side — gradient branding */}
            <div className="hidden lg:flex lg:w-[52%] bg-gradient-to-br from-indigo-600 via-violet-600 to-purple-700 p-14 flex-col justify-between relative overflow-hidden">
                {/* Background decorations */}
                <div className="absolute top-0 right-0 w-96 h-96 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/2" />
                <div className="absolute bottom-0 left-0 w-80 h-80 bg-black/10 rounded-full translate-y-1/2 -translate-x-1/2" />
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-white/3 rounded-full" />

                {/* Logo */}
                <div className="relative z-10 flex items-center gap-3">
                    <div className="w-11 h-11 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center border border-white/30">
                        <Beaker className="w-6 h-6 text-white" />
                    </div>
                    <span className="text-2xl font-bold text-white tracking-tight">CortexLab</span>
                </div>

                {/* Headline */}
                <div className="relative z-10 space-y-8">
                    <div>
                        <h1 className="text-5xl font-black text-white leading-[1.1] tracking-tight mb-4">
                            Discover Gaps.<br />
                            Design Experiments.<br />
                            Draft Papers.
                        </h1>
                        <p className="text-lg text-white/75 leading-relaxed max-w-sm">
                            AI-powered research assistant that guides you from idea to publication — fast.
                        </p>
                    </div>

                    {/* Feature pills */}
                    <div className="grid grid-cols-2 gap-3">
                        {[
                            { icon: <Sparkles className="w-4 h-4" />, title: 'Gap Discovery', desc: 'Find untapped opportunities' },
                            { icon: <BookOpen className="w-4 h-4" />, title: 'Deep Analysis', desc: 'Literature synthesis' },
                            { icon: <Brain className="w-4 h-4" />, title: 'Experiment Design', desc: 'Actionable research plans' },
                            { icon: <FileText className="w-4 h-4" />, title: 'Paper Drafting', desc: 'Publication-ready drafts' },
                        ].map((f) => (
                            <div key={f.title} className="bg-white/10 border border-white/20 rounded-2xl p-4 backdrop-blur-sm">
                                <div className="text-white/90 mb-2">{f.icon}</div>
                                <h3 className="text-sm font-bold text-white">{f.title}</h3>
                                <p className="text-xs text-white/60 mt-0.5">{f.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>

                <p className="relative z-10 text-xs text-white/40">© 2026 CortexLab. Powered by AI.</p>
            </div>

            {/* Right side — sign-in form */}
            <div className="w-full lg:w-[48%] flex items-center justify-center p-8 bg-slate-50">
                {/* Subtle background blobs */}
                <div className="fixed inset-0 overflow-hidden pointer-events-none lg:hidden">
                    <div className="absolute top-[-10%] left-[-10%] w-[60vw] h-[60vw] bg-violet-200/40 rounded-full blur-[120px] mix-blend-multiply animate-blob" />
                    <div className="absolute bottom-[-10%] right-[-10%] w-[50vw] h-[50vw] bg-indigo-200/40 rounded-full blur-[100px] mix-blend-multiply animate-blob animation-delay-2000" />
                </div>

                <div className="relative w-full max-w-sm">
                    {/* Mobile logo */}
                    <div className="text-center lg:hidden mb-10">
                        <div className="inline-flex items-center gap-3">
                            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
                                <Beaker className="w-6 h-6 text-white" />
                            </div>
                            <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-violet-600">
                                CortexLab
                            </span>
                        </div>
                    </div>

                    {/* Header */}
                    <div className="mb-8">
                        <h2 className="text-3xl font-black text-slate-900 mb-2">Welcome back</h2>
                        <p className="text-slate-500 font-medium">Sign in to continue your research journey</p>
                    </div>

                    {/* Google button */}
                    <div className="space-y-5">
                        <button
                            onClick={() => login()}
                            className="w-full flex items-center gap-3 px-6 py-4 bg-white border border-slate-200 text-slate-700 rounded-2xl font-semibold text-sm hover:bg-slate-50 hover:border-indigo-200 hover:shadow-lg hover:shadow-indigo-500/10 transition-all shadow-sm active:scale-[0.99] group"
                        >
                            <GoogleIcon />
                            <span className="flex-1 text-center">Continue with Google</span>
                            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-500 group-hover:translate-x-0.5 transition-all" />
                        </button>

                        {/* Divider */}
                        <div className="flex items-center gap-4">
                            <div className="flex-1 h-px bg-slate-200" />
                            <span className="text-xs text-slate-400 font-medium">Secured with OAuth 2.0</span>
                            <div className="flex-1 h-px bg-slate-200" />
                        </div>

                        <p className="text-center text-xs text-slate-400 leading-relaxed">
                            By signing in, you agree to our{' '}
                            <span className="text-indigo-500 hover:text-indigo-600 cursor-pointer font-medium">Terms of Service</span>
                            {' '}and{' '}
                            <span className="text-indigo-500 hover:text-indigo-600 cursor-pointer font-medium">Privacy Policy</span>.
                        </p>
                    </div>

                    {/* Trust card */}
                    <div className="mt-8 bg-white rounded-2xl border border-slate-100 shadow-sm p-4 flex items-center gap-3">
                        <div className="w-9 h-9 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center flex-shrink-0">
                            <Brain className="w-5 h-5 text-indigo-600" />
                        </div>
                        <div>
                            <p className="text-xs font-bold text-slate-800">AI-Powered Research Platform</p>
                            <p className="text-xs text-slate-400 mt-0.5">Gemini AI · LangGraph · Google Scholar</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function GoogleIcon() {
    return (
        <svg width="20" height="20" viewBox="0 0 24 24" className="flex-shrink-0">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
        </svg>
    );
}
