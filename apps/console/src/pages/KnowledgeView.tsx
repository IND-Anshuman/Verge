import { useEffect, useRef, useState } from 'react';
import { Button, EmptyState } from '@/components/atoms';
import { BookOpen, Upload, Search, CornerDownRight, AlertTriangle } from 'lucide-react';
import clsx from 'clsx';
import {
  askKnowledge,
  ingestDocument,
  listDocuments,
  type KnowledgeCitation,
  type KnowledgeDocument,
} from '@/api/knowledge';

/* Living Knowledge — one composition: corpus rail | ask → answer → citations.
   The corpus never invents documents; the answer is grounded or honestly
   degraded; upload and ask are separate verbs with separate busy states. */

function docHealth(d: KnowledgeDocument): 'ok' | 'failed' | 'pending' {
  const s = d.status.toLowerCase();
  if (d.error || s.includes('fail') || s.includes('error')) return 'failed';
  if (s.includes('pend') || s.includes('process') || s.includes('ingest')) return 'pending';
  return 'ok';
}

export default function KnowledgeView() {
  const [docs, setDocs] = useState<KnowledgeDocument[]>([]);
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [askedQuery, setAskedQuery] = useState('');
  const [citations, setCitations] = useState<KnowledgeCitation[]>([]);
  const [degraded, setDegraded] = useState(false);
  const [reason, setReason] = useState('');
  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [corpusError, setCorpusError] = useState<string | null>(null);
  const [askError, setAskError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
    if (!q) return;
    setAsking(true);
    setAskError(null);
    try {
      const res = await askKnowledge(q);
      setAnswer(res.answer);
      setAskedQuery(q);
      setCitations(res.citations);
      setDegraded(res.degraded);
      setReason(res.reason);
    } catch {
      setAskError('The corpus could not be queried. Check that the API is running, then ask again.');
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
            Living Knowledge
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

        {/* ── Ask → answer → citations ─────────────────── */}
        <section aria-label="Ask the corpus" className="surface-1 p-3 flex flex-col gap-3 min-h-0 overflow-hidden">
          <form onSubmit={onAsk} className="flex gap-2 shrink-0">
            <div className="relative flex-1">
              <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-dim/40 pointer-events-none">
                <Search className="h-4 w-4" />
              </span>
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. What must be checked before hot work in B-04?"
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

          <div className="flex-1 overflow-y-auto scrollbar flex flex-col gap-4 min-h-0">
            {askError ? (
              <div className="bg-imminent/10 border border-imminent/20 rounded p-3 flex items-baseline gap-2 select-text">
                <AlertTriangle className="h-3.5 w-3.5 shrink-0 self-center text-imminent" />
                <span className="text-micro font-mono uppercase tracking-[0.08em] text-imminent font-semibold shrink-0">
                  Ask failed
                </span>
                <span className="text-xs text-ink leading-normal">{askError}</span>
              </div>
            ) : answer ? (
              <article className="flex flex-col gap-2">
                <span className="ruled-label">Answer</span>
                <p className="text-micro font-mono text-ink-dim flex items-center gap-1 select-text">
                  <CornerDownRight className="h-3 w-3 shrink-0" />
                  {askedQuery}
                </p>
                <div className="border border-line rounded-md bg-panel p-4 text-sm leading-relaxed whitespace-pre-wrap select-text">
                  {answer}
                </div>
                {degraded && (
                  <div className="bg-near/10 border border-near/25 rounded p-2 flex items-baseline gap-2">
                    <span className="text-micro font-mono uppercase tracking-[0.08em] text-near font-semibold shrink-0">
                      Degraded
                    </span>
                    <span className="text-micro text-ink leading-normal">
                      {reason || 'Partial grounding — treat as a pointer, not an instruction.'}
                    </span>
                  </div>
                )}
              </article>
            ) : (
              <EmptyState
                icon={<Search />}
                title={docs.length === 0 ? 'Ingest a document, then ask' : 'Ask the plant corpus'}
                hint="Answers are grounded in ingested chunks with citations — or honestly empty."
                className="flex-1"
              />
            )}

            {!askError && citations.length > 0 && (
              <div className="flex flex-col gap-2">
                <span className="ruled-label">
                  Citations · <span className="tabular-nums">{citations.length}</span>
                </span>
                {citations.map((c, i) => (
                  <div
                    key={c.chunkId}
                    className="border border-line rounded p-2.5 text-xs bg-panel hover-elevate select-text"
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
                    <span className="font-mono text-micro text-ink-dim/60 block mt-1 truncate">
                      {c.chunkId}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
