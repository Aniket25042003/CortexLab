/**
 * Dashboard Page
 *
 * Shows all user projects and allows creating / deleting them.
 */

import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
    Plus, FolderOpen, Clock, FileText,
    Beaker, Trash2, ArrowRight, X, Loader2
} from 'lucide-react';
import { projectsApi, type Project } from '../lib/api';
import { useAuthStore } from '../stores/authStore';
import { formatRelativeTime } from '../lib/utils';

/* ── helpers ──────────────────────────────────────────────────────────────── */

/** Lock/unlock body scroll while a modal is visible */
function useBodyScrollLock(locked: boolean) {
    useEffect(() => {
        document.body.style.overflow = locked ? 'hidden' : '';
        return () => { document.body.style.overflow = ''; };
    }, [locked]);
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Page                                                                       */
/* ═══════════════════════════════════════════════════════════════════════════ */

export function DashboardPage() {
    const [isCreating, setIsCreating] = useState(false);
    const [newTitle, setNewTitle] = useState('');
    const [newDesc, setNewDesc] = useState('');

    const queryClient = useQueryClient();
    const { isAuthenticated } = useAuthStore();

    useBodyScrollLock(isCreating);

    /* ── queries / mutations ── */
    const { data, isLoading, isError, refetch } = useQuery({
        queryKey: ['projects'],
        queryFn: () => projectsApi.list().then((r) => r.data),
        enabled: isAuthenticated,
    });

    const createMutation = useMutation({
        mutationFn: (d: { title: string; description?: string }) => projectsApi.create(d),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['projects'] });
            setIsCreating(false);
            setNewTitle('');
            setNewDesc('');
        },
    });

    const deleteMutation = useMutation({
        mutationFn: (id: string) => projectsApi.delete(id),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['projects'] }),
    });

    const handleCreate = () => {
        if (newTitle.trim() && !createMutation.isPending) {
            createMutation.mutate({
                title: newTitle.trim(),
                description: newDesc.trim() || undefined,
            });
        }
    };

    /* ── key handler ── */
    useEffect(() => {
        const handleKey = (e: KeyboardEvent) => {
            // Escape only — Enter is handled by the title input's onKeyDown to avoid
            // double-firing and to prevent swallowing newlines in the description textarea
            if (e.key === 'Escape') setIsCreating(false);
        };
        if (isCreating) window.addEventListener('keydown', handleKey);
        return () => window.removeEventListener('keydown', handleKey);
    }, [isCreating]);

    /* ──────────────────────────────────────────────────────────────────────── */

    return (
        <div className="space-y-8 animate-fade-in-up">

            {/* Page header */}
            <div className="flex items-end justify-between border-b border-slate-200 pb-6">
                <div>
                    <h1 className="text-4xl font-black text-slate-900 tracking-tight">
                        Research Projects
                    </h1>
                    <p className="mt-2 text-base text-slate-500 font-medium">
                        Manage your research explorations and paper drafts
                    </p>
                </div>
                <button
                    onClick={() => setIsCreating(true)}
                    className="btn-primary flex items-center gap-2"
                >
                    <Plus className="w-5 h-5" />
                    New Project
                </button>
            </div>

            {/* Projects grid */}
            {isLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="glass-card h-52 animate-pulse bg-white/40" />
                    ))}
                </div>
            ) : isError ? (
                <div className="text-center py-20">
                    <p className="text-slate-500 mb-4 font-medium">Failed to load projects.</p>
                    <button onClick={() => refetch()} className="btn-secondary">
                        Try Again
                    </button>
                </div>
            ) : data?.projects.length === 0 ? (
                <EmptyState onCreateClick={() => setIsCreating(true)} />
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {data?.projects.map((project) => (
                        <ProjectCard
                            key={project.id}
                            project={project}
                            onDelete={async (id) => { await deleteMutation.mutateAsync(id); }}
                        />
                    ))}
                </div>
            )}

            {/* ── Create-project modal (portaled to <body>) ─────────────────── */}
            {isCreating && createPortal(
                <div
                    className="fixed inset-0 flex items-center justify-center p-4"
                    style={{ zIndex: 9999 }}
                >
                    {/* Backdrop */}
                    <div
                        className="absolute inset-0 bg-slate-900/50 backdrop-blur-[3px]"
                        onClick={() => setIsCreating(false)}
                        aria-hidden="true"
                    />

                    {/* Panel */}
                    <div
                        className="relative w-full max-w-md bg-white rounded-3xl shadow-2xl shadow-slate-900/20 border border-slate-100 overflow-hidden"
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="modal-title"
                    >
                        {/* Header bar */}
                        <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b border-slate-100">
                            <div className="flex items-center gap-3">
                                <div className="w-9 h-9 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center">
                                    <Beaker className="w-5 h-5 text-indigo-600" />
                                </div>
                                <h2 id="modal-title" className="text-xl font-black text-slate-900">
                                    New Research Project
                                </h2>
                            </div>
                            <button
                                onClick={() => setIsCreating(false)}
                                className="p-2 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
                                aria-label="Close"
                            >
                                <X className="w-4 h-4" />
                            </button>
                        </div>

                        {/* Body */}
                        <div className="px-6 py-5 space-y-4">
                            {/* Title */}
                            <div>
                                <label htmlFor="proj-title" className="block text-sm font-bold text-slate-700 mb-1.5">
                                    Project Title <span className="text-red-400">*</span>
                                </label>
                                <input
                                    id="proj-title"
                                    type="text"
                                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-sm"
                                    placeholder="e.g., Computer Vision Classifiers Research"
                                    value={newTitle}
                                    onChange={(e) => setNewTitle(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleCreate()}
                                    autoFocus
                                />
                            </div>

                            {/* Description */}
                            <div>
                                <label htmlFor="proj-desc" className="block text-sm font-bold text-slate-700 mb-1.5">
                                    Description{' '}
                                    <span className="text-slate-400 font-normal">(optional)</span>
                                </label>
                                <textarea
                                    id="proj-desc"
                                    rows={3}
                                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-sm resize-none"
                                    placeholder="Brief description of your research area..."
                                    value={newDesc}
                                    onChange={(e) => setNewDesc(e.target.value)}
                                />
                            </div>
                        </div>

                        {/* Footer */}
                        <div className="flex items-center justify-end gap-3 px-6 py-4 bg-slate-50 border-t border-slate-100">
                            <button
                                onClick={() => setIsCreating(false)}
                                className="px-5 py-2.5 text-sm font-semibold text-slate-600 bg-white border border-slate-200 hover:bg-slate-50 hover:border-slate-300 rounded-xl transition-all"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleCreate}
                                disabled={!newTitle.trim() || createMutation.isPending}
                                className="flex items-center gap-2 px-5 py-2.5 text-sm font-bold text-white bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 rounded-xl transition-all shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40 disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:shadow-none"
                            >
                                {createMutation.isPending ? (
                                    <><Loader2 className="w-4 h-4 animate-spin" /> Creating...</>
                                ) : (
                                    <><Plus className="w-4 h-4" /> Create Project</>
                                )}
                            </button>
                        </div>
                    </div>
                </div>,
                document.body
            )}
        </div>
    );
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Project Card                                                               */
/* ═══════════════════════════════════════════════════════════════════════════ */

function ProjectCard({ project, onDelete }: { project: Project; onDelete: (id: string) => Promise<void> }) {
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);
    const [deleteError, setDeleteError] = useState<string | null>(null);

    useBodyScrollLock(showDeleteConfirm);

    const handleConfirmDelete = async (e: React.MouseEvent) => {
        e.stopPropagation();
        if (isDeleting) return;
        setIsDeleting(true);
        setDeleteError(null);
        try {
            await onDelete(project.id);
            setShowDeleteConfirm(false);
        } catch (err) {
            setDeleteError('Failed to delete project. Please try again.');
        } finally {
            setIsDeleting(false);
        }
    };

    const statusStyles: Record<string, string> = {
        discovery: 'bg-blue-50 text-blue-700 border-blue-200',
        deep_dive: 'bg-violet-50 text-violet-700 border-violet-200',
        paper_drafting: 'bg-amber-50 text-amber-700 border-amber-200',
        completed: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    };
    const statusLabels: Record<string, string> = {
        discovery: 'Discovery',
        deep_dive: 'Deep Dive',
        paper_drafting: 'Paper Draft',
        completed: 'Completed',
    };

    return (
        <>
            <div className="glass-card group hover-lift relative p-6 flex flex-col bg-white border border-slate-100">
                <Link to={`/dashboard/project/${project.id}`} className="flex-1 flex flex-col">

                    {/* Card top */}
                    <div className="flex items-start justify-between mb-4">
                        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-50 to-violet-50 border border-indigo-100 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                            <FolderOpen className="w-6 h-6 text-indigo-600" />
                        </div>
                        <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${statusStyles[project.status] || statusStyles.discovery}`}>
                            {statusLabels[project.status] || project.status}
                        </span>
                    </div>

                    {/* Title */}
                    <h3 className="text-lg font-bold text-slate-900 group-hover:text-indigo-600 transition-colors mb-1">
                        {project.title}
                    </h3>

                    {/* Description */}
                    {project.description && (
                        <p className="text-sm text-slate-500 line-clamp-2 mb-4 flex-1">
                            {project.description}
                        </p>
                    )}

                    {/* Footer meta */}
                    <div className="mt-auto pt-4 border-t border-slate-100 flex items-center justify-between text-xs font-medium text-slate-400">
                        <div className="flex items-center gap-1.5">
                            <Clock className="w-3.5 h-3.5" />
                            {formatRelativeTime(project.updated_at)}
                        </div>
                        {(project.artifact_count || 0) > 0 && (
                            <div className="flex items-center gap-1.5 text-indigo-500 bg-indigo-50 px-2 py-0.5 rounded-md">
                                <FileText className="w-3.5 h-3.5" />
                                {project.artifact_count} artifacts
                            </div>
                        )}
                    </div>
                </Link>

                {/* Delete button (appears on hover or keyboard focus) */}
                <button
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); setShowDeleteConfirm(true); }}
                    className="absolute top-4 right-4 p-2 rounded-xl text-slate-300 hover:text-red-500 hover:bg-red-50 transition-all opacity-0 group-hover:opacity-100 focus-visible:opacity-100 focus-visible:text-red-500 focus-visible:bg-red-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400"
                    aria-label="Delete project"
                >
                    <Trash2 className="w-4 h-4" />
                </button>
            </div>

            {/* Delete-confirm modal (portaled) */}
            {showDeleteConfirm && createPortal(
                <div
                    className="fixed inset-0 flex items-center justify-center p-4"
                    style={{ zIndex: 9999 }}
                    onKeyDown={(e) => e.key === 'Escape' && !isDeleting && setShowDeleteConfirm(false)}
                >
                    <div
                        className="absolute inset-0 bg-slate-900/50 backdrop-blur-[2px]"
                        onClick={(e) => { e.stopPropagation(); if (!isDeleting) setShowDeleteConfirm(false); }}
                        aria-hidden="true"
                    />
                    <div
                        className="relative bg-white rounded-3xl shadow-2xl shadow-slate-900/15 w-full max-w-sm p-6 border border-slate-100"
                        onClick={(e) => e.stopPropagation()}
                        role="alertdialog"
                        aria-modal="true"
                        aria-labelledby={`delete-dialog-title-${project.id}`}
                        aria-describedby={`delete-dialog-desc-${project.id}`}
                    >
                        {/* Icon */}
                        <div className="w-12 h-12 rounded-2xl bg-red-50 border border-red-100 flex items-center justify-center mb-4">
                            <Trash2 className="w-6 h-6 text-red-500" />
                        </div>
                        <h3 id={`delete-dialog-title-${project.id}`} className="text-lg font-black text-slate-900 mb-1">Delete project?</h3>
                        <p id={`delete-dialog-desc-${project.id}`} className="text-sm text-slate-500 mb-6 leading-relaxed">
                            <span className="font-semibold text-slate-700">"{project.title}"</span> and all its artifacts
                            will be permanently deleted. This can't be undone.
                        </p>
                        {deleteError && (
                            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl px-3 py-2 mb-4" role="alert">
                                {deleteError}
                            </p>
                        )}
                        <div className="flex gap-3">
                            <button
                                autoFocus
                                disabled={isDeleting}
                                onClick={(e) => { e.stopPropagation(); setShowDeleteConfirm(false); }}
                                className="flex-1 py-2.5 text-sm font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleConfirmDelete}
                                disabled={isDeleting}
                                className="flex-1 py-2.5 text-sm font-bold text-white bg-red-500 hover:bg-red-600 rounded-xl transition-colors shadow-lg shadow-red-500/20 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            >
                                {isDeleting ? <><Loader2 className="w-4 h-4 animate-spin" />Deleting...</> : 'Delete'}
                            </button>
                        </div>
                    </div>
                </div>,
                document.body
            )}
        </>
    );
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Empty state                                                                */
/* ═══════════════════════════════════════════════════════════════════════════ */

function EmptyState({ onCreateClick }: { onCreateClick: () => void }) {
    return (
        <div className="text-center py-20 px-4">
            <div className="relative inline-block mb-8">
                <div className="absolute inset-0 bg-indigo-200 rounded-full blur-2xl opacity-20 animate-pulse" />
                <div className="w-24 h-24 rounded-3xl bg-white border border-indigo-100 flex items-center justify-center shadow-xl shadow-indigo-500/10 relative">
                    <Beaker className="w-10 h-10 text-indigo-500" />
                </div>
            </div>
            <h3 className="text-2xl font-black text-slate-900 mb-3">No projects yet</h3>
            <p className="text-slate-500 mb-8 max-w-md mx-auto text-base leading-relaxed">
                Start your research journey by creating a new project. Our AI agents will help you
                discover research gaps and plan your experiments.
            </p>
            <button onClick={onCreateClick} className="btn-primary flex items-center gap-2 mx-auto">
                <Plus className="w-5 h-5" />
                Create Your First Project
                <ArrowRight className="w-4 h-4 opacity-60" />
            </button>
        </div>
    );
}
