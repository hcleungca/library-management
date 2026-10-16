import React, { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useBook, useDeleteBook } from '../../hooks/useBooks';
import { useCheckoutBook } from '../../hooks/useCirculation';
import { useRole } from '../../context/RoleContext';
import { StatusBadge } from '../StatusBadge';
import { Book } from '../../types';
import {
  ArrowLeft,
  BookOpen,
  Pencil,
  Trash2,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Calendar,
  Bookmark,
  Hash,
  X,
  RotateCcw,
} from 'lucide-react';

export interface BookDetailPageProps {
  onEditBook?: (book: Book) => void;
}

interface ToastState {
  message: string;
  type: 'success' | 'error';
}

export function BookDetailPage({ onEditBook }: BookDetailPageProps) {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const bookId = Number(id);

  const { isLibrarian } = useRole();
  const { data: book, isLoading, isError, error, refetch } = useBook(bookId);

  const checkoutMutation = useCheckoutBook();
  const deleteMutation = useDeleteBook();

  const [imgError, setImgError] = useState(false);
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

  const isAvailable = book?.status === 'AVAILABLE';
  const isBorrowing = checkoutMutation.isPending;
  const isDeleting = deleteMutation.isPending;

  const handleBorrow = () => {
    if (!book || isBorrowing || !isAvailable) return;

    checkoutMutation.mutate(book.id, {
      onSuccess: () => {
        showToast(`Successfully checked out "${book.title}"! Due in 14 days.`, 'success');
      },
      onError: (err) => {
        showToast(
          err.message || `Unable to borrow "${book.title}". It may have already been checked out.`,
          'error'
        );
      },
    });
  };

  const handleDelete = () => {
    if (!book || isDeleting || book.status === 'CHECKED_OUT') return;

    if (window.confirm(`Are you sure you want to delete "${book.title}" from the catalog?`)) {
      deleteMutation.mutate(book.id, {
        onSuccess: () => {
          navigate('/catalog');
        },
        onError: (err) => {
          showToast(err.message || `Failed to delete "${book.title}".`, 'error');
        },
      });
    }
  };

  if (isLoading) {
    return (
      <div className="w-full max-w-5xl mx-auto space-y-6 animate-pulse">
        <div className="h-5 bg-slate-200 rounded w-36 mb-6" />
        <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-xs grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="h-96 bg-slate-200 rounded-xl" />
          <div className="md:col-span-2 space-y-4">
            <div className="h-8 bg-slate-200 rounded w-3/4" />
            <div className="h-4 bg-slate-200 rounded w-1/3" />
            <div className="h-6 bg-slate-100 rounded w-24" />
            <div className="space-y-2 pt-6">
              <div className="h-3 bg-slate-100 rounded w-full" />
              <div className="h-3 bg-slate-100 rounded w-full" />
              <div className="h-3 bg-slate-100 rounded w-4/5" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (isError || !book) {
    return (
      <div className="w-full max-w-xl mx-auto my-12 text-center bg-white border border-slate-200 rounded-2xl p-8 shadow-xs">
        <AlertCircle className="w-12 h-12 text-rose-500 mx-auto mb-3" />
        <h2 className="text-lg font-bold text-slate-900">Book Volume Not Found</h2>
        <p className="text-sm text-slate-500 mt-1 mb-6">
          {error?.message || `No catalog volume exists with ID #${id}.`}
        </p>
        <div className="flex items-center justify-center space-x-3">
          <button
            type="button"
            onClick={() => refetch()}
            className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Try Again</span>
          </button>
          <Link
            to="/catalog"
            className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Catalog</span>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-5xl mx-auto space-y-6">
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
              <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
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

      {/* Navigation Breadcrumb */}
      <div>
        <Link
          to="/catalog"
          className="inline-flex items-center space-x-1.5 text-xs font-semibold text-slate-500 hover:text-indigo-600 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Catalog</span>
        </Link>
      </div>

      {/* Main Detail Card */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 p-6 sm:p-8">
          {/* Left Column: Cover & Primary Action */}
          <div className="space-y-4">
            <div className="relative aspect-[3/4] bg-slate-100 rounded-xl overflow-hidden border border-slate-200 flex items-center justify-center shadow-inner">
              {book.cover_image_url && !imgError ? (
                <img
                  src={book.cover_image_url}
                  alt={book.title}
                  onError={() => setImgError(true)}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="flex flex-col items-center justify-center text-slate-400 p-6 text-center">
                  <BookOpen className="w-16 h-16 text-slate-300 mb-2 stroke-1" />
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    No Cover Available
                  </span>
                </div>
              )}
              <div className="absolute top-3 right-3">
                <StatusBadge status={book.status} />
              </div>
            </div>

            {/* Patron Borrow Button */}
            {!isLibrarian && (
              isAvailable ? (
                <button
                  type="button"
                  disabled={isBorrowing}
                  onClick={handleBorrow}
                  className="w-full py-3 px-4 rounded-xl text-sm font-bold flex items-center justify-center space-x-2 shadow-xs transition-all bg-indigo-600 hover:bg-indigo-700 text-white cursor-pointer active:scale-[0.99]"
                >
                  {isBorrowing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin text-white" />
                      <span>Processing Checkout...</span>
                    </>
                  ) : (
                    <>
                      <BookOpen className="w-4 h-4" />
                      <span>Borrow This Book (14 Days)</span>
                    </>
                  )}
                </button>
              ) : (
                <div className="w-full py-3 px-4 rounded-xl text-sm font-semibold text-center bg-slate-100 text-slate-500 border border-slate-200 select-none">
                  {book.status === 'CHECKED_OUT' ? (
                    <span className="text-amber-800">Currently Checked Out by a Patron</span>
                  ) : (
                    <span>Currently {book.status.replace('_', ' ')}</span>
                  )}
                </div>
              )
            )}

            {/* Staff Actions */}
            {isLibrarian && (
              <div className="flex items-center space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => onEditBook?.(book)}
                  className="flex-1 inline-flex items-center justify-center space-x-1.5 py-2.5 px-3 rounded-xl text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 hover:text-slate-900 shadow-2xs transition-colors"
                >
                  <Pencil className="w-3.5 h-3.5 text-slate-500" />
                  <span>Edit Volume</span>
                </button>
                <button
                  type="button"
                  disabled={isDeleting || book.status === 'CHECKED_OUT'}
                  onClick={handleDelete}
                  className={`inline-flex items-center justify-center p-2.5 rounded-xl text-xs font-semibold border transition-colors ${
                    book.status === 'CHECKED_OUT'
                      ? 'border-slate-200 bg-slate-100 text-slate-300 cursor-not-allowed'
                      : 'border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100 hover:border-rose-300 cursor-pointer'
                  }`}
                  title={
                    book.status === 'CHECKED_OUT'
                      ? 'Cannot delete book that is currently checked out'
                      : 'Delete book from catalog'
                  }
                >
                  {isDeleting ? (
                    <Loader2 className="w-4 h-4 animate-spin text-rose-600" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                </button>
              </div>
            )}
          </div>

          {/* Right Column: Title, Classification, & Full Synopsis */}
          <div className="md:col-span-2 space-y-6">
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-2">
                {book.genre && (
                  <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
                    <Bookmark className="w-3 h-3 text-indigo-500" />
                    <span>{book.genre}</span>
                  </span>
                )}
              </div>

              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight leading-tight">
                {book.title}
              </h1>
              <p className="text-base text-slate-600 font-medium mt-1">
                by <span className="text-slate-900 font-semibold">{book.author}</span>
              </p>
            </div>

            {/* Classification & Metadata Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 p-4 bg-slate-50/80 rounded-xl border border-slate-200/80 text-xs">
              <div>
                <span className="text-slate-400 block font-medium">Dewey Call Number</span>
                <span className="font-mono font-bold text-slate-800 text-sm">
                  {book.dewey_decimal || 'Unclassified'}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block font-medium">ISBN</span>
                <span className="font-mono text-slate-800 font-semibold">
                  {book.isbn || 'None'}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block font-medium">Publication Year</span>
                <span className="text-slate-800 font-semibold flex items-center mt-0.5">
                  <Calendar className="w-3 h-3 mr-1 text-slate-400" />
                  {book.publication_year || 'Unknown'}
                </span>
              </div>
            </div>

            {/* Complete Full-Length Synopsis */}
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                Volume Synopsis & Description
              </h3>
              <div className="text-sm text-slate-700 leading-relaxed space-y-3 whitespace-pre-line bg-white border border-slate-100 rounded-xl p-4 shadow-2xs">
                {book.summary || 'No detailed description provided for this volume.'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default BookDetailPage;

