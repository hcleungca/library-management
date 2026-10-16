import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Book } from '../../types';
import { useRole } from '../../context/RoleContext';
import { StatusBadge } from '../StatusBadge';
import { BookOpen, Pencil, Trash2, Loader2, Bookmark, Calendar, Sparkles } from 'lucide-react';

export interface BookCardProps {
  book: Book;
  onBorrow?: (book: Book) => void;
  onEdit?: (book: Book) => void;
  onDelete?: (book: Book) => void;
  isBorrowing?: boolean;
  isDeleting?: boolean;
}

export function BookCard({
  book,
  onBorrow,
  onEdit,
  onDelete,
  isBorrowing = false,
  isDeleting = false,
}: BookCardProps) {
  const { isLibrarian } = useRole();
  const [imgError, setImgError] = useState(false);

  const handleBorrow = () => {
    if (isBorrowing || book.status !== 'AVAILABLE') return;
    onBorrow?.(book);
  };

  const handleDelete = () => {
    if (isDeleting || book.status === 'CHECKED_OUT') return;
    onDelete?.(book);
  };

  const isAvailable = book.status === 'AVAILABLE';

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs hover:shadow-md transition-shadow flex flex-col h-full">
      {/* Clickable Link to Book Details */}
      <Link to={`/books/${book.id}`} className="flex-1 flex flex-col group cursor-pointer focus:outline-none">
        {/* Top: Cover Thumbnail / Fallback Banner */}
        <div className="relative h-44 bg-slate-100 flex items-center justify-center overflow-hidden border-b border-slate-100 group-hover:opacity-95 transition-opacity">
          {book.cover_image_url && !imgError ? (
            <img
              src={book.cover_image_url}
              alt={book.title}
              onError={() => setImgError(true)}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="flex flex-col items-center justify-center text-slate-400 p-4 text-center">
              <BookOpen className="w-12 h-12 text-slate-300 mb-1 stroke-1" />
              <span className="text-[11px] font-medium tracking-tight text-slate-400 uppercase">
                No Cover Available
              </span>
            </div>
          )}

          {/* Top-Right Status Badge Overlay */}
          <div className="absolute top-2.5 right-2.5">
            <StatusBadge status={book.status} />
          </div>

          {/* Top-Left AI Similarity Match Badge */}
          {book.similarity_score !== undefined && (
            <div className="absolute top-2.5 left-2.5 bg-indigo-600/95 backdrop-blur-xs text-white text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center space-x-1 shadow-sm border border-indigo-400/30">
              <Sparkles className="w-2.5 h-2.5 text-amber-300 fill-amber-300" />
              <span>{Math.round(book.similarity_score * 100)}% Match</span>
            </div>
          )}

          {/* Genre Pill on Cover */}
          {book.genre && (
            <div className="absolute bottom-2.5 left-2.5 bg-slate-900/80 backdrop-blur-xs text-white text-[10px] font-semibold px-2 py-0.5 rounded-full flex items-center space-x-1">
              <Bookmark className="w-2.5 h-2.5 text-indigo-300" />
              <span>{book.genre}</span>
            </div>
          )}
        </div>

        {/* Body: Metadata & Summary */}
        <div className="p-4 flex-1 flex flex-col">
          {/* Title & Author */}
          <h3 className="font-bold text-slate-900 text-base leading-snug line-clamp-1 group-hover:text-indigo-600 transition-colors" title={book.title}>
            {book.title}
          </h3>
          <p className="text-xs text-slate-600 font-medium mt-0.5 line-clamp-1">
            by <span className="text-slate-800">{book.author}</span>
          </p>

          {/* Metadata Badges (Dewey & Year) */}
          <div className="flex items-center space-x-2 text-[11px] text-slate-400 mt-2 font-mono">
            {book.dewey_decimal && (
              <span className="bg-slate-50 border border-slate-200 px-1.5 py-0.5 rounded text-slate-600">
                DDC {book.dewey_decimal}
              </span>
            )}
            {book.publication_year && (
              <span className="flex items-center text-slate-500">
                <Calendar className="w-3 h-3 mr-0.5" />
                {book.publication_year}
              </span>
            )}
          </div>

          {/* Two-Line Summary */}
          <p className="text-xs text-slate-500 mt-3 line-clamp-2 leading-relaxed flex-1">
            {book.summary || 'No description provided for this catalog volume.'}
          </p>

          {/* ISBN Footer Tag */}
          {book.isbn && (
            <p className="text-[10px] text-slate-400 font-mono mt-2">
              ISBN: {book.isbn}
            </p>
          )}
        </div>
      </Link>

      {/* Action Footer */}
      <div className="px-4 py-3 bg-slate-50/75 border-t border-slate-100 flex items-center justify-between gap-2">
        {isLibrarian ? (
          // Staff Actions: Edit and Delete
          <div className="flex items-center space-x-2 w-full">
            <button
              type="button"
              onClick={() => onEdit?.(book)}
              className="flex-1 inline-flex items-center justify-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 hover:text-slate-900 shadow-2xs transition-colors"
            >
              <Pencil className="w-3.5 h-3.5 text-slate-500" />
              <span>Edit</span>
            </button>
            <button
              type="button"
              disabled={isDeleting || book.status === 'CHECKED_OUT'}
              onClick={handleDelete}
              className={`inline-flex items-center justify-center p-1.5 rounded-lg text-xs font-semibold border transition-colors ${
                book.status === 'CHECKED_OUT'
                  ? 'border-slate-200 bg-slate-100 text-slate-300 cursor-not-allowed'
                  : 'border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100 hover:border-rose-300'
              }`}
              title={
                book.status === 'CHECKED_OUT'
                  ? 'Cannot delete book that is currently checked out'
                  : 'Delete book record'
              }
            >
              {isDeleting ? (
                <Loader2 className="w-4 h-4 animate-spin text-rose-600" />
              ) : (
                <Trash2 className="w-4 h-4" />
              )}
            </button>
          </div>
        ) : isAvailable ? (
          // Patron Action: Borrow Button (strictly available books only)
          <button
            type="button"
            disabled={isBorrowing}
            onClick={handleBorrow}
            className="w-full inline-flex items-center justify-center space-x-1.5 px-3 py-2 rounded-lg text-xs font-semibold shadow-2xs transition-all bg-indigo-600 hover:bg-indigo-700 text-white cursor-pointer active:scale-[0.99]"
          >
            {isBorrowing ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />
                <span>Borrowing...</span>
              </>
            ) : (
              <>
                <BookOpen className="w-3.5 h-3.5" />
                <span>Borrow Book</span>
              </>
            )}
          </button>
        ) : (
          // Book is unavailable (Checked Out / In Processing) - No borrow button
          <div className="w-full py-2 px-3 rounded-lg text-xs font-medium text-center bg-slate-100 text-slate-500 border border-slate-200 select-none">
            {book.status === 'CHECKED_OUT' ? (
              <span className="text-amber-800 font-semibold">Currently Checked Out</span>
            ) : (
              <span>Currently {book.status.replace('_', ' ')}</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default BookCard;

