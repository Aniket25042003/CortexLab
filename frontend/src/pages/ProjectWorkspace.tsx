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

    const latestRun = sortedRuns[0];
    const currentRun = sortedRuns.find(
        (r) => r.status === 'running' || r.status === 'pending'
    );

    // Determine current phase
    const isDiscoveryPhase = latestRun?.run_type === 'discovery' && latestRun?.status === 'completed';
    const isDeepDivePhase = latestRun?.run_type === 'deep_dive';
    const isChatEnabled = isDeepDivePhase && latestRun?.status === 'completed';
    const hasActiveRun = !!currentRun;

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
        <div className="flex h-[calc(100vh-64px)]">
            {/* Left Sidebar - Artifacts & Sources */}
            <div className="w-72 border-r border-[var(--color-border)] p-4 overflow-y-auto hidden md:block">
                <div className="space-y-6">
                    {/* Artifacts Section */}
                    <div>
                        <h3 className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wide mb-3">
                            Artifacts
                        </h3>
                        {artifactsData?.artifacts.length === 0 ? (
                            <p className="text-sm text-[var(--color-text-muted)]">
                                No artifacts yet.
                            </p>
                        ) : (
                            <div className="space-y-2">
                                {artifactsData?.artifacts.map((artifact) => (
                                    <button
                                        key={artifact.id}
                                        onClick={() => setSelectedArtifact(artifact)}
                                        className={cn(
                                            "w-full text-left p-3 rounded-lg transition-all",
                                            selectedArtifact?.id === artifact.id
                                                ? "bg-[var(--color-primary)]/20 border border-[var(--color-primary)]"
                                                : "hover:bg-[var(--color-bg-tertiary)] border border-transparent"
                                        )}
                                    >
                                        <div className="flex items-center gap-2">
                                            <FileText className="w-4 h-4 text-[var(--color-primary)]" />
                                            <span className="text-sm font-medium truncate">
                                                {artifact.title}
                                            </span>
                                        </div>
                                        <p className="text-xs text-[var(--color-text-muted)] mt-1">
                                            {artifact.artifact_type} • v{artifact.version}
                                        </p>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Upload & Experiment Section (Visible only in Chat/Deep Dive Phase) */}
                    {isDeepDivePhase && (
                        <div>
                            <h3 className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wide mb-3 flex justify-between items-center">
                                <span>Experiments</span>
                                {uploadMutation.isPending && <Loader2 className="w-3 h-3 animate-spin" />}
                            </h3>

                            {/* Experiment List */}
                            <div className="space-y-2 mb-3">
                                {experimentsData?.experiments.map((exp: any) => (
                                    <div key={exp.id} className="text-xs p-2 rounded bg-[var(--color-bg-tertiary)] flex items-center justify-between group">
                                        <span className="truncate flex-1" title={exp.original_name}>{exp.original_name}</span>
                                    </div>
                                ))}
                            </div>

                            <div className="space-y-2">
                                <input
                                    type="file"
                                    ref={fileInputRef}
                                    className="hidden"
                                    onChange={handleFileChange}
                                />
                                <button
                                    onClick={() => fileInputRef.current?.click()}
                                    className="w-full btn btn-secondary text-sm"
                                    disabled={uploadMutation.isPending || draftPaperMutation.isPending}
                                >
                                    <Upload className="w-4 h-4" />
                                    {uploadMutation.isPending ? 'Uploading...' : 'Upload Results'}
                                </button>

                                {experimentsData?.experiments && experimentsData.experiments.length > 0 && (
                                    <button
                                        onClick={() => draftPaperMutation.mutate()}
                                        className="w-full btn btn-primary text-sm"
                                        disabled={draftPaperMutation.isPending || hasActiveRun}
                                    >
                                        <Sparkles className="w-4 h-4" />
                                        {draftPaperMutation.isPending ? 'Drafting...' : 'Draft Paper'}
                                    </button>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Main Area */}
            <div className="flex-1 flex flex-col">
                {/* Project Header */}
                <div className="border-b border-[var(--color-border)] p-4">
                    <h2 className="text-xl font-semibold">{project?.title || 'Loading...'}</h2>
                    {project?.description && (
                        <p className="text-sm text-[var(--color-text-secondary)] mt-1 line-clamp-1">
                            {project.description}
                        </p>
                    )}
                </div>

                {/* Main Content Area */}
                <div className="flex-1 overflow-hidden relative">
                    {/* Phase 1: Options Selection */}
                    {isDiscoveryPhase && !hasActiveRun && (
                        <div className="h-full overflow-y-auto">
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
                            <div className="w-16 h-16 bg-[var(--color-primary)]/10 rounded-full flex items-center justify-center mb-4 animate-pulse">
                                <Loader2 className="w-8 h-8 text-[var(--color-primary)] animate-spin" />
                            </div>
                            <h3 className="text-xl font-semibold mb-2">
                                {currentRun?.run_type === 'discovery' ? 'Analyzing Research Landscape...' :
                                    currentRun?.run_type === 'deep_dive' ? 'Conducting Deep Dive...' :
                                        'Agent Working...'}
                            </h3>
                            <p className="text-[var(--color-text-secondary)] max-w-md">
                                {currentRun?.run_type === 'discovery'
                                    ? 'Scanning sources to identify trends and gaps.'
                                    : 'Analyzing baselines, datasets, and experiment protocols.'}
                            </p>
                        </div>
                    )}

                    {/* Error State */}
                    {latestRun?.status === 'failed' && (
                        <div className="h-full flex flex-col items-center justify-center p-12 text-center text-red-500">
                            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
                                <ShieldAlert className="w-8 h-8 text-red-600" />
                            </div>
                            <h3 className="text-xl font-semibold mb-2">Analysis Failed</h3>
                            <p className="max-w-md mb-4">{latestRun.error_message || "An unexpected error occurred."}</p>
                            <button
                                onClick={() => {
                                    if (latestRun.run_type === 'discovery') {
                                        runsApi.startDiscovery(projectId!, project?.title || "Research Request");
                                    } else if (latestRun.run_type === 'deep_dive') {
                                        // Need direction ID for deep dive retry, might need to reset state instead
                                        queryClient.invalidateQueries({ queryKey: ['runs', projectId] });
                                    } else if (latestRun.run_type === 'paper') {
                                        draftPaperMutation.mutate();
                                    }
                                }}
                                className="btn btn-secondary"
                            >
                                <RefreshCw className="w-4 h-4 mr-2" />
                                Retry
                            </button>
                        </div>
                    )}

                    {/* Phase 3: Research Complete View */}
                    {isChatEnabled && !hasActiveRun && (
                        <div className="h-full flex flex-col items-center justify-center p-12 text-center">
                            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                                <Sparkles className="w-8 h-8 text-green-600" />
                            </div>
                            <h3 className="text-xl font-semibold mb-2">Research Deep Dive Complete</h3>
                            <p className="text-[var(--color-text-secondary)] max-w-md mb-6">
                                The agent has completed the detailed analysis. You can find the experimental plan and other findings in the artifacts sidebar.
                            </p>
                            <div className="flex gap-4">
                                <button
                                    onClick={() => fileInputRef.current?.click()}
                                    className="btn btn-primary"
                                >
                                    <Upload className="w-4 h-4 mr-2" />
                                    Upload Results
                                </button>
                                {artifactsData?.artifacts?.[0] && (
                                    <button
                                        onClick={() => setSelectedArtifact(artifactsData.artifacts[0])}
                                        className="btn btn-secondary"
                                    >
                                        View Latest Artifact
                                    </button>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Right Panel - Artifact Viewer */}
            {selectedArtifact && (
                <div className="w-[500px] border-l border-[var(--color-border)] flex flex-col">
                    <div className="p-4 border-b border-[var(--color-border)] flex items-center justify-between">
                        <div>
                            <h3 className="font-semibold">{selectedArtifact.title}</h3>
                            <p className="text-xs text-[var(--color-text-muted)]">
                                Version {selectedArtifact.version} • {formatRelativeTime(selectedArtifact.updated_at)}
                            </p>
                        </div>
                        <button
                            onClick={() => handleExportDocx(selectedArtifact.id, selectedArtifact.title)}
                            className="btn btn-secondary text-sm"
                        >
                            <Download className="w-4 h-4" />
                            Export
                        </button>
                    </div>
                    <div className="flex-1 overflow-y-auto p-4">
                        <div className="markdown-content prose prose-invert max-w-none">
                            <ReactMarkdown>{selectedArtifact.content_markdown}</ReactMarkdown>
                        </div>
                    </div>

                    {/* Action Footer for Experiment Plans */}
                    {selectedArtifact.artifact_type === 'experiment_plan' && (
                        <div className="p-4 border-t border-[var(--color-border)] bg-[var(--color-bg-tertiary)]/50">
                            <div className="flex items-start gap-3">
                                <Sparkles className="w-5 h-5 text-[var(--color-primary)] mt-0.5" />
                                <div>
                                    <h4 className="text-sm font-medium mb-1">Ready to Draft Paper?</h4>
                                    <p className="text-xs text-[var(--color-text-secondary)] mb-3">
                                        Upload your experiment results (logs, metrics, or notes) to generate the paper draft.
                                    </p>
                                    <button
                                        onClick={() => fileInputRef.current?.click()}
                                        className="w-full btn btn-primary text-sm"
                                        disabled={uploadMutation.isPending}
                                    >
                                        <Upload className="w-4 h-4 mr-2" />
                                        {uploadMutation.isPending ? 'Uploading...' : 'Upload Results'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}



