import React, { useState, useEffect } from 'react';
import { Book, BookCreateInput } from '../../types';
import { useCreateBook, useUpdateBook } from '../../hooks/useBooks';
import { CANONICAL_GENRES } from '../catalog/BookFilters';
import { X, Loader2, BookOpen, AlertCircle, Pencil, Plus } from 'lucide-react';

export interface BookFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  bookToEdit?: Book | null;
}

interface FormState {
  title: string;
  author: string;
  isbn: string;
  genre: string;
  publication_year: string;
  dewey_decimal: string;
  summary: string;
  cover_image_url: string;
}

const INITIAL_STATE: FormState = {
  title: '',
  author: '',
  isbn: '',
  genre: '',
  publication_year: '',
  dewey_decimal: '',
  summary: '',
  cover_image_url: '',
};

export function BookFormModal({ isOpen, onClose, bookToEdit = null }: BookFormModalProps) {
  const [formState, setFormState] = useState<FormState>(INITIAL_STATE);
  const [isCustomGenre, setIsCustomGenre] = useState(false);
  const [customGenre, setCustomGenre] = useState('');
  const [errors, setErrors] = useState<{ title?: string; author?: string }>({});
  const [submitError, setSubmitError] = useState<string | null>(null);

  const createMutation = useCreateBook();
  const updateMutation = useUpdateBook();

  const isEditing = !!bookToEdit;
  const isPending = createMutation.isPending || updateMutation.isPending;

  // Synchronize form values when modal opens or target book changes
  useEffect(() => {
    if (isOpen) {
      if (bookToEdit) {
        setFormState({
          title: bookToEdit.title || '',
          author: bookToEdit.author || '',
          isbn: bookToEdit.isbn || '',
          genre: bookToEdit.genre || '',
          publication_year: bookToEdit.publication_year ? String(bookToEdit.publication_year) : '',
          dewey_decimal: bookToEdit.dewey_decimal || '',
          summary: bookToEdit.summary || '',
          cover_image_url: bookToEdit.cover_image_url || '',
        });
      } else {
        setFormState(INITIAL_STATE);
      }
      setIsCustomGenre(false);
      setCustomGenre('');
      setErrors({});
      setSubmitError(null);
    }
  }, [isOpen, bookToEdit]);

  // Handle ESC key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !isPending) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isPending, onClose]);

  if (!isOpen) return null;

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormState((prev) => ({ ...prev, [name]: value }));
    if (errors[name as keyof typeof errors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const handleGenreSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    if (val === '__CUSTOM__') {
      setIsCustomGenre(true);
      setFormState((prev) => ({ ...prev, genre: customGenre }));
    } else {
      setIsCustomGenre(false);
      setFormState((prev) => ({ ...prev, genre: val }));
    }
  };

  const handleCustomGenreChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setCustomGenre(val);
    setFormState((prev) => ({ ...prev, genre: val }));
  };

  const validate = (): boolean => {
    const newErrors: { title?: string; author?: string } = {};
    if (!formState.title.trim()) {
      newErrors.title = 'Book title is required';
    }
    if (!formState.author.trim()) {
      newErrors.author = 'Author name is required';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isPending || !validate()) return;

    setSubmitError(null);

    const payload: BookCreateInput = {
      title: formState.title.trim(),
      author: formState.author.trim(),
      isbn: formState.isbn.trim() || undefined,
      genre: formState.genre.trim() || undefined,
      publication_year: formState.publication_year
        ? parseInt(formState.publication_year, 10)
        : undefined,
      dewey_decimal: formState.dewey_decimal.trim() || undefined,
      summary: formState.summary.trim() || undefined,
      cover_image_url: formState.cover_image_url.trim() || undefined,
    };

    if (isEditing && bookToEdit) {
      updateMutation.mutate(
        { id: bookToEdit.id, data: payload },
        {
          onSuccess: () => {
            onClose();
          },
          onError: (err) => {
            setSubmitError(err.message || 'Failed to update book.');
          },
        }
      );
    } else {
      createMutation.mutate(payload, {
        onSuccess: () => {
          onClose();
        },
        onError: (err) => {
          setSubmitError(err.message || 'Failed to catalog book.');
        },
      });
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget && !isPending) {
          onClose();
        }
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-lg w-full overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
              {isEditing ? <Pencil className="w-5 h-5" /> : <Plus className="w-5 h-5" />}
            </div>
            <div>
              <h2 id="modal-title" className="text-base font-bold text-slate-900 leading-tight">
                {isEditing ? 'Edit Book Record' : 'Catalog New Book Volume'}
              </h2>
              <p className="text-xs text-slate-500 font-medium">
                {isEditing
                  ? `Updating catalog record #${bookToEdit?.id}`
                  : 'Add a physical inventory asset to the catalog'}
              </p>
            </div>
          </div>
          <button
            type="button"
            disabled={isPending}
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-300"
            title="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {submitError && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{submitError}</span>
            </div>
          )}

          {/* Title (Required) */}
          <div>
            <label htmlFor="title" className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
              Title <span className="text-rose-500">*</span>
            </label>
            <input
              id="title"
              name="title"
              type="text"
              value={formState.title}
              onChange={handleChange}
              placeholder="e.g. Designing Data-Intensive Applications"
              className={`w-full px-3 py-2 bg-slate-50 border rounded-lg text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 transition-all ${
                errors.title
                  ? 'border-rose-400 focus:ring-rose-500/20'
                  : 'border-slate-200 focus:ring-indigo-500/20 focus:border-indigo-500'
              }`}
            />
            {errors.title && <p className="text-xs text-rose-600 mt-1">{errors.title}</p>}
          </div>

          {/* Author (Required) */}
          <div>
            <label htmlFor="author" className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
              Author <span className="text-rose-500">*</span>
            </label>
            <input
              id="author"
              name="author"
              type="text"
              value={formState.author}
              onChange={handleChange}
              placeholder="e.g. Martin Kleppmann"
              className={`w-full px-3 py-2 bg-slate-50 border rounded-lg text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 transition-all ${
                errors.author
                  ? 'border-rose-400 focus:ring-rose-500/20'
                  : 'border-slate-200 focus:ring-indigo-500/20 focus:border-indigo-500'
              }`}
            />
            {errors.author && <p className="text-xs text-rose-600 mt-1">{errors.author}</p>}
          </div>

          {/* Grid row: ISBN & Genre */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label htmlFor="isbn" className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                ISBN
              </label>
              <input
                id="isbn"
                name="isbn"
                type="text"
                value={formState.isbn}
                onChange={handleChange}
                placeholder="978-1449373320"
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm font-mono text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
              />
            </div>

            <div>
              <label htmlFor="genre" className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                Category / Genre
              </label>
              <select
                id="genre"
                name="genre"
                value={isCustomGenre ? '__CUSTOM__' : formState.genre}
                onChange={handleGenreSelectChange}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 cursor-pointer transition-all"
              >
                <option value="">Select a Category / Genre</option>
                {formState.genre && !CANONICAL_GENRES.includes(formState.genre) && !isCustomGenre && (
                  <option value={formState.genre}>{formState.genre}</option>
                )}
                {CANONICAL_GENRES.map((g) => (
                  <option key={g} value={g}>
                    {g}
                  </option>
                ))}
                <option value="__CUSTOM__">+ Custom Category...</option>
              </select>
              {isCustomGenre && (
                <div className="mt-2">
                  <input
                    type="text"
                    value={customGenre}
                    onChange={handleCustomGenreChange}
                    placeholder="Type custom category name..."
                    className="w-full px-3 py-1.5 bg-white border border-indigo-300 rounded-lg text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
                    autoFocus
                  />
                </div>
              )}
            </div>
          </div>

          {/* Grid row: Publication Year & Dewey Decimal */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label htmlFor="publication_year" className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                Publication Year
              </label>
              <input
                id="publication_year"
                name="publication_year"
                type="number"
                min="1000"
                max="2100"
                value={formState.publication_year}
                onChange={handleChange}
                placeholder="2017"
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
              />
            </div>

            <div>
              <label htmlFor="dewey_decimal" className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                Dewey Decimal (DDC)
              </label>
              <input
                id="dewey_decimal"
                name="dewey_decimal"
                type="text"
                value={formState.dewey_decimal}
                onChange={handleChange}
                placeholder="005.74"
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm font-mono text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
              />
            </div>
          </div>

          {/* Cover Image URL */}
          <div>
            <label htmlFor="cover_image_url" className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
              Cover Image URL
            </label>
            <input
              id="cover_image_url"
              name="cover_image_url"
              type="url"
              value={formState.cover_image_url}
              onChange={handleChange}
              placeholder="https://images.example.com/cover.jpg"
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
            />
          </div>

          {/* Summary Textarea */}
          <div>
            <label htmlFor="summary" className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
              Summary / Notes
            </label>
            <textarea
              id="summary"
              name="summary"
              rows={3}
              value={formState.summary}
              onChange={handleChange}
              placeholder="Brief summary or description of the volume..."
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all resize-none"
            />
          </div>

          {/* Modal Footer Actions */}
          <div className="pt-3 border-t border-slate-100 flex items-center justify-end space-x-3">
            <button
              type="button"
              disabled={isPending}
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-800 hover:bg-slate-100 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isPending}
              className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-indigo-500 transition-all cursor-pointer disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isPending ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>{isEditing ? 'Saving...' : 'Cataloging...'}</span>
                </>
              ) : (
                <>
                  <BookOpen className="w-3.5 h-3.5" />
                  <span>{isEditing ? 'Update Record' : 'Catalog Volume'}</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default BookFormModal;

