import { useEffect, useState } from 'react';
import { useGoogleLogin } from '@react-oauth/google';
import { useNavigate } from 'react-router-dom';
import {
    Beaker,
    Sparkles,
    ArrowRight,
    Brain,
    Zap,
    Search,
    FileText,
    Menu,
    X,
} from 'lucide-react';
import { authApi } from '../lib/api';
import { useAuthStore } from '../stores/authStore';

export function LandingPage() {
    const navigate = useNavigate();
    const { setUser, isAuthenticated } = useAuthStore();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    useEffect(() => {
        if (isAuthenticated) {
            navigate('/dashboard');
        }
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

    return (
        <div className="min-h-screen bg-slate-50 text-slate-900 font-sans selection:bg-indigo-100 selection:text-indigo-900 overflow-x-hidden">

            {/* Vibrant Background Blobs */}
            <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
                <div className="absolute top-[-10%] left-[-10%] w-[60vw] h-[60vw] bg-violet-200/40 rounded-full blur-[120px] mix-blend-multiply animate-blob"></div>
                <div className="absolute top-[10%] right-[-10%] w-[50vw] h-[50vw] bg-indigo-200/40 rounded-full blur-[120px] mix-blend-multiply animate-blob animation-delay-2000"></div>
                <div className="absolute bottom-[-20%] left-[30%] w-[60vw] h-[60vw] bg-fuchsia-200/40 rounded-full blur-[120px] mix-blend-multiply animate-blob animation-delay-4000"></div>
                {/* Subtle Mesh pattern */}
                <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-[0.03]"></div>
            </div>

            {/* Navbar */}
            <nav className="glass-nav">
                <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/20 text-white">
                            <Beaker className="w-6 h-6" />
                        </div>
                        <span className="text-xl font-bold tracking-tight text-slate-900">CortexLab</span>
                    </div>

                    <div className="hidden md:flex items-center gap-8">
                        <a href="#features" className="text-sm font-semibold text-slate-600 hover:text-indigo-600 transition-colors">Features</a>
                        <button
                            onClick={() => login()}
                            className="text-sm font-semibold text-slate-600 hover:text-indigo-600 transition-colors"
                        >
                            Sign In
                        </button>
                        <button
                            onClick={() => login()}
                            className="px-6 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-full font-bold transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5"
                        >
                            Get Started
                        </button>
                    </div>

                    <button
                        className="md:hidden p-2 text-slate-600 hover:text-indigo-600"
                        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                    >
                        {mobileMenuOpen ? <X /> : <Menu />}
                    </button>
                </div>

                {mobileMenuOpen && (
                    <div className="md:hidden absolute top-20 left-0 w-full bg-white/95 backdrop-blur-xl border-b border-indigo-100 p-6 flex flex-col gap-4 shadow-xl">
                        <a href="#features" className="text-lg font-medium text-slate-700">Features</a>
                        <div className="h-px bg-slate-100 my-2"></div>
                        <button onClick={() => login()} className="w-full py-3 bg-slate-100 text-slate-900 rounded-xl font-bold">Sign In</button>
                        <button onClick={() => login()} className="w-full py-3 bg-indigo-600 text-white rounded-xl font-bold">Get Started</button>
                    </div>
                )}
            </nav>

            {/* Hero Section */}
            <section className="relative z-10 pt-44 pb-32 px-6">
                <div className="max-w-7xl mx-auto text-center">

                    <div className="inline-flex items-center gap-2 px-6 py-2.5 rounded-full bg-white border border-indigo-100 shadow-sm mb-8 animate-fade-in-up hover:shadow-md transition-shadow cursor-default">
                        <Sparkles className="w-4 h-4 text-indigo-500 animate-pulse" />
                        <span className="text-sm font-semibold text-slate-700">The Next Gen AI Research Assistant</span>
                    </div>

                    <h1 className="text-6xl md:text-8xl font-black mb-8 leading-tight tracking-tight text-slate-900 animate-fade-in-up md:delay-100">
                        Research at the <br />
                        <span className="text-gradient">
                            Speed of Thought
                        </span>
                    </h1>

                    <p className="text-xl md:text-2xl text-slate-500 max-w-2xl mx-auto mb-12 leading-relaxed animate-fade-in-up md:delay-200 font-medium">
                        Discover research gaps, design experiments, and draft papers with an intelligent partner that never sleeps.
                    </p>

                    <div className="flex flex-col sm:flex-row items-center justify-center gap-5 animate-fade-in-up md:delay-300 relative z-30">
                        <button onClick={() => login()} className="btn-primary w-full sm:w-auto flex items-center justify-center gap-2 group cursor-pointer">
                            Start Researching
                            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                        </button>
                    </div>

                    {/* Floating Features - Desktop Only */}
                    <div className="hidden lg:block absolute top-[40%] left-[5%] animate-float hover:z-20">
                        <FeaturePill icon={<Brain className="text-violet-500" />} text="Deep Analysis" rotate="-6deg" />
                    </div>
                    <div className="hidden lg:block absolute top-[30%] right-[5%] animate-float animation-delay-2000 hover:z-20">
                        <FeaturePill icon={<Search className="text-indigo-500" />} text="Gap Discovery" rotate="6deg" />
                    </div>
                    <div className="hidden lg:block absolute bottom-[10%] left-[15%] animate-float animation-delay-4000 hover:z-20">
                        <FeaturePill icon={<Zap className="text-fuchsia-500" />} text="Experiment Design" rotate="3deg" />
                    </div>
                </div>
            </section>

            {/* Features Grid */}
            <section id="features" className="relative z-10 py-32 px-6">
                <div className="max-w-7xl mx-auto">
                    <div className="text-center mb-20">
                        <h2 className="text-4xl md:text-5xl font-bold mb-6 text-slate-900">Built for Modern Science</h2>
                        <p className="text-slate-500 max-w-2xl mx-auto text-lg font-medium">
                            A complete suite of AI tools designed to accelerate every stage of your academic workflow.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                        <FeatureCard
                            icon={<Search className="w-8 h-8 text-indigo-600" />}
                            title="Gap Discovery"
                            description="Instantly analyze millions of papers to find unexplored opportunities and contradictions."
                            delay={0}
                        />
                        <FeatureCard
                            icon={<Brain className="w-8 h-8 text-violet-600" />}
                            title="Deep Reading"
                            description="Synthesize findings across disciplines with AI that understands context and nuance."
                            delay={100}
                        />
                        <FeatureCard
                            icon={<FileText className="w-8 h-8 text-fuchsia-600" />}
                            title="Auto Drafting"
                            description="Generate structure, arguments, and citations for your manuscript automatically."
                            delay={200}
                        />
                        <FeatureCard
                            icon={<Zap className="w-8 h-8 text-indigo-600" />}
                            title="Experiment Design"
                            description="Create detailed experimental protocols tailored to your hypotheses."
                            delay={300}
                        />
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-12 border-t border-indigo-100 bg-white/50">
                <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
                            <Beaker className="w-4 h-4 text-white" />
                        </div>
                        <span className="text-lg font-bold text-slate-800">CortexLab</span>
                    </div>
                    <p className="text-sm text-slate-400 font-medium">
                        © 2026 CortexLab. All rights reserved.
                    </p>
                </div>
            </footer>
        </div>
    );
}

function FeaturePill({ icon, text, rotate }: { icon: React.ReactNode, text: string, rotate: string }) {
    return (
        <div
            className="px-6 py-4 bg-white rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.1)] border border-white/50 flex items-center gap-3 transform transition-transform hover:scale-110 cursor-default"
            style={{ transform: `rotate(${rotate})` }}
        >
            <div className="p-2 bg-slate-50 rounded-xl">{icon}</div>
            <span className="font-bold text-slate-700">{text}</span>
        </div>
    )
}

function FeatureCard({ icon, title, description, delay }: { icon: React.ReactNode, title: string, description: string, delay: number }) {
    return (
        <div
            className="glass-card p-8 hover-lift flex flex-col items-start gap-4 group"
            style={{ animationDelay: `${delay}ms` }}
        >
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-50 to-violet-50 flex items-center justify-center group-hover:scale-110 transition-transform">
                {icon}
            </div>
            <h3 className="text-2xl font-bold text-slate-900">{title}</h3>
            <p className="text-slate-500 leading-relaxed font-medium">
                {description}
            </p>
        </div>
    );
}
