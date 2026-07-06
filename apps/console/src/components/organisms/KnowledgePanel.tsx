import { useState } from 'react';
import { Badge, Button } from '@/components/atoms';
import { Send, FileText, ExternalLink } from 'lucide-react';

interface QuestionMessage {
  sender: 'operator' | 'rag';
  text: string;
  timestamp: string;
  citations?: string[];
  confidence?: number;
}

export function KnowledgePanel() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<QuestionMessage[]>([
    {
      sender: 'rag',
      text: 'SYSTEM RECOMMENDATION: Based on convergence of methane and PTW hot-work welding, similar incident detected at Visakhapatnam Reformer (2025). The incident resulted in an ignition because gas migration from secondary lines was not isolated.',
      timestamp: new Date(Date.now() - 3600000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      confidence: 0.88,
      citations: ['OISD-137 Clause 4.2', 'Factories Act Sec 38'],
    },
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userMessage: QuestionMessage = {
      sender: 'operator',
      text: query.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setQuery('');
    setIsSubmitting(true);

    try {
      // Simulate RAG AI delay
      await new Promise((resolve) => setTimeout(resolve, 1500));

      const ragResponse: QuestionMessage = {
        sender: 'rag',
        text: 'AI ANALYSIS: Section 4.2 of OISD-137 mandates positive physical isolation (blind flanges) for reformer line maintenance whenever adjacent hot work is authorized. RAG confidence high. No other conflicting regulations found.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        confidence: 0.94,
        citations: ['OISD-137 Clause 4.2 (Blinding/Isolation)'],
      };

      setMessages((prev) => [...prev, ragResponse]);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col gap-4 text-ink h-full select-none">
      {/* Messages Scroll viewport */}
      <div className="flex-1 overflow-y-auto flex flex-col gap-3 pr-1 scrollbar select-text">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex flex-col gap-2 p-3 rounded border ${
              m.sender === 'rag'
                ? 'bg-panel border-line text-ink'
                : 'bg-panel-2 border-line/60 text-ink-dim'
            }`}
          >
            {/* Header row */}
            <div className="flex justify-between items-center text-micro font-mono text-ink-dim select-none">
              <span className="font-bold uppercase tracking-wider">
                {m.sender === 'rag' ? 'VERGE INTELLIGENCE (RAG)' : 'OPERATOR QUERY'}
              </span>
              <span>{m.timestamp}</span>
            </div>

            {/* Message text */}
            <p className="text-xs leading-relaxed">{m.text}</p>

            {/* Citations & Confidence badges */}
            {m.sender === 'rag' && (
              <div className="flex flex-wrap items-center gap-1.5 mt-1 select-none border-t border-line/40 pt-2 shrink-0">
                {m.confidence !== undefined && (
                  <Badge
                    variant="generic"
                    color={m.confidence >= 0.85 ? 'ok' : 'near'}
                    className="text-micro font-mono font-bold"
                  >
                    CONF: {(m.confidence * 100).toFixed(0)}%
                  </Badge>
                )}
                {m.citations?.map((cit) => (
                  <a
                    key={cit}
                    href="#citation"
                    className="inline-flex items-center gap-1 text-micro font-mono text-watch hover:text-accent border border-watch/20 hover:border-accent/40 bg-watch/5 px-2 py-0.5 rounded transition-all"
                  >
                    <FileText className="h-3 w-3" />
                    {cit}
                    <ExternalLink className="h-2.5 w-2.5" />
                  </a>
                ))}
              </div>
            )}
          </div>
        ))}

        {isSubmitting && (
          <div className="p-3 border border-line bg-panel rounded flex flex-col gap-1.5 select-none shrink-0">
            <span className="text-micro font-mono text-ink-dim uppercase animate-pulse">
              AI Query Parsing...
            </span>
            <div className="h-2 bg-line rounded w-3/4 animate-pulse" />
          </div>
        )}
      </div>

      {/* Query Text Input Bar */}
      <form onSubmit={handleSend} className="flex gap-2 border-t border-line pt-3 shrink-0 select-none">
        <input
          type="text"
          placeholder="Ask a question about OISD, Factories Act, or past incidents..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={isSubmitting}
          className="flex-1 h-8 px-3 rounded border border-line text-xs bg-panel-2 text-ink placeholder:text-ink-dim/40 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent"
        />
        <Button
          variant="primary"
          size="sm"
          type="submit"
          loading={isSubmitting}
          disabled={!query.trim()}
          icon={<Send className="h-3.5 w-3.5" />}
          className="h-8 uppercase text-micro font-mono font-bold"
        >
          Send
        </Button>
      </form>
    </div>
  );
}
