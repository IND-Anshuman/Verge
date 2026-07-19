import { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Button, EmptyState } from '@/components/atoms';
import {
  BookOpen,
  Upload,
  Search,
  CornerDownRight,
  AlertTriangle,
  X,
  Crosshair,
} from 'lucide-react';
import clsx from 'clsx';
import {
  askKnowledge,
  ingestDocument,
  listDocuments,
  type KnowledgeCitation,
  type KnowledgeDocument,
} from '@/api/knowledge';
import { getFinding } from '@/api';
import type { RiskFinding } from '@/types';

/* ── Plant Copilot — Living Knowledge (design_plan §6.3) ─────────────
   Threaded, grounded chat over the ingested corpus: every turn carries
   its own citation rail or an honest "cannot answer from corpus". The
   corpus rail grows the library; the thread asks it. `?finding=` scopes
   the conversation to one finding (deep link from /findings/:id).
   Quiet and document-forward — no purple "AI" chrome (§4). */

interface Turn {
  id: number;
  query: string;
  answer: string;
  citations: KnowledgeCitation[];
  degraded: boolean;
  reason: string;
  error: string | null;
  pending: boolean;
}

function docHealth(d: KnowledgeDocument): 'ok' | 'failed' | 'pending' {
  const s = d.status.toLowerCase();
  if (d.error || s.includes('fail') || s.includes('error')) return 'failed';
  if (s.includes('pend') || s.includes('process') || s.includes('ingest')) return 'pending';
  return 'ok';
}

export default function KnowledgeView() {
  const [docs, setDocs] = useState<KnowledgeDocument[]>([]);
  const [query, setQuery] = useState('');
  const [turns, setTurns] = useState<Turn[]>([]);
  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [corpusError, setCorpusError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const threadEndRef = useRef<HTMLDivElement>(null);
  const nextId = useRef(1);

  // ── Finding scope (deep link: /knowledge?finding=VF-…) ────────────
  const [searchParams, setSearchParams] = useSearchParams();
  const scopeId = searchParams.get('finding');
  const [scopeFinding, setScopeFinding] = useState<RiskFinding | null>(null);

  useEffect(() => {
    if (!scopeId) {
      setScopeFinding(null);
      return;
    }
    const ctrl = new AbortController();
    getFinding(scopeId, ctrl.signal)
      .then((f) => setScopeFinding(f))
      .catch(() => setScopeFinding(null));
    return () => ctrl.abort();
  }, [scopeId]);

  const clearScope = () => {
    searchParams.delete('finding');
    setSearchParams(searchParams, { replace: true });
  };

  const refresh = async () => {
    try {
      const res = await listDocuments();
      setDocs(res.documents);
      setCorpusError(null);
    } catch {
      setCorpusError('Knowledge API unavailable — start API with `make dev`.');
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  // New turns settle into view.
  useEffect(() => {
    threadEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [turns]);

  const onUpload = async (file: File | null) => {
    if (!file) return;
    setUploading(true);
    setCorpusError(null);
    try {
      await ingestDocument(file, file.name);
      await refresh();
    } catch {
      setCorpusError(`Ingest failed for ${file.name}.`);
    } finally {
      setUploading(false);
    }
  };

  const onAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    const q = query.trim();
    if (!q || asking) return;

    // Scope context rides along in the query text — the retrieval layer
    // matches zone/equipment tokens, so this is real grounding, not chrome.
    const sent = scopeId
      ? `${q} (context: finding ${scopeId}${scopeFinding ? ` — ${scopeFinding.title}, zone ${scopeFinding.zoneId}` : ''})`
      : q;

    const id = nextId.current++;
    setTurns((prev) => [
      ...prev,
      { id, query: q, answer: '', citations: [], degraded: false, reason: '', error: null, pending: true },
    ]);
    setQuery('');
    setAsking(true);
    try {
      const res = await askKnowledge(sent);
      setTurns((prev) =>
        prev.map((t) =>
          t.id === id
            ? {
                ...t,
                pending: false,
                answer: res.answer,
                citations: res.citations,
                degraded: res.degraded,
                reason: res.reason,
              }
            : t,
        ),
      );
    } catch {
      setTurns((prev) =>
        prev.map((t) =>
          t.id === id
            ? {
                ...t,
                pending: false,
                error: 'The corpus could not be queried. Check that the API is running, then ask again.',
              }
            : t,
        ),
      );
    } finally {
      setAsking(false);
    }
  };

  return (
    <div className="flex flex-col gap-4 p-4 h-full overflow-hidden text-ink">
      {/* Page header — editorial: sentence-case title, one-line dim subtitle */}
      <div className="flex items-end justify-between gap-4 border-b border-line pb-3 shrink-0">
        <div className="flex flex-col gap-1 min-w-0">
          <h1 className="text-lg font-semibold tracking-tight flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-ink-dim" />
            Plant Copilot
          </h1>
          <p className="text-xs text-ink-dim">
            Ingest SOPs, work orders, and procedures — ask with citations. An empty corpus stays empty.
          </p>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".md,.txt,text/markdown,text/plain"
          className="hidden"
          onChange={(e) => {
            void onUpload(e.target.files?.[0] ?? null);
            e.target.value = '';
          }}
        />
        <Button
          variant="secondary"
          size="sm"
          icon={<Upload className="h-3.5 w-3.5" />}
          loading={uploading}
          onClick={() => fileInputRef.current?.click()}
          className="shrink-0"
        >
          {uploading ? 'Ingesting…' : 'Ingest document'}
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[300px_minmax(0,1fr)] gap-4 min-h-0 flex-1">
        {/* ── Corpus rail ─────────────────────────────── */}
        <section
          aria-label="Document corpus"
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            void onUpload(e.dataTransfer.files?.[0] ?? null);
          }}
          className={clsx(
            'surface-1 p-3 flex flex-col gap-2 min-h-0 overflow-hidden transition-colors duration-fast',
            dragOver && 'border-ink bg-panel-2/60',
          )}
        >
          <span className="ruled-label">
            Corpus · <span className="tabular-nums">{docs.length}</span>
          </span>

          {corpusError && (
            <div className="bg-imminent/10 border border-imminent/20 rounded p-2 flex items-baseline gap-1.5 select-text">
              <AlertTriangle className="h-3 w-3 shrink-0 self-center text-imminent" />
              <span className="text-micro text-ink leading-normal">{corpusError}</span>
            </div>
          )}

          <div className="flex-1 overflow-y-auto scrollbar flex flex-col gap-1.5">
            {docs.length === 0 ? (
              <EmptyState
                icon={<BookOpen />}
                title="No documents yet"
                hint="Drop a .md or .txt SOP here, or use Ingest document. Verge will not invent a library."
                action={
                  <Button
                    variant="secondary"
                    size="sm"
                    icon={<Upload className="h-3 w-3" />}
                    loading={uploading}
                    onClick={() => fileInputRef.current?.click()}
                  >
                    Upload first document
                  </Button>
                }
                className="flex-1"
              />
            ) : (
              docs.map((d) => {
                const health = docHealth(d);
                return (
                  <div
                    key={d.documentId}
                    className="border border-line rounded p-2.5 text-xs flex flex-col gap-1 hover-elevate bg-panel"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold truncate text-ink" title={d.title}>
                        {d.title}
                      </span>
                      <span className="font-mono text-micro text-ink-dim uppercase shrink-0">
                        {d.kind}
                      </span>
                    </div>
                    <span className="font-mono text-micro text-ink-dim flex items-center gap-1.5 min-w-0">
                      <span
                        className={clsx(
                          'h-1.5 w-1.5 rounded-full shrink-0',
                          health === 'ok' ? 'bg-ok' : health === 'failed' ? 'bg-imminent' : 'bg-unknown',
                        )}
                        title={d.status}
                      />
                      <span className="truncate">
                        {d.status} · <span className="tabular-nums">{d.textChars.toLocaleString()}</span> chars ·{' '}
                        {d.documentId}
                      </span>
                    </span>
                    {d.error && (
                      <span className="font-mono text-micro text-imminent leading-normal select-text">
                        {d.error}
                      </span>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </section>

        {/* ── Thread: turns + composer ─────────────────── */}
        <section aria-label="Copilot thread" className="surface-1 flex flex-col min-h-0 overflow-hidden">
          {/* Thread */}
          <div className="flex-1 overflow-y-auto scrollbar flex flex-col gap-6 min-h-0 p-4">
            {turns.length === 0 ? (
              <div className="flex-1 flex items-center justify-center">
                {/* The route's one display moment (§13.1) — an invitation, not a toolbar */}
                <div className="flex flex-col items-center gap-3 text-center max-w-md select-none">
                  <span className="text-[28px] leading-snug font-semibold tracking-tight text-ink">
                    {docs.length === 0 ? 'Ingest a document, then ask.' : 'Ask the plant.'}
                  </span>
                  <span className="text-sm text-ink-dim leading-relaxed">
                    Every answer is grounded in the corpus and cited — or honestly empty. Verge never
                    invents SOP text.
                  </span>
                </div>
              </div>
            ) : (
              turns.map((turn) => (
                <article key={turn.id} className="flex flex-col gap-2 select-text">
                  {/* Operator turn */}
                  <p className="text-sm font-medium text-ink flex items-start gap-1.5">
                    <CornerDownRight className="h-3.5 w-3.5 shrink-0 mt-0.5 text-ink-dim" />
                    {turn.query}
                  </p>

                  {/* Answer turn */}
                  {turn.pending ? (
                    <div className="border border-line rounded-md bg-panel-2/40 p-4 text-xs font-mono text-ink-dim">
                      Consulting the corpus…
                    </div>
                  ) : turn.error ? (
                    <div className="bg-imminent/10 border border-imminent/20 rounded p-3 flex items-baseline gap-2">
                      <AlertTriangle className="h-3.5 w-3.5 shrink-0 self-center text-imminent" />
                      <span className="text-micro font-mono uppercase tracking-[0.08em] text-imminent font-semibold shrink-0">
                        Ask failed
                      </span>
                      <span className="text-xs text-ink leading-normal">{turn.error}</span>
                    </div>
                  ) : (
                    <>
                      <div className="border border-line rounded-md bg-panel p-4 text-sm leading-relaxed whitespace-pre-wrap">
                        {turn.answer || 'The corpus cannot answer this — no matching grounded material.'}
                      </div>
                      {turn.degraded && (
                        <div className="bg-near/10 border border-near/25 rounded p-2 flex items-baseline gap-2">
                          <span className="text-micro font-mono uppercase tracking-[0.08em] text-near font-semibold shrink-0">
                            Degraded
                          </span>
                          <span className="text-micro text-ink leading-normal">
                            {turn.reason || 'Partial grounding — treat as a pointer, not an instruction.'}
                          </span>
                        </div>
                      )}
                      {turn.citations.length > 0 && (
                        <div className="flex flex-col gap-1.5 pl-3 border-l-2 border-line-2">
                          <span className="text-micro font-mono uppercase tracking-[0.1em] text-ink-dim">
                            Citations · <span className="tabular-nums">{turn.citations.length}</span>
                          </span>
                          {turn.citations.map((c, i) => (
                            <div
                              key={`${turn.id}-${c.chunkId ?? i}`}
                              className="border border-line rounded p-2.5 text-xs bg-panel hover-elevate"
                            >
                              <div className="flex items-baseline justify-between gap-2 mb-1">
                                <span className="font-mono text-micro text-ink font-semibold truncate">
                                  [{i + 1}] {c.title}
                                  {c.page != null && <span className="text-ink-dim"> · p.{c.page}</span>}
                                </span>
                                <span className="font-mono text-micro text-ink-dim tabular-nums shrink-0">
                                  score {c.score}
                                </span>
                              </div>
                              <p className="text-ink-dim leading-relaxed">{c.excerpt}</p>
                              {c.chunkId && (
                                <span className="font-mono text-micro text-ink-dim/60 block mt-1 truncate">
                                  {c.chunkId}
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </article>
              ))
            )}
            <div ref={threadEndRef} />
          </div>

          {/* Composer */}
          <div className="border-t border-line p-3 flex flex-col gap-2 shrink-0 bg-panel">
            {scopeId && (
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1.5 h-6 pl-2 pr-1 rounded border border-line bg-panel-2 text-micro font-mono text-ink">
                  <Crosshair className="h-3 w-3 text-ink-dim" />
                  <span className="uppercase tracking-[0.06em]">
                    Scoped · {scopeId}
                    {scopeFinding && ` · ${scopeFinding.zoneId}`}
                  </span>
                  <button
                    onClick={clearScope}
                    aria-label="Clear finding scope"
                    className="text-ink-dim hover:text-ink transition-colors duration-fast cursor-pointer p-0.5"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
                {scopeFinding && (
                  <span className="text-micro text-ink-dim truncate">{scopeFinding.title}</span>
                )}
              </div>
            )}
            <form onSubmit={onAsk} className="flex gap-2">
              <div className="relative flex-1">
                <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-dim/40 pointer-events-none">
                  <Search className="h-4 w-4" />
                </span>
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={
                    scopeId
                      ? `Ask about ${scopeId} — e.g. which SOP governs this zone?`
                      : 'e.g. What must be checked before hot work in B-04?'
                  }
                  aria-label="Question for the plant corpus"
                  className="w-full h-10 pl-8 pr-3 rounded border border-line bg-panel text-base text-ink placeholder:text-ink-dim/60 focus:outline-none focus:border-accent transition-colors duration-fast"
                />
              </div>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                loading={asking}
                disabled={!query.trim()}
                className="h-10 px-5 text-sm"
              >
                {asking ? 'Asking…' : 'Ask'}
              </Button>
            </form>
          </div>
        </section>
      </div>
    </div>
  );
}
