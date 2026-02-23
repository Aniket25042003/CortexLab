/**
 * Project Workspace Page
 * 
 * Main workspace for a research project with chat, agent timeline, and artifacts.
 */

import { useState, useRef, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import {
    Sparkles,
    FileText,
    Upload,
    Loader2,
    Download,
    ShieldAlert,
    RefreshCw,
    Maximize2
} from 'lucide-react';
import {
    projectsApi,
    runsApi,
    artifactsApi,
    experimentsApi,
    type Artifact,
    type AgentRun,
} from '../lib/api';
import { cn, formatRelativeTime, downloadBlob } from '../lib/utils';
import { OptionsSelector } from '../components/OptionsSelector';
import { useAuthStore } from '../stores/authStore';

export function ProjectWorkspace() {
    const { projectId } = useParams<{ projectId: string }>();
    const [selectedArtifact, setSelectedArtifact] = useState<Artifact | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const queryClient = useQueryClient();
    const { isAuthenticated } = useAuthStore();

    // Fetch project details
    const { data: project } = useQuery({
        queryKey: ['project', projectId],
        queryFn: () => projectsApi.get(projectId!).then((res) => res.data),
        enabled: !!projectId && isAuthenticated,
    });


    // Fetch artifacts
    const { data: artifactsData } = useQuery({
        queryKey: ['artifacts', projectId],
        queryFn: () => artifactsApi.list(projectId!).then((res) => res.data),
        enabled: !!projectId && isAuthenticated,
    });

    // Fetch experiments
    const { data: experimentsData } = useQuery({
        queryKey: ['experiments', projectId],
        queryFn: () => experimentsApi.list(projectId!).then((res) => res.data),
        enabled: !!projectId && isAuthenticated,
    });

    // Fetch runs with conditional polling
    const { data: runsData } = useQuery({
        queryKey: ['runs', projectId],
        queryFn: () => runsApi.list(projectId!).then((res) => res.data),
        enabled: !!projectId && isAuthenticated,
        staleTime: 10000,
        refetchInterval: (query) => {
            const hasActiveRun = query.state.data?.runs?.some(
                (r: AgentRun) => r.status === 'running' || r.status === 'pending'
            );
            return hasActiveRun ? 3000 : false;
        },
    });

    // Sort runs by creation time (descending)
    const sortedRuns = runsData?.runs.sort((a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    ) || [];

    // Active run = any run currently running or pending
    const currentRun = sortedRuns.find(
        (r) => r.status === 'running' || r.status === 'pending'
    );
    const hasActiveRun = !!currentRun;

    // When no active run, use the most recent run to determine phase / error
    const latestRun = currentRun ?? sortedRuns[0];
    const latestFailedRun = !hasActiveRun
        ? sortedRuns.find((r) => r.status === 'failed')
        : undefined;

    // Determine current phase (only meaningful when no run is active)
    const isDiscoveryPhase = !hasActiveRun && latestRun?.run_type === 'discovery' && latestRun?.status === 'completed';
    const isDeepDivePhase = !hasActiveRun && latestRun?.run_type === 'deep_dive';
    const isChatEnabled = isDeepDivePhase && latestRun?.status === 'completed';

    // Refresh artifacts when a run completes
    useEffect(() => {
        if (!hasActiveRun) {
            queryClient.invalidateQueries({ queryKey: ['artifacts', projectId] });
        }
    }, [hasActiveRun, queryClient, projectId]);


    // Deep dive mutation
    const deepDiveMutation = useMutation({
        mutationFn: (direction: any) =>
            runsApi.startDeepDive(projectId!, direction.id, direction.description),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['runs', projectId] });
        },
    });

    // Upload mutation
    const uploadMutation = useMutation({
        mutationFn: (file: File) => experimentsApi.upload(projectId!, file),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['experiments', projectId] });
        },
    });

    // Draft paper mutation
    const draftPaperMutation = useMutation({
        mutationFn: () => {
            // Include all uploaded experiments
            const experimentIds = experimentsData?.experiments.map(e => e.id) || [];
            return runsApi.startPaper(projectId!, experimentIds);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['runs', projectId] });
        },
    });

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            uploadMutation.mutate(file);
        }
    };


    const handleSelectDirection = (direction: any) => {
        deepDiveMutation.mutate(direction);
    };

    const handleExportDocx = async (artifactId: string, title: string) => {
        try {
            const response = await artifactsApi.exportDocx(artifactId);
            downloadBlob(response.data, `${title}.docx`);
        } catch (error) {
            console.error('Export failed:', error);
        }
    };

    return (
        <div className="flex h-[calc(100vh-140px)] gap-6">
            {/* Left Sidebar - Artifacts & Sources */}
            <div className="w-80 glass-card bg-white/60 flex flex-col overflow-hidden hidden md:flex border border-white/50">
                <div className="p-4 border-b border-indigo-50 bg-white/30 backdrop-blur-sm">
                    <h2 className="font-bold text-slate-800 text-lg line-clamp-1">{project?.title || 'Loading...'}</h2>
                    <p className="text-xs text-slate-500 mt-1 uppercase tracking-wider font-semibold">Project Artifacts</p>
                </div>

                <div className="flex-1 overflow-y-auto p-3 space-y-2">
                    {artifactsData?.artifacts.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-40 text-slate-400 text-sm text-center px-4">
                            <FileText className="w-8 h-8 mb-2 opacity-50" />
                            <p>No research artifacts generated yet.</p>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {artifactsData?.artifacts.map((artifact) => (
                                <button
                                    key={artifact.id}
                                    onClick={() => setSelectedArtifact(artifact)}
                                    className={cn(
                                        "w-full text-left p-3 rounded-xl transition-all group border",
                                        selectedArtifact?.id === artifact.id
                                            ? "bg-white border-indigo-200 shadow-md shadow-indigo-500/10"
                                            : "hover:bg-white/60 border-transparent hover:border-white/60"
                                    )}
                                >
                                    <div className="flex items-center gap-3">
                                        <div className={cn(
                                            "w-8 h-8 rounded-lg flex items-center justify-center",
                                            selectedArtifact?.id === artifact.id
                                                ? "bg-indigo-100 text-indigo-600"
                                                : "bg-slate-100 text-slate-500 group-hover:bg-indigo-50 group-hover:text-indigo-500"
                                        )}>
                                            <FileText className="w-4 h-4" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <h4 className={cn(
                                                "text-sm font-semibold truncate",
                                                selectedArtifact?.id === artifact.id ? "text-indigo-900" : "text-slate-700"
                                            )}>
                                                {artifact.title}
                                            </h4>
                                            <p className="text-xs text-slate-400 mt-0.5 truncate">
                                                {formatRelativeTime(artifact.updated_at)}
                                            </p>
                                        </div>
                                    </div>
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* Bottom Actions - Upload & Draft */}
                {isDeepDivePhase && (
                    <div className="p-4 border-t border-indigo-50 bg-white/40">
                        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wide mb-3 flex justify-between items-center">
                            <span>Experiment Data</span>
                            {uploadMutation.isPending && <Loader2 className="w-3 h-3 animate-spin text-indigo-500" />}
                        </h3>

                        <div className="space-y-2">
                            {experimentsData?.experiments.map((exp: any) => (
                                <div key={exp.id} className="text-xs px-3 py-2 rounded-lg bg-white/60 border border-indigo-50 text-slate-600 flex items-center gap-2">
                                    <Upload className="w-3 h-3 text-indigo-400" />
                                    <span className="truncate">{exp.original_name}</span>
                                </div>
                            ))}

                            <input
                                type="file"
                                ref={fileInputRef}
                                className="hidden"
                                onChange={handleFileChange}
                            />

                            <div className="grid grid-cols-2 gap-2 mt-3">
                                <button
                                    onClick={() => fileInputRef.current?.click()}
                                    className="btn-secondary px-3 py-2 text-xs flex items-center justify-center gap-2"
                                    disabled={uploadMutation.isPending || draftPaperMutation.isPending}
                                >
                                    <Upload className="w-3.5 h-3.5" />
                                    Upload
                                </button>
                                {experimentsData?.experiments && experimentsData.experiments.length > 0 && (
                                    <button
                                        onClick={() => draftPaperMutation.mutate()}
                                        className="btn-primary px-3 py-2 text-xs flex items-center justify-center gap-2"
                                        disabled={draftPaperMutation.isPending || hasActiveRun}
                                    >
                                        <Sparkles className="w-3.5 h-3.5" />
                                        Draft
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Main Area */}
            <div className="flex-1 flex flex-col glass-card bg-white/80 overflow-hidden border border-white/60 shadow-xl">
                {/* Main Content Area */}
                <div className="flex-1 overflow-hidden relative">
                    {/* Phase 1: Options Selection */}
                    {isDiscoveryPhase && !hasActiveRun && (
                        <div className="h-full overflow-y-auto p-6">
                            <OptionsSelector
                                run={latestRun}
                                onSelect={handleSelectDirection}
                                isLoading={deepDiveMutation.isPending}
                            />
                        </div>
                    )}

                    {/* Phase 2: Active Run Loading State */}
                    {hasActiveRun && (
                        <div className="h-full flex flex-col items-center justify-center p-12 text-center">
                            <div className="relative mb-8">
                                <div className="absolute inset-0 bg-indigo-200 rounded-full blur-xl opacity-50 animate-pulse"></div>
                                <div className="relative w-24 h-24 bg-white rounded-full shadow-lg flex items-center justify-center">
                                    <Loader2 className="w-10 h-10 text-indigo-600 animate-spin" />
                                </div>
                                <div className="absolute top-0 right-0 w-8 h-8 bg-violet-400 rounded-full animate-bounce delay-100"></div>
                                <div className="absolute bottom-1 left-0 w-6 h-6 bg-fuchsia-400 rounded-full animate-bounce delay-300"></div>
                            </div>

                            <h3 className="text-2xl font-bold text-slate-900 mb-3">
                                {currentRun?.run_type === 'discovery' ? 'Analyzing Research Landscape' :
                                    currentRun?.run_type === 'deep_dive' ? 'Conducting Deep Dive' :
                                        'Agent Working...'}
                            </h3>
                            <p className="text-slate-500 font-medium max-w-md animate-pulse">
                                {currentRun?.run_type === 'discovery'
                                    ? 'Scanning sources to identify key trends and gaps...'
                                    : 'Analyzing baselines, datasets, and experiment protocols...'}
                            </p>
                        </div>
                    )}

                    {/* Error State — only shown when NO run is currently active */}
                    {latestFailedRun && !hasActiveRun && !isDiscoveryPhase && !isChatEnabled && (
                        <div className="h-full flex flex-col items-center justify-center p-12 text-center">
                            <div className="w-20 h-20 bg-red-50 rounded-full flex items-center justify-center mb-6 shadow-sm border border-red-100">
                                <ShieldAlert className="w-10 h-10 text-red-500" />
                            </div>
                            <h3 className="text-xl font-bold text-slate-900 mb-2">Analysis Failed</h3>
                            <p className="max-w-md mb-6 text-sm text-slate-500 font-medium leading-relaxed">
                                {latestFailedRun.error_message || 'An unexpected error occurred.'}
                            </p>
                            <button
                                onClick={() => {
                                    if (latestFailedRun.run_type === 'discovery') {
                                        runsApi.startDiscovery(projectId!, project?.title || 'Research Request');
                                        queryClient.invalidateQueries({ queryKey: ['runs', projectId] });
                                    } else if (latestFailedRun.run_type === 'deep_dive') {
                                        queryClient.invalidateQueries({ queryKey: ['runs', projectId] });
                                    } else if (latestFailedRun.run_type === 'paper') {
                                        draftPaperMutation.mutate();
                                    }
                                }}
                                className="btn-secondary flex items-center gap-2"
                            >
                                <RefreshCw className="w-4 h-4" />
                                Retry
                            </button>
                        </div>
                    )}

                    {/* Phase 3: Research Complete View (Empty Main State, prompting to select artifact) */}
                    {isChatEnabled && !hasActiveRun && !selectedArtifact && (
                        <div className="h-full flex flex-col items-center justify-center p-12 text-center">
                            <div className="w-24 h-24 bg-gradient-to-br from-emerald-100 to-teal-100 rounded-3xl rotate-3 flex items-center justify-center mb-8 shadow-lg shadow-emerald-500/10">
                                <Sparkles className="w-12 h-12 text-emerald-600" />
                            </div>
                            <h3 className="text-2xl font-bold text-slate-900 mb-3">Research Deep Dive Complete!</h3>
                            <p className="text-slate-500 text-lg max-w-md mb-8">
                                The agent has completed the detailed analysis. Select an artifact from the sidebar to view the results.
                            </p>
                            <div className="flex gap-4">
                                <button
                                    onClick={() => fileInputRef.current?.click()}
                                    className="btn-secondary"
                                >
                                    <Upload className="w-4 h-4 mr-2" />
                                    Upload Results
                                </button>
                                {artifactsData?.artifacts?.[0] && (
                                    <button
                                        onClick={() => setSelectedArtifact(artifactsData.artifacts[0])}
                                        className="btn-primary shadow-emerald-500/20 bg-gradient-to-r from-emerald-500 to-teal-500 border-none"
                                    >
                                        View Latest Artifact
                                    </button>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Artifact Viewer (Overlay or Main Content) */}
                    {selectedArtifact && !hasActiveRun && (
                        <div className="absolute inset-0 flex flex-col bg-white/50 backdrop-blur-sm">
                            <div className="p-4 border-b border-indigo-500/10 flex items-center justify-between bg-white/80 backdrop-blur-md sticky top-0 z-10">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-indigo-50 rounded-lg">
                                        <FileText className="w-5 h-5 text-indigo-600" />
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-slate-900 line-clamp-1">{selectedArtifact.title}</h3>
                                        <p className="text-xs text-slate-500 font-medium">
                                            v{selectedArtifact.version} • {formatRelativeTime(selectedArtifact.updated_at)}
                                        </p>
                                    </div>
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => setSelectedArtifact(null)}
                                        className="md:hidden btn-secondary p-2"
                                    >
                                        <Maximize2 className="w-4 h-4" />
                                    </button>
                                    <button
                                        onClick={() => handleExportDocx(selectedArtifact.id, selectedArtifact.title)}
                                        className="btn-secondary text-xs flex items-center gap-2"
                                    >
                                        <Download className="w-3.5 h-3.5" />
                                        Export
                                    </button>
                                </div>
                            </div>

                            <div className="flex-1 overflow-y-auto p-8 lg:px-16 bg-white/40">
                                <div className="markdown-content prose prose-slate max-w-4xl mx-auto bg-white p-8 md:p-12 rounded-2xl shadow-sm border border-slate-100">
                                    <ReactMarkdown>{selectedArtifact.content_markdown}</ReactMarkdown>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
