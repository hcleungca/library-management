import React from 'react';
import { Link } from 'react-router-dom';
import { Book } from '../../types';
import { useRole } from '../../context/RoleContext';
import { StatusBadge } from '../StatusBadge';
import { BookOpen, Pencil, Trash2, Loader2, Inbox, Sparkles } from 'lucide-react';

export interface BookTableProps {
  books: Book[];
  onBorrow?: (book: Book) => void;
  onEdit?: (book: Book) => void;
  onDelete?: (book: Book) => void;
  borrowingBookId?: number | null;
  deletingBookId?: number | null;
}

export function BookTable({
  books,
  onBorrow,
  onEdit,
  onDelete,
  borrowingBookId = null,
  deletingBookId = null,
}: BookTableProps) {
  const { isLibrarian } = useRole();

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50/75 text-[11px] font-bold uppercase tracking-wider text-slate-500">
              <th scope="col" className="py-3 px-4 sm:px-6">Title & Author</th>
              <th scope="col" className="py-3 px-3">ISBN</th>
              <th scope="col" className="py-3 px-3">Genre</th>
              <th scope="col" className="py-3 px-3">Dewey</th>
              <th scope="col" className="py-3 px-3">Year</th>
              <th scope="col" className="py-3 px-3">Status</th>
              <th scope="col" className="py-3 px-4 sm:px-6 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-sm">
            {books.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-12 px-4 text-center">
                  <div className="flex flex-col items-center justify-center text-slate-400">
                    <Inbox className="w-10 h-10 text-slate-300 mb-2 stroke-1" />
                    <p className="text-sm font-semibold text-slate-700">No books found</p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      No catalog records match your selected filters.
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              books.map((book) => {
                const isAvailable = book.status === 'AVAILABLE';
                const isRowBorrowing = borrowingBookId === book.id;
                const isRowDeleting = deletingBookId === book.id;

                return (
                  <tr
                    key={book.id}
                    className="hover:bg-slate-50/80 transition-colors group"
                  >
                    {/* 1. Title & Author */}
                    <td className="py-3.5 px-4 sm:px-6 max-w-xs">
                      <Link
                        to={`/books/${book.id}`}
                        className="font-semibold text-slate-900 hover:text-indigo-600 transition-colors truncate block"
                        title={book.title}
                      >
                        {book.title}
                      </Link>
                      <div className="text-xs text-slate-500 truncate" title={book.author}>
                        by {book.author}
                      </div>
                      {book.similarity_score !== undefined && (
                        <div className="mt-1">
                          <span className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
                            <Sparkles className="w-2.5 h-2.5 text-indigo-500 fill-indigo-200" />
                            <span>{Math.round(book.similarity_score * 100)}% Match</span>
                          </span>
                        </div>
                      )}
                    </td>

                    {/* 2. ISBN */}
                    <td className="py-3.5 px-3 text-xs font-mono text-slate-600 whitespace-nowrap">
                      {book.isbn || '—'}
                    </td>

                    {/* 3. Genre */}
                    <td className="py-3.5 px-3 whitespace-nowrap">
                      {book.genre ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
                          {book.genre}
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400">—</span>
                      )}
                    </td>

                    {/* 4. Dewey Decimal */}
                    <td className="py-3.5 px-3 text-xs font-mono text-slate-500 whitespace-nowrap">
                      {book.dewey_decimal || '—'}
                    </td>

                    {/* 5. Publication Year */}
                    <td className="py-3.5 px-3 text-xs text-slate-600 whitespace-nowrap">
                      {book.publication_year || '—'}
                    </td>

                    {/* 6. Status Badge */}
                    <td className="py-3.5 px-3 whitespace-nowrap">
                      <StatusBadge status={book.status} />
                    </td>

                    {/* 7. Actions */}
                    <td className="py-3.5 px-4 sm:px-6 text-right whitespace-nowrap">
                      {isLibrarian ? (
                        // Staff Actions
                        <div className="inline-flex items-center space-x-1.5">
                          <button
                            type="button"
                            onClick={() => onEdit?.(book)}
                            className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 hover:text-slate-900 shadow-2xs transition-colors"
                            title="Edit book metadata"
                          >
                            <Pencil className="w-3 h-3 text-slate-500" />
                            <span>Edit</span>
                          </button>
                          <button
                            type="button"
                            disabled={isRowDeleting || book.status === 'CHECKED_OUT'}
                            onClick={() => {
                              if (!isRowDeleting && book.status !== 'CHECKED_OUT') {
                                onDelete?.(book);
                              }
                            }}
                            className={`p-1 rounded-md text-xs border transition-colors ${
                              book.status === 'CHECKED_OUT'
                                ? 'border-slate-200 bg-slate-100 text-slate-300 cursor-not-allowed'
                                : 'border-rose-200 bg-rose-50 text-rose-600 hover:bg-rose-100 hover:border-rose-300 cursor-pointer'
                            }`}
                            title={
                              book.status === 'CHECKED_OUT'
                                ? 'Cannot delete book that is currently checked out'
                                : 'Delete book record'
                            }
                          >
                            {isRowDeleting ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin text-rose-600" />
                            ) : (
                              <Trash2 className="w-3.5 h-3.5" />
                            )}
                          </button>
                        </div>
                      ) : (
                        // Patron Action
                        <button
                          type="button"
                          disabled={!isAvailable || isRowBorrowing}
                          onClick={() => {
                            if (isAvailable && !isRowBorrowing) {
                              onBorrow?.(book);
                            }
                          }}
                          className={`inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold shadow-2xs transition-all ${
                            isAvailable
                              ? 'bg-indigo-600 hover:bg-indigo-700 text-white cursor-pointer active:scale-95'
                              : 'bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed'
                          }`}
                        >
                          {isRowBorrowing ? (
                            <>
                              <Loader2 className="w-3 h-3 animate-spin text-white" />
                              <span>Borrowing...</span>
                            </>
                          ) : (
                            <>
                              <BookOpen className="w-3 h-3" />
                              <span>{isAvailable ? 'Borrow' : 'Unavailable'}</span>
                            </>
                          )}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default BookTable;

