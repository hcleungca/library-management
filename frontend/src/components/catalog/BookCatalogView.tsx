import React, { useState, useRef, useEffect, useMemo } from 'react';
import { Book } from '../../types';
import { useBooks, useDeleteBook } from '../../hooks/useBooks';
import { useCheckoutBook } from '../../hooks/useCirculation';
import { BookFilters, CANONICAL_GENRES } from './BookFilters';
import { BookCard } from './BookCard';
import { BookTable } from './BookTable';
import { AlertCircle, CheckCircle2, RotateCcw, X, Inbox } from 'lucide-react';

export interface BookCatalogViewProps {
  onEditBook?: (book: Book) => void;
}

interface ToastState {
  message: string;
  type: 'success' | 'error';
}

export function BookCatalogView({ onEditBook }: BookCatalogViewProps) {
  const [search, setSearch] = useState('');
  const [selectedGenre, setSelectedGenre] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');
  const [selectedBookForEdit, setSelectedBookForEdit] = useState<Book | null>(null);

  // Toast notification state
  const [toast, setToast] = useState<ToastState | null>(null);
  const toastTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const showToast = (message: string, type: 'success' | 'error') => {
    if (toastTimeoutRef.current) {
      clearTimeout(toastTimeoutRef.current);
    }
    setToast({ message, type });
    toastTimeoutRef.current = setTimeout(() => {
      setToast(null);
    }, 4000);
  };

  useEffect(() => {
    return () => {
      if (toastTimeoutRef.current) {
        clearTimeout(toastTimeoutRef.current);
      }
    };
  }, []);

  // Books Query
  const {
    data: booksData,
    isLoading,
    isError,
    error,
    refetch,
  } = useBooks({
    search: search.trim() || undefined,
    genre: selectedGenre || undefined,
    status: selectedStatus || undefined,
  });

  // Mutations
  const checkoutMutation = useCheckoutBook();
  const deleteMutation = useDeleteBook();

  // Active book IDs in-flight to prevent race conditions & isolate spinners
  const borrowingBookId = checkoutMutation.isPending
    ? typeof checkoutMutation.variables === 'number'
      ? checkoutMutation.variables
      : checkoutMutation.variables?.book_id ?? null
    : null;

  const deletingBookId = deleteMutation.isPending ? deleteMutation.variables ?? null : null;

  const handleBorrow = (book: Book) => {
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

  const handleDelete = (book: Book) => {
    if (window.confirm(`Are you sure you want to delete "${book.title}" from the catalog?`)) {
      deleteMutation.mutate(book.id, {
        onSuccess: () => {
          showToast(`Deleted "${book.title}" from catalog.`, 'success');
        },
        onError: (err) => {
          showToast(err.message || `Failed to delete "${book.title}".`, 'error');
        },
      });
    }
  };

  const handleEdit = (book: Book) => {
    setSelectedBookForEdit(book);
    onEditBook?.(book);
  };

  const books = booksData?.items || [];
  const totalBooks = booksData?.total ?? books.length;

  // Dynamically merge canonical genres with any custom genres in books
  const allGenres = useMemo(() => {
    const genreSet = new Set(CANONICAL_GENRES);
    books.forEach((b) => {
      if (b.genre && b.genre.trim()) {
        genreSet.add(b.genre.trim());
      }
    });
    return Array.from(genreSet).sort();
  }, [books]);

  return (
    <div className="w-full">
      {/* Toast Notification Banner */}
      {toast && (
        <div
          role="alert"
          aria-live="polite"
          className={`mb-4 p-3.5 rounded-xl border flex items-center justify-between shadow-sm transition-all duration-200 ${
            toast.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
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
            className="text-slate-400 hover:text-slate-600 focus:outline-none p-1"
            title="Dismiss notification"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Catalog Filters Bar */}
      <BookFilters
        search={search}
        onSearchChange={setSearch}
        selectedGenre={selectedGenre}
        onGenreChange={setSelectedGenre}
        selectedStatus={selectedStatus}
        onStatusChange={setSelectedStatus}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        genres={allGenres}
      />

      {/* Results Header Summary */}
      <div className="flex items-center justify-between mb-4 px-1">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
          Catalog Inventory ({isLoading ? 'Loading...' : `${totalBooks} Volumes`})
        </p>
        {(search || selectedGenre || selectedStatus) && (
          <button
            type="button"
            onClick={() => {
              setSearch('');
              setSelectedGenre('');
              setSelectedStatus('');
            }}
            className="text-xs font-medium text-indigo-600 hover:text-indigo-800 transition-colors"
          >
            Clear active filters
          </button>
        )}
      </div>

      {/* Error State Banner */}
      {isError && (
        <div className="rounded-xl border border-rose-200 bg-rose-50/70 p-6 text-center my-6">
          <AlertCircle className="w-8 h-8 text-rose-500 mx-auto mb-2" />
          <h3 className="text-sm font-semibold text-rose-900">Failed to load catalog books</h3>
          <p className="text-xs text-rose-600 max-w-md mx-auto mt-1 mb-4">
            {error?.message || 'An error occurred while connecting to the catalog database.'}
          </p>
          <button
            type="button"
            onClick={() => refetch()}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-rose-600 hover:bg-rose-700 text-white shadow-xs transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Try Again</span>
          </button>
        </div>
      )}

      {/* Loading Skeleton */}
      {isLoading && (
        viewMode === 'grid' ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {Array.from({ length: 8 }).map((_, idx) => (
              <div
                key={idx}
                className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs animate-pulse flex flex-col h-80"
              >
                <div className="h-44 bg-slate-200" />
                <div className="p-4 flex-1 flex flex-col justify-between">
                  <div>
                    <div className="h-4 bg-slate-200 rounded w-3/4 mb-2" />
                    <div className="h-3 bg-slate-200 rounded w-1/2 mb-3" />
                    <div className="h-2.5 bg-slate-100 rounded w-full mb-1" />
                    <div className="h-2.5 bg-slate-100 rounded w-4/5" />
                  </div>
                  <div className="h-8 bg-slate-200 rounded w-full mt-4" />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs p-6 animate-pulse">
            <div className="space-y-4">
              {Array.from({ length: 6 }).map((_, idx) => (
                <div key={idx} className="h-8 bg-slate-100 rounded w-full" />
              ))}
            </div>
          </div>
        )
      )}

      {/* Loaded Views */}
      {!isLoading && !isError && (
        books.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 p-12 text-center bg-white my-4">
            <Inbox className="w-12 h-12 text-slate-300 mx-auto mb-3 stroke-1" />
            <h3 className="text-base font-semibold text-slate-800">
              No books found matching your criteria
            </h3>
            <p className="text-sm text-slate-400 max-w-sm mx-auto mt-1 mb-4">
              Try adjusting your search query, genre category, or inventory status filter.
            </p>
            <button
              type="button"
              onClick={() => {
                setSearch('');
                setSelectedGenre('');
                setSelectedStatus('');
              }}
              className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
            >
              <span>Reset all filters</span>
            </button>
          </div>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {books.map((book) => (
              <BookCard
                key={book.id}
                book={book}
                onBorrow={handleBorrow}
                onEdit={handleEdit}
                onDelete={handleDelete}
                isBorrowing={borrowingBookId === book.id}
                isDeleting={deletingBookId === book.id}
              />
            ))}
          </div>
        ) : (
          <BookTable
            books={books}
            onBorrow={handleBorrow}
            onEdit={handleEdit}
            onDelete={handleDelete}
            borrowingBookId={borrowingBookId}
            deletingBookId={deletingBookId}
          />
        )
      )}
    </div>
  );
}

export default BookCatalogView;

