/**
 * Proactive LESSON cards — Mission Control strip (Phase 3C).
 * Polls /api/lessons/proactive; never invents lesson ids.
 */
import { useEffect, useState } from 'react';
import { BookMarked } from 'lucide-react';
import clsx from 'clsx';

interface LessonCard {
  severity: string;
  lessonId: string;
  title: string;
  summary?: string;
  sourceRefs?: string[];
  matchScore?: number;
}

export function LessonProactiveStrip({ className }: { className?: string }) {
  const [cards, setCards] = useState<LessonCard[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const res = await fetch('/api/lessons/proactive?zoneId=B-04');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const body = (await res.json()) as { proactiveCards?: LessonCard[] };
        if (!cancelled) {
          setCards(body.proactiveCards ?? []);
          setError(null);
        }
      } catch {
        if (!cancelled) setError('lessons feed offline');
      }
    };
    void load();
    const id = setInterval(() => void load(), 15000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  if (error && cards.length === 0) {
    return (
      <div
        className={clsx(
          'border-b border-line bg-panel px-4 py-1.5 flex items-center gap-3 min-h-[28px]',
          className,
        )}
        aria-label="Lessons learned"
      >
        <span className="flex items-center gap-1.5 shrink-0 text-micro font-mono uppercase tracking-[0.08em] text-ink-dim">
          <BookMarked className="h-3 w-3" />
          Lessons
        </span>
        <span className="text-xs text-ink-dim truncate">{error}</span>
      </div>
    );
  }

  if (cards.length === 0) return null;

  return (
    <div
      className={clsx(
        'border-b border-line bg-panel px-4 py-1.5 flex items-center gap-3 min-h-[28px] overflow-hidden',
        className,
      )}
      aria-label="Proactive lessons"
    >
      <span className="flex items-center gap-1.5 shrink-0 text-micro font-mono uppercase tracking-[0.08em] text-ink-dim">
        <BookMarked className="h-3 w-3" />
        Lesson
      </span>
      <div className="flex-1 min-w-0 overflow-hidden">
        <div className="flex gap-6">
          {cards.slice(0, 2).map((c) => (
            <span key={c.lessonId} className="text-xs text-ink whitespace-nowrap shrink-0">
              <span className="font-mono text-watch mr-1.5">{c.lessonId}</span>
              {(c.title || '').slice(0, 88)}
              {(c.title || '').length > 88 ? '…' : ''}
              {c.sourceRefs?.[0] ? (
                <span className="font-mono text-ink-dim ml-1.5">← {c.sourceRefs[0]}</span>
              ) : null}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
