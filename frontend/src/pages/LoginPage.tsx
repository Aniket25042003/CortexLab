/**
 * Login Page
 * 
 * Google OAuth sign-in page with authorization code flow.
 */

import { useGoogleLogin } from '@react-oauth/google';
import { useNavigate } from 'react-router-dom';
import { Beaker, Sparkles, BookOpen, FileText } from 'lucide-react';
import { authApi } from '../lib/api';
import { useAuthStore } from '../stores/authStore';

export function LoginPage() {
    const navigate = useNavigate();
    const { setUser, isAuthenticated } = useAuthStore();

    // Redirect if already authenticated
    if (isAuthenticated) {
        navigate('/');
        return null;
    }

    const login = useGoogleLogin({
        flow: 'auth-code',
        onSuccess: async (codeResponse) => {
            try {
                // Send the authorization code to the backend
                // Backend will exchange it for tokens using client_secret
                const response = await authApi.googleAuth(codeResponse.code);
                setUser(response.data.user);
                localStorage.setItem('session_token', response.data.session_token);
                navigate('/');
            } catch (error) {
                console.error('Login failed:', error);
            }
        },
        onError: (error) => {
            console.error('Google login error:', error);
        },
    });

    return (
        <div className="min-h-screen flex">
            {/* Left side - Branding */}
            <div className="hidden lg:flex lg:w-1/2 gradient-bg p-12 flex-col justify-between">
                <div>
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-white/20 flex items-center justify-center">
                            <Beaker className="w-7 h-7 text-white" />
                        </div>
                        <span className="text-2xl font-bold text-white">CortexLab</span>
                    </div>
                </div>

                <div className="space-y-8">
                    <h1 className="text-4xl font-bold text-white leading-tight">
                        Discover Research Gaps.<br />
                        Design Experiments.<br />
                        Draft Papers.
                    </h1>
                    <p className="text-xl text-white/80">
                        AI-powered research assistant that guides you from idea to publication.
                    </p>

                    <div className="grid grid-cols-2 gap-4 pt-8">
                        <FeatureCard
                            icon={<Sparkles className="w-5 h-5" />}
                            title="Gap Discovery"
                            description="Find untapped research opportunities"
                        />
                        <FeatureCard
                            icon={<BookOpen className="w-5 h-5" />}
                            title="Deep Analysis"
                            description="Comprehensive literature review"
                        />
                        <FeatureCard
                            icon={<Beaker className="w-5 h-5" />}
                            title="Experiment Design"
                            description="Actionable research plans"
                        />
                        <FeatureCard
                            icon={<FileText className="w-5 h-5" />}
                            title="Paper Drafting"
                            description="Generate publication-ready drafts"
                        />
                    </div>
                </div>

                <div className="text-white/60 text-sm">
                    © 2026 CortexLab. Powered by AI.
                </div>
            </div>

            {/* Right side - Login */}
            <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-[var(--color-bg-primary)]">
                <div className="w-full max-w-md space-y-8">
                    <div className="text-center lg:hidden mb-8">
                        <div className="flex items-center justify-center gap-3 mb-4">
                            <div className="w-12 h-12 rounded-xl gradient-bg flex items-center justify-center">
                                <Beaker className="w-7 h-7 text-white" />
                            </div>
                            <span className="text-2xl font-bold gradient-text">CortexLab</span>
                        </div>
                    </div>

                    <div className="text-center space-y-2">
                        <h2 className="text-3xl font-bold text-[var(--color-text-primary)]">
                            Welcome back
                        </h2>
                        <p className="text-[var(--color-text-secondary)]">
                            Sign in to continue your research journey
                        </p>
                    </div>

                    <div className="space-y-4">
                        <button
                            onClick={() => login()}
                            className="w-full flex items-center justify-center gap-3 px-6 py-4 bg-white text-gray-800 rounded-xl font-medium hover:bg-gray-100 transition-all shadow-lg hover:shadow-xl"
                        >
                            <GoogleIcon />
                            Continue with Google
                        </button>

                        <p className="text-center text-sm text-[var(--color-text-muted)]">
                            By signing in, you agree to our Terms of Service and Privacy Policy.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}

function FeatureCard({
    icon,
    title,
    description
}: {
    icon: React.ReactNode;
    title: string;
    description: string;
}) {
    return (
        <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
            <div className="text-white mb-2">{icon}</div>
            <h3 className="font-semibold text-white">{title}</h3>
            <p className="text-sm text-white/70">{description}</p>
        </div>
    );
}

function GoogleIcon() {
    return (
        <svg width="20" height="20" viewBox="0 0 24 24">
            <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                fill="#4285F4"
            />
            <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                fill="#34A853"
            />
            <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                fill="#FBBC05"
            />
            <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                fill="#EA4335"
            />
        </svg>
    );
}
