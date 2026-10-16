import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import { Book, BookCreateInput, SemanticSearchResponse } from '../types';

export interface BookFilters {
  genre?: string;
  status?: string;
  search?: string;
  skip?: number;
  limit?: number;
}

export interface BookListResponse {
  items: Book[];
  total: number;
}

export type BookUpdateInput = Partial<BookCreateInput> & {
  status?: Book['status'];
};

export interface UpdateBookPayload {
  id: number;
  data: BookUpdateInput;
}

export interface SemanticSearchParams {
  query: string;
  limit?: number;
  available_only?: boolean;
  genre?: string;
  min_similarity?: number;
  enabled?: boolean;
}

function buildQueryString(params?: BookFilters): string {
  if (!params) return '';
  const searchParams = new URLSearchParams();

  if (params.genre && params.genre.trim()) {
    searchParams.set('genre', params.genre.trim());
  }
  if (params.status && params.status.trim()) {
    searchParams.set('status', params.status.trim());
  }
  if (params.search && params.search.trim()) {
    searchParams.set('search', params.search.trim());
  }
  if (params.skip !== undefined && params.skip >= 0) {
    searchParams.set('skip', String(params.skip));
  }
  if (params.limit !== undefined && params.limit > 0) {
    searchParams.set('limit', String(params.limit));
  }

  const qs = searchParams.toString();
  return qs ? `?${qs}` : '';
}

/**
 * Hook to retrieve and cache catalog books with filtering support.
 */
export function useBooks(filters?: BookFilters) {
  return useQuery<BookListResponse, Error>({
    queryKey: ['books', filters],
    queryFn: () => apiFetch<BookListResponse>(`/books${buildQueryString(filters)}`),
  });
}

/**
 * Hook to perform AI semantic vector search against catalog books using pgvector.
 */
export function useSemanticSearch(params: SemanticSearchParams) {
  const isEnabled = (params.enabled ?? true) && params.query.trim().length >= 2;

  return useQuery<SemanticSearchResponse, Error>({
    queryKey: [
      'books',
      'semantic-search',
      params.query.trim(),
      params.limit,
      params.available_only,
      params.genre,
      params.min_similarity,
    ],
    queryFn: () =>
      apiFetch<SemanticSearchResponse>('/books/search', {
        method: 'POST',
        body: JSON.stringify({
          query: params.query.trim(),
          limit: params.limit ?? 20,
          available_only: params.available_only ?? false,
          genre: params.genre || undefined,
          min_similarity: params.min_similarity ?? 0.2,
        }),
      }),
    enabled: isEnabled,
    staleTime: 1000 * 60 * 2, // 2 minutes cache
  });
}

/**
 * Hook to fetch a single book by ID.
 */
export function useBook(bookId: number) {
  return useQuery<Book, Error>({
    queryKey: ['book', bookId],
    queryFn: () => apiFetch<Book>(`/books/${bookId}`),
    enabled: !!bookId,
  });
}

/**
 * Mutation hook to catalog a new book asset (Librarian only).
 * Automatically invalidates catalog books queries on success.
 */
export function useCreateBook() {
  const queryClient = useQueryClient();

  return useMutation<Book, Error, BookCreateInput>({
    mutationFn: (newBook: BookCreateInput) =>
      apiFetch<Book>('/books', {
        method: 'POST',
        body: JSON.stringify(newBook),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['books'] });
    },
  });
}

/**
 * Mutation hook to update an existing book's metadata (Librarian only).
 * Automatically invalidates catalog books and the specific book queries on success.
 */
export function useUpdateBook() {
  const queryClient = useQueryClient();

  return useMutation<Book, Error, UpdateBookPayload>({
    mutationFn: ({ id, data }: UpdateBookPayload) =>
      apiFetch<Book>(`/books/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    onSuccess: (_updatedBook, variables) => {
      queryClient.invalidateQueries({ queryKey: ['books'] });
      queryClient.invalidateQueries({ queryKey: ['book', variables.id] });
    },
  });
}

/**
 * Mutation hook to delete a book from the catalog (Librarian only).
 * Automatically invalidates catalog books queries on success.
 */
export function useDeleteBook() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, number>({
    mutationFn: (bookId: number) =>
      apiFetch<void>(`/books/${bookId}`, {
        method: 'DELETE',
      }),
    onSuccess: (_data, bookId) => {
      queryClient.invalidateQueries({ queryKey: ['books'] });
      queryClient.removeQueries({ queryKey: ['book', bookId] });
    },
  });
}

