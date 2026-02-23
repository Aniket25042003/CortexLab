/**
 * Main Layout
 * 
 * App shell with header and content area.
 */

import { Outlet } from 'react-router-dom';
import { Header } from './Header';

export function MainLayout() {
    return (
        <div className="min-h-screen bg-slate-50 relative selection:bg-indigo-100 selection:text-indigo-900">
            {/* Vibrant Background Blobs (Fixed) */}
            <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
                <div className="absolute top-[-10%] left-[-10%] w-[60vw] h-[60vw] bg-violet-200/40 rounded-full blur-[120px] mix-blend-multiply animate-blob"></div>
                <div className="absolute top-[10%] right-[-10%] w-[50vw] h-[50vw] bg-indigo-200/40 rounded-full blur-[120px] mix-blend-multiply animate-blob animation-delay-2000"></div>
                <div className="absolute bottom-[-20%] left-[30%] w-[60vw] h-[60vw] bg-fuchsia-200/40 rounded-full blur-[120px] mix-blend-multiply animate-blob animation-delay-4000"></div>
                <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-[0.03]"></div>
            </div>

            <div className="relative z-10 flex flex-col min-h-screen">
                <Header />
                <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-8 relative z-0">
                    <Outlet />
                </main>
            </div>
        </div>
    );
}
