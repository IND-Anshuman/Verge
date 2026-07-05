export type SSEEventHandler = (data: unknown) => void;

interface SSEOptions {
  onMessage: SSEEventHandler;
  onError?: (error: Event) => void;
  onOpen?: () => void;
}

export function createSSEConnection(
  url: string,
  options: SSEOptions
): EventSource {
  const source = new EventSource(url);

  source.onmessage = (event) => {
    try {
      const data: unknown = JSON.parse(event.data as string);
      options.onMessage(data);
    } catch {
      console.warn('[SSE] Failed to parse message:', event.data);
    }
  };

  source.onerror = (event) => {
    options.onError?.(event);
  };

  source.onopen = () => {
    options.onOpen?.();
  };

  return source;
}
