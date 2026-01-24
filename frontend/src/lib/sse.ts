/**
 * SSE Connection Manager
 * 
 * Handles Server-Sent Events for real-time agent progress updates.
 */

export interface SSEEvent {
    type: string;
    data: any;
}

export function createSSEConnection(
    url: string,
    onEvent: (event: SSEEvent) => void,
    onError?: (error: Event) => void,
    onComplete?: () => void
): EventSource {
    const eventSource = new EventSource(url, { withCredentials: true });

    eventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            onEvent({ type: 'message', data });
        } catch (e) {
            console.error('Failed to parse SSE message:', e);
        }
    };

    // Listen for custom event types
    const eventTypes = [
        'agent_start',
        'tool_call',
        'tool_result',
        'agent_note',
        'partial_output',
        'artifact_ready',
        'run_complete',
        'run_error',
    ];

    eventTypes.forEach((eventType) => {
        eventSource.addEventListener(eventType, (event) => {
            try {
                const data = JSON.parse((event as MessageEvent).data);
                onEvent({ type: eventType, data });

                // Close connection on completion or error
                if (eventType === 'run_complete' || eventType === 'run_error') {
                    eventSource.close();
                    onComplete?.();
                }
            } catch (e) {
                console.error(`Failed to parse ${eventType} event:`, e);
            }
        });
    });

    eventSource.onerror = (error) => {
        console.error('SSE connection error:', error);
        onError?.(error);
        eventSource.close();
    };

    return eventSource;
}

export function closeSSEConnection(eventSource: EventSource | null): void {
    if (eventSource) {
        eventSource.close();
    }
}
