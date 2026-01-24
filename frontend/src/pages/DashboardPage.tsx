/**
 * Dashboard Page
 * 
 * Shows all user projects and allows creating new ones.
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Plus, FolderOpen, Clock, FileText, Beaker, Trash2 } from 'lucide-react';
import { projectsApi, type Project } from '../lib/api';
import { useAuthStore } from '../stores/authStore';
import { formatRelativeTime } from '../lib/utils';

export function DashboardPage() {
    const [isCreating, setIsCreating] = useState(false);
    const [newProjectTitle, setNewProjectTitle] = useState('');
    const [newProjectDescription, setNewProjectDescription] = useState('');
    const queryClient = useQueryClient();
    const { isAuthenticated } = useAuthStore();

    const { data, isLoading } = useQuery({
        queryKey: ['projects'],
        queryFn: () => projectsApi.list().then((res) => res.data),
        enabled: isAuthenticated,
    });

    const createMutation = useMutation({
        mutationFn: (data: { title: string; description?: string }) =>
            projectsApi.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['projects'] });
            setIsCreating(false);
            setNewProjectTitle('');
            setNewProjectDescription('');
        },
    });

    const deleteMutation = useMutation({
        mutationFn: (id: string) => projectsApi.delete(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['projects'] });
        },
    });

    const handleDelete = (id: string) => {
        deleteMutation.mutate(id);
    };

    const handleCreate = () => {
        if (newProjectTitle.trim()) {
            createMutation.mutate({
                title: newProjectTitle.trim(),
                description: newProjectDescription.trim() || undefined,
            });
        }
    };

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-[var(--color-text-primary)]">
                        Research Projects
                    </h1>
                    <p className="mt-1 text-[var(--color-text-secondary)]">
                        Manage your research explorations and paper drafts
                    </p>
                </div>
                <button
                    onClick={() => setIsCreating(true)}
                    className="btn btn-primary"
                >
                    <Plus className="w-5 h-5" />
                    New Project
                </button>
            </div>

            {/* Create Project Modal */}
            {isCreating && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="card w-full max-w-lg animate-fade-in">
                        <h2 className="text-xl font-bold mb-4">Create New Project</h2>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm text-[var(--color-text-secondary)] mb-2">
                                    Project Title
                                </label>
                                <input
                                    type="text"
                                    className="input"
                                    placeholder="e.g., Computer Vision Classifiers Research"
                                    value={newProjectTitle}
                                    onChange={(e) => setNewProjectTitle(e.target.value)}
                                    autoFocus
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-[var(--color-text-secondary)] mb-2">
                                    Description (optional)
                                </label>
                                <textarea
                                    className="input min-h-[100px]"
                                    placeholder="Brief description of your research area..."
                                    value={newProjectDescription}
                                    onChange={(e) => setNewProjectDescription(e.target.value)}
                                />
                            </div>
                            <div className="flex gap-3 justify-end pt-4">
                                <button
                                    onClick={() => setIsCreating(false)}
                                    className="btn btn-secondary"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleCreate}
                                    disabled={!newProjectTitle.trim() || createMutation.isPending}
                                    className="btn btn-primary disabled:opacity-50"
                                >
                                    {createMutation.isPending ? 'Creating...' : 'Create Project'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Projects Grid */}
            {isLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="card">
                            <div className="skeleton h-6 w-3/4 rounded mb-3" />
                            <div className="skeleton h-4 w-full rounded mb-2" />
                            <div className="skeleton h-4 w-2/3 rounded" />
                        </div>
                    ))}
                </div>
            ) : data?.projects.length === 0 ? (
                <EmptyState onCreateClick={() => setIsCreating(true)} />
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {data?.projects.map((project) => (
                        <ProjectCard key={project.id} project={project} onDelete={handleDelete} />
                    ))}
                </div>
            )}
        </div>
    );
}

function ProjectCard({ project, onDelete }: { project: Project; onDelete: (id: string) => void }) {
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

    const statusColors: Record<string, string> = {
        discovery: 'bg-blue-500/20 text-blue-400',
        deep_dive: 'bg-purple-500/20 text-purple-400',
        paper_drafting: 'bg-amber-500/20 text-amber-400',
        completed: 'bg-green-500/20 text-green-400',
    };

    const statusLabels: Record<string, string> = {
        discovery: 'Discovery',
        deep_dive: 'Deep Dive',
        paper_drafting: 'Paper Draft',
        completed: 'Completed',
    };

    const handleDelete = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setShowDeleteConfirm(true);
    };

    const confirmDelete = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        onDelete(project.id);
        setShowDeleteConfirm(false);
    };

    const cancelDelete = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setShowDeleteConfirm(false);
    };

    return (
        <div className="card group hover:border-[var(--color-primary)] relative">
            <Link to={`/project/${project.id}`} className="block">
                <div className="flex items-start justify-between mb-3">
                    <div className="w-10 h-10 rounded-lg gradient-bg flex items-center justify-center">
                        <FolderOpen className="w-5 h-5 text-white" />
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[project.status] || statusColors.discovery}`}>
                        {statusLabels[project.status] || project.status}
                    </span>
                </div>

                <h3 className="text-lg font-semibold text-[var(--color-text-primary)] group-hover:text-[var(--color-primary)] transition-colors">
                    {project.title}
                </h3>

                {project.description && (
                    <p className="mt-2 text-sm text-[var(--color-text-secondary)] line-clamp-2">
                        {project.description}
                    </p>
                )}

                <div className="mt-4 flex items-center gap-4 text-sm text-[var(--color-text-muted)]">
                    <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {formatRelativeTime(project.updated_at)}
                    </div>
                    {(project.artifact_count || 0) > 0 && (
                        <div className="flex items-center gap-1">
                            <FileText className="w-4 h-4" />
                            {project.artifact_count} artifacts
                        </div>
                    )}
                </div>
            </Link>

            {/* Delete button */}
            <button
                onClick={handleDelete}
                className="absolute top-3 right-3 p-2 rounded-lg bg-red-500/10 text-red-400 opacity-0 group-hover:opacity-100 hover:bg-red-500/20 transition-all"
                title="Delete project"
            >
                <Trash2 className="w-4 h-4" />
            </button>

            {/* Delete confirmation modal */}
            {showDeleteConfirm && (
                <div
                    className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
                    onClick={cancelDelete}
                >
                    <div
                        className="card w-full max-w-sm animate-fade-in"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <h3 className="text-lg font-semibold mb-2">Delete Project?</h3>
                        <p className="text-sm text-[var(--color-text-secondary)] mb-4">
                            Are you sure you want to delete "{project.title}"? This action cannot be undone.
                        </p>
                        <div className="flex gap-3 justify-end">
                            <button onClick={cancelDelete} className="btn btn-secondary">
                                Cancel
                            </button>
                            <button
                                onClick={confirmDelete}
                                className="btn bg-red-500 hover:bg-red-600 text-white"
                            >
                                Delete
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function EmptyState({ onCreateClick }: { onCreateClick: () => void }) {
    return (
        <div className="text-center py-16">
            <div className="w-20 h-20 mx-auto mb-6 rounded-2xl gradient-bg flex items-center justify-center opacity-50">
                <Beaker className="w-10 h-10 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">
                No projects yet
            </h3>
            <p className="text-[var(--color-text-secondary)] mb-6 max-w-md mx-auto">
                Start your research journey by creating a new project. Our AI agents will help you
                discover research gaps and plan your experiments.
            </p>
            <button onClick={onCreateClick} className="btn btn-primary">
                <Plus className="w-5 h-5" />
                Create Your First Project
            </button>
        </div>
    );
}
