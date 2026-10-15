import React, { useState, useRef, useEffect } from 'react';
import { Book } from '../../types';
import { useIntakeQueue, useShelveBook } from '../../hooks/useCirculation';
import { StatusBadge } from '../StatusBadge';
import {
  Inbox,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Loader2,
  X,
  BookOpen,
  Calendar,
  Layers,
  ArrowRight,
} from 'lucide-react';

interface ToastState {
  message: string;
  type: 'success' | 'error';
}

export function TriageDeskView() {
  const { data: queue = [], isLoading, isError, error, refetch } = useIntakeQueue();
  const shelveMutation = useShelveBook();

  const [toast, setToast] = useState<ToastState | null>(null);
  const toastTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const showToast = (message: string, type: 'success' | 'error') => {
    if (toastTimeoutRef.current) {
      clearTimeout(toastTimeoutRef.current);
    }
    setToast({ message, type });
    toastTimeoutRef.current = setTimeout(() => {
      setToast(null);
    }, 4500);
  };

  useEffect(() => {
    return () => {
      if (toastTimeoutRef.current) {
        clearTimeout(toastTimeoutRef.current);
      }
    };
  }, []);

  // Track active shelving book ID for isolated loading spinner
  const shelvingBookId = shelveMutation.isPending ? shelveMutation.variables ?? null : null;

  const handleDirectShelve = (book: Book) => {
    if (shelvingBookId === book.id) return;

    shelveMutation.mutate(book.id, {
      onSuccess: () => {
        showToast(
          `"${book.title}" inspected and shelved back to open stacks (AVAILABLE).`,
          'success'
        );
      },
      onError: (err) => {
        showToast(
          err.message || `Failed to shelve "${book.title}". It may have already been processed.`,
          'error'
        );
      },
    });
  };

  return (
    <div className="w-full space-y-6">
      {/* Toast Notification */}
      {toast && (
        <div
          role="alert"
          aria-live="polite"
          className={`p-4 rounded-xl border flex items-center justify-between shadow-sm transition-all duration-200 ${
            toast.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
              : 'bg-rose-50 border-rose-200 text-rose-900'
          }`}
        >
          <div className="flex items-center space-x-2.5">
            {toast.type === 'success' ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
            )}
            <span className="text-sm font-medium">{toast.message}</span>
          </div>
          <button
            type="button"
            onClick={() => setToast(null)}
            className="text-slate-400 hover:text-slate-600 p-1 focus:outline-none"
            title="Dismiss notification"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Header Banner */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2.5">
              <div className="p-2 bg-amber-50 text-amber-700 rounded-lg">
                <Inbox className="w-5 h-5" />
              </div>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">
                Reverse Logistics Intake & Shelving Desk
              </h2>
            </div>
            <p className="text-sm text-slate-500 mt-1 max-w-2xl">
              FIFO queue of returned volumes awaiting physical staff inspection before returning to open stacks circulation.
            </p>
          </div>

          <div className="flex items-center space-x-3 shrink-0">
            <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-bold bg-amber-100 text-amber-900 border border-amber-200">
              <span className="w-2 h-2 rounded-full bg-amber-500 mr-2 animate-pulse" />
              {queue.length} Awaiting Shelving
            </span>
            <button
              type="button"
              onClick={() => refetch()}
              className="p-2 rounded-lg border border-slate-200 text-slate-500 hover:text-slate-900 hover:bg-slate-50 transition-colors"
              title="Refresh queue"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Workflow Info Strip */}
        <div className="mt-4 pt-4 border-t border-slate-100 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-slate-500">
          <div className="flex items-center space-x-2">
            <span className="font-semibold text-slate-700">Workflow:</span>
            <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-800 font-medium border border-amber-200">
              IN_PROCESSING
            </span>
            <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
            <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 font-medium border border-emerald-200">
              AVAILABLE (Stacks)
            </span>
          </div>
          <span className="text-slate-400">|</span>
          <span className="text-slate-500">
            Click <strong>Shelve to Stacks</strong> after verifying physical condition.
          </span>
        </div>
      </div>

      {/* Error State */}
      {isError && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-6 text-center">
          <AlertTriangle className="w-8 h-8 text-rose-500 mx-auto mb-2" />
          <h3 className="text-sm font-semibold text-rose-900">Failed to load intake queue</h3>
          <p className="text-xs text-rose-600 max-w-md mx-auto mt-1 mb-4">
            {error?.message || 'Could not connect to reverse logistics service.'}
          </p>
          <button
            type="button"
            onClick={() => refetch()}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-rose-600 hover:bg-rose-700 text-white shadow-xs"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, idx) => (
            <div
              key={idx}
              className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs animate-pulse flex items-center justify-between"
            >
              <div className="flex items-center space-x-4">
                <div className="w-12 h-16 bg-slate-200 rounded-md" />
                <div className="space-y-2">
                  <div className="h-4 bg-slate-200 rounded w-48" />
                  <div className="h-3 bg-slate-200 rounded w-32" />
                  <div className="h-3 bg-slate-100 rounded w-24" />
                </div>
              </div>
              <div className="h-9 bg-slate-200 rounded w-36" />
            </div>
          ))}
        </div>
      )}

      {/* Queue List */}
      {!isLoading && !isError && (
        queue.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 p-12 text-center bg-white shadow-xs">
            <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-slate-900">
              All returned items triaged and shelved to open stacks
            </h3>
            <p className="text-sm text-slate-500 max-w-sm mx-auto mt-1">
              The intake queue is completely clear. Newly returned volumes from patron drop-offs will appear here automatically.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center justify-between px-1">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Items Awaiting Shelving (FIFO Order)
              </span>
              <span className="text-xs text-slate-400">
                Sorted by return arrival time
              </span>
            </div>

            <div className="grid grid-cols-1 gap-3">
              {queue.map((book) => {
                const isItemShelving = shelvingBookId === book.id;

                return (
                  <div
                    key={book.id}
                    className="bg-white rounded-xl border border-slate-200 p-4 sm:p-5 shadow-xs hover:border-slate-300 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                  >
                    {/* Book Metadata & State */}
                    <div className="flex items-start sm:items-center space-x-4 flex-1">
                      {book.cover_image_url ? (
                        <img
                          src={book.cover_image_url}
                          alt={book.title}
                          className="w-12 h-16 sm:w-14 sm:h-20 object-cover rounded-md border border-slate-200 shrink-0"
                        />
                      ) : (
                        <div className="w-12 h-16 sm:w-14 sm:h-20 bg-slate-100 rounded-md border border-slate-200 flex items-center justify-center text-slate-400 shrink-0">
                          <BookOpen className="w-6 h-6 stroke-1" />
                        </div>
                      )}

                      <div className="space-y-1 flex-1 min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <h4 className="font-bold text-slate-900 text-sm sm:text-base leading-snug line-clamp-1">
                            {book.title}
                          </h4>
                          <StatusBadge status="IN_PROCESSING" />
                        </div>

                        <p className="text-xs text-slate-600 font-medium line-clamp-1">
                          by <span className="text-slate-800">{book.author}</span>
                        </p>

                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs pt-1">
                          {book.dewey_decimal && (
                            <span className="font-mono bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded text-[11px] font-semibold">
                              Call: {book.dewey_decimal}
                            </span>
                          )}
                          {book.isbn && (
                            <span className="text-slate-500 font-mono text-[11px]">
                              ISBN: {book.isbn}
                            </span>
                          )}
                          <span className="text-slate-400 flex items-center text-[11px]">
                            <Calendar className="w-3 h-3 mr-1" />
                            Arrived:{' '}
                            {book.updated_at
                              ? new Date(book.updated_at).toLocaleDateString(undefined, {
                                  month: 'short',
                                  day: 'numeric',
                                  hour: '2-digit',
                                  minute: '2-digit',
                                })
                              : 'Just now'}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Direct 1-Click Shelving Action */}
                    <div className="sm:self-center shrink-0">
                      <button
                        type="button"
                        disabled={isItemShelving}
                        onClick={() => handleDirectShelve(book)}
                        className="w-full sm:w-auto inline-flex items-center justify-center space-x-1.5 px-4 py-2 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs transition-all cursor-pointer active:scale-95 disabled:opacity-70 disabled:cursor-not-allowed"
                        title="Confirm inspection and return book to open stacks (AVAILABLE)"
                      >
                        {isItemShelving ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            <span>Shelving Volume...</span>
                          </>
                        ) : (
                          <>
                            <CheckCircle2 className="w-4 h-4" />
                            <span>Shelve to Stacks</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )
      )}
    </div>
  );
}

export default TriageDeskView;

