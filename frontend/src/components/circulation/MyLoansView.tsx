import React, { useState, useRef, useEffect } from 'react';
import { useMyLoans, useReturnBook } from '../../hooks/useCirculation';
import { StatusBadge } from '../StatusBadge';
import {
  BookOpen,
  Clock,
  AlertTriangle,
  CheckCircle2,
  PackageCheck,
  RotateCcw,
  Loader2,
  ChevronDown,
  ChevronUp,
  X,
  Inbox,
  Calendar,
} from 'lucide-react';

export interface MyLoansViewProps {
  onBrowseCatalog?: () => void;
}

interface ToastState {
  message: string;
  type: 'success' | 'error';
}

function formatDueRelative(dueDateStr: string, isOverdue?: boolean): { text: string; isPast: boolean } {
  try {
    const due = new Date(dueDateStr);
    const now = new Date();
    const diffMs = due.getTime() - now.getTime();
    const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

    const dateFormatted = due.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });

    if (isOverdue || diffDays < 0) {
      const absDays = Math.abs(diffDays);
      return {
        text: `Overdue by ${absDays === 0 ? 'today' : `${absDays} day${absDays === 1 ? '' : 's'}`} (${dateFormatted})`,
        isPast: true,
      };
    }
    if (diffDays === 0) {
      return { text: `Due today (${dateFormatted})`, isPast: false };
    }
    return {
      text: `Due in ${diffDays} day${diffDays === 1 ? '' : 's'} (${dateFormatted})`,
      isPast: false,
    };
  } catch {
    return { text: dueDateStr, isPast: false };
  }
}

export function MyLoansView({ onBrowseCatalog }: MyLoansViewProps) {
  const { data: loans = [], isLoading, isError, error, refetch } = useMyLoans();
  const returnMutation = useReturnBook();

  const [showHistory, setShowHistory] = useState(false);
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

  const activeLoans = loans.filter((l) => l.status === 'ACTIVE');
  const pastLoans = loans.filter((l) => l.status === 'RETURNED');

  // Metrics
  const overdueCount = activeLoans.filter((l) => l.is_overdue).length;
  const dueSoonCount = activeLoans.filter((l) => {
    if (l.is_overdue) return false;
    try {
      const due = new Date(l.due_date);
      const now = new Date();
      const diffDays = (due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
      return diffDays <= 3 && diffDays >= 0;
    } catch {
      return false;
    }
  }).length;

  // Active returning loan ID for isolated spinner
  const returningLoanId = returnMutation.isPending ? returnMutation.variables ?? null : null;

  const handleReturn = (loanId: number, bookTitle?: string) => {
    if (returningLoanId === loanId) return;

    returnMutation.mutate(loanId, {
      onSuccess: () => {
        showToast(
          `"${bookTitle || 'Book'}" returned to intake desk for staff inspection.`,
          'success'
        );
      },
      onError: (err) => {
        showToast(err.message || 'Failed to process return.', 'error');
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
              <PackageCheck className="w-5 h-5 text-emerald-600 shrink-0" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
            )}
            <span className="text-sm font-medium">{toast.message}</span>
          </div>
          <button
            type="button"
            onClick={() => setToast(null)}
            className="text-slate-400 hover:text-slate-600 p-1 focus:outline-none"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Header & Metrics */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
        <div className="mb-6">
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            My Circulation & Loan History
          </h2>
          <p className="text-sm text-slate-500 mt-0.5">
            Manage your borrowed library books, view return due dates, and drop off items.
          </p>
        </div>

        {/* 3 Metrics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Active Loans */}
          <div className="p-4 rounded-lg border border-sky-200 bg-sky-50/50">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-bold uppercase tracking-wider text-sky-700">
                Active Loans
              </span>
              <BookOpen className="w-4 h-4 text-sky-600" />
            </div>
            <p className="text-2xl font-black text-sky-900">{activeLoans.length}</p>
            <p className="text-xs text-sky-600 mt-0.5">Currently checked out</p>
          </div>

          {/* Due Soon */}
          <div className="p-4 rounded-lg border border-amber-200 bg-amber-50/50">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-bold uppercase tracking-wider text-amber-700">
                Due Soon
              </span>
              <Clock className="w-4 h-4 text-amber-600" />
            </div>
            <p className="text-2xl font-black text-amber-900">{dueSoonCount}</p>
            <p className="text-xs text-amber-600 mt-0.5">Within next 3 days</p>
          </div>

          {/* Overdue Items */}
          <div className="p-4 rounded-lg border border-rose-200 bg-rose-50/50">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-bold uppercase tracking-wider text-rose-700">
                Overdue Items
              </span>
              <AlertTriangle className={`w-4 h-4 text-rose-600 ${overdueCount > 0 ? 'badge-pulse' : ''}`} />
            </div>
            <p className="text-2xl font-black text-rose-900">{overdueCount}</p>
            <p className="text-xs text-rose-600 mt-0.5">Past due return date</p>
          </div>
        </div>
      </div>

      {/* Error State */}
      {isError && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-6 text-center">
          <AlertTriangle className="w-8 h-8 text-rose-500 mx-auto mb-2" />
          <h3 className="text-sm font-semibold text-rose-900">Failed to load loan records</h3>
          <p className="text-xs text-rose-600 max-w-md mx-auto mt-1 mb-4">
            {error?.message || 'Could not connect to circulation service.'}
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
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, idx) => (
            <div
              key={idx}
              className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs animate-pulse flex items-center justify-between"
            >
              <div className="flex items-center space-x-4">
                <div className="w-14 h-20 bg-slate-200 rounded-md" />
                <div className="space-y-2">
                  <div className="h-4 bg-slate-200 rounded w-48" />
                  <div className="h-3 bg-slate-200 rounded w-32" />
                  <div className="h-3 bg-slate-100 rounded w-24" />
                </div>
              </div>
              <div className="h-9 bg-slate-200 rounded w-32" />
            </div>
          ))}
        </div>
      )}

      {/* Active Loans Section */}
      {!isLoading && !isError && (
        <div className="space-y-4">
          <div className="flex items-center justify-between px-1">
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
              Active Loans ({activeLoans.length})
            </h3>
            {activeLoans.length > 0 && onBrowseCatalog && (
              <button
                type="button"
                onClick={onBrowseCatalog}
                className="text-xs font-medium text-indigo-600 hover:text-indigo-800"
              >
                + Borrow more books
              </button>
            )}
          </div>

          {activeLoans.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-300 p-12 text-center bg-white shadow-xs">
              <Inbox className="w-12 h-12 text-slate-300 mx-auto mb-3 stroke-1" />
              <h4 className="text-base font-semibold text-slate-800">
                You have no active book loans
              </h4>
              <p className="text-sm text-slate-500 max-w-sm mx-auto mt-1 mb-4">
                Browse our catalog to discover volumes ready for borrowing on open stacks.
              </p>
              {onBrowseCatalog && (
                <button
                  type="button"
                  onClick={onBrowseCatalog}
                  className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition-colors cursor-pointer"
                >
                  <BookOpen className="w-4 h-4" />
                  <span>Browse Catalog</span>
                </button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3">
              {activeLoans.map((loan) => {
                const relativeDue = formatDueRelative(loan.due_date, loan.is_overdue);
                const isRowReturning = returningLoanId === loan.id;

                return (
                  <div
                    key={loan.id}
                    className={`bg-white rounded-xl border p-4 sm:p-5 shadow-xs transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                      loan.is_overdue
                        ? 'border-rose-300 bg-rose-50/20'
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    {/* Left: Book Thumbnail & Details */}
                    <div className="flex items-start sm:items-center space-x-4 flex-1">
                      {loan.cover_image_url ? (
                        <img
                          src={loan.cover_image_url}
                          alt={loan.book_title || 'Book cover'}
                          className="w-14 h-20 object-cover rounded-md border border-slate-200 shrink-0"
                        />
                      ) : (
                        <div className="w-14 h-20 bg-slate-100 rounded-md border border-slate-200 flex items-center justify-center text-slate-400 shrink-0">
                          <BookOpen className="w-6 h-6 stroke-1" />
                        </div>
                      )}

                      <div className="space-y-1 flex-1 min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <h4 className="font-bold text-slate-900 text-sm sm:text-base leading-snug line-clamp-1">
                            {loan.book_title || `Book #${loan.book_id}`}
                          </h4>
                          <StatusBadge
                            status={loan.is_overdue ? 'OVERDUE' : 'CHECKED_OUT'}
                            isOverdue={loan.is_overdue}
                          />
                        </div>

                        {loan.book_author && (
                          <p className="text-xs text-slate-600 font-medium line-clamp-1">
                            by {loan.book_author}
                          </p>
                        )}

                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs pt-1">
                          <span
                            className={`flex items-center font-semibold ${
                              relativeDue.isPast ? 'text-rose-600' : 'text-slate-600'
                            }`}
                          >
                            <Calendar className="w-3.5 h-3.5 mr-1 text-slate-400" />
                            {relativeDue.text}
                          </span>
                          <span className="text-slate-400">
                            Borrowed: {new Date(loan.borrowed_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Right: 1-Click Return Action */}
                    <div className="sm:self-center shrink-0">
                      <button
                        type="button"
                        disabled={isRowReturning}
                        onClick={() => handleReturn(loan.id, loan.book_title)}
                        className="w-full sm:w-auto inline-flex items-center justify-center space-x-1.5 px-4 py-2 rounded-lg text-xs font-semibold bg-amber-600 hover:bg-amber-700 text-white shadow-xs transition-colors cursor-pointer disabled:opacity-70 disabled:cursor-not-allowed"
                        title="Drop off book into reverse logistics intake queue"
                      >
                        {isRowReturning ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            <span>Processing Return...</span>
                          </>
                        ) : (
                          <>
                            <PackageCheck className="w-4 h-4" />
                            <span>Return to Intake Desk</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Past Loan History Accordion */}
      {!isLoading && !isError && pastLoans.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
          <button
            type="button"
            onClick={() => setShowHistory((prev) => !prev)}
            className="w-full px-5 py-4 flex items-center justify-between text-left hover:bg-slate-50 transition-colors focus:outline-none"
          >
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span className="text-sm font-bold text-slate-800">
                Returned Loan History ({pastLoans.length})
              </span>
            </div>
            {showHistory ? (
              <ChevronUp className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            )}
          </button>

          {showHistory && (
            <div className="border-t border-slate-100 divide-y divide-slate-100">
              {pastLoans.map((loan) => (
                <div
                  key={loan.id}
                  className="px-5 py-3.5 flex flex-col sm:flex-row sm:items-center justify-between text-xs gap-2 hover:bg-slate-50/50"
                >
                  <div>
                    <span className="font-semibold text-slate-800">
                      {loan.book_title || `Book #${loan.book_id}`}
                    </span>
                    {loan.book_author && (
                      <span className="text-slate-500 ml-1">by {loan.book_author}</span>
                    )}
                  </div>
                  <div className="flex items-center space-x-4 text-slate-500">
                    <span>
                      Borrowed: {new Date(loan.borrowed_at).toLocaleDateString()}
                    </span>
                    <span>
                      Returned:{' '}
                      {loan.returned_at
                        ? new Date(loan.returned_at).toLocaleDateString()
                        : 'Completed'}
                    </span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-600">
                      RETURNED
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default MyLoansView;

