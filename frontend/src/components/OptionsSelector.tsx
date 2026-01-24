import { ArrowRight, Lightbulb, Sparkles } from 'lucide-react';
import { cn } from '../lib/utils';
import type { AgentRun } from '../lib/api';

interface OptionsSelectorProps {
    run: AgentRun;
    onSelect: (direction: any) => void;
    isLoading?: boolean;
}

export function OptionsSelector({ run, onSelect, isLoading }: OptionsSelectorProps) {
    // Extract directions from run result
    // Fallback to empty array if not present (should be ensured by backend)
    const directions = run.result?.directions || [];

    if (directions.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center p-12 text-center h-full">
                <div className="w-16 h-16 bg-amber-500/10 rounded-full flex items-center justify-center mb-4">
                    <Sparkles className="w-8 h-8 text-amber-500" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Analyzing Field...</h3>
                <p className="text-[var(--color-text-secondary)] max-w-md">
                    Our agents are currently scanning recent literature to find the most promising
                    research directions for you.
                </p>
            </div>
        );
    }

    return (
        <div className="p-6 h-full overflow-y-auto">
            <div className="max-w-5xl mx-auto space-y-8">
                <div className="text-center space-y-2">
                    <h2 className="text-2xl font-bold">Research Directions Found</h2>
                    <p className="text-[var(--color-text-secondary)]">
                        Based on your topic, we identified 5 potential research directions.
                        Each includes analysis of the field. Select one to start a deep dive.
                    </p>
                </div>

                <div className="space-y-4">
                    {directions.map((direction: any, index: number) => (
                        <div
                            key={index}
                            className={cn(
                                "rounded-xl border border-[var(--color-border)] hover:border-[var(--color-primary)] transition-all bg-[var(--color-bg-secondary)] overflow-hidden",
                                isLoading && "opacity-50"
                            )}
                        >
                            <div className="p-6">
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-lg bg-[var(--color-primary)]/10 flex items-center justify-center">
                                            <Lightbulb className="w-5 h-5 text-[var(--color-primary)]" />
                                        </div>
                                        <div>
                                            <span className="text-xs font-medium text-[var(--color-text-muted)]">
                                                Direction {index + 1}
                                            </span>
                                            <h3 className="text-lg font-semibold">
                                                {direction.title}
                                            </h3>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => onSelect(direction)}
                                        disabled={isLoading}
                                        className="btn btn-primary text-sm disabled:opacity-50"
                                    >
                                        Select <ArrowRight className="w-4 h-4 ml-1" />
                                    </button>
                                </div>

                                <p className="text-[var(--color-text-secondary)] mb-4">
                                    {direction.description}
                                </p>

                                {/* Rich content sections */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                    {direction.past_approaches && (
                                        <div className="p-3 rounded-lg bg-[var(--color-bg-tertiary)]">
                                            <h4 className="font-medium text-blue-400 mb-1">Past Approaches</h4>
                                            <p className="text-[var(--color-text-muted)]">{direction.past_approaches}</p>
                                        </div>
                                    )}
                                    {direction.current_state && (
                                        <div className="p-3 rounded-lg bg-[var(--color-bg-tertiary)]">
                                            <h4 className="font-medium text-purple-400 mb-1">Current State</h4>
                                            <p className="text-[var(--color-text-muted)]">{direction.current_state}</p>
                                        </div>
                                    )}
                                    {direction.gaps && (
                                        <div className="p-3 rounded-lg bg-[var(--color-bg-tertiary)]">
                                            <h4 className="font-medium text-amber-400 mb-1">Research Gaps</h4>
                                            <p className="text-[var(--color-text-muted)]">{direction.gaps}</p>
                                        </div>
                                    )}
                                    {direction.improvements && (
                                        <div className="p-3 rounded-lg bg-[var(--color-bg-tertiary)]">
                                            <h4 className="font-medium text-green-400 mb-1">Potential Improvements</h4>
                                            <p className="text-[var(--color-text-muted)]">{direction.improvements}</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
