import { useQuery, useMutation, useQueryClient, QueryKey } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import { Book, Loan } from '../types';
import { BookListResponse } from './useBooks';

export interface CheckoutPayload {
  book_id: number;
  loan_duration_days?: number;
}

export type CheckoutInput = number | CheckoutPayload;

interface CheckoutContext {
  previousBooks: [QueryKey, BookListResponse | undefined][];
  previousBook?: Book;
  targetBookId: number;
}

/**
 * Hook to retrieve and cache the authenticated patron's loan history.
 */
export function useMyLoans(statusFilter?: 'ACTIVE' | 'RETURNED') {
  const queryParam = statusFilter ? `?status_filter=${statusFilter}` : '';
  return useQuery<Loan[], Error>({
    queryKey: ['loans', 'my-loans', statusFilter],
    queryFn: () => apiFetch<Loan[]>(`/circulation/my-loans${queryParam}`),
  });
}

/**
 * Mutation hook to check out an available book.
 * Optimistically transitions book status to 'CHECKED_OUT' in cache,
 * rolling back snapshot on conflict/error, and invalidating on settled.
 */
export function useCheckoutBook() {
  const queryClient = useQueryClient();

  return useMutation<Loan, Error, CheckoutInput, CheckoutContext>({
    mutationFn: (input: CheckoutInput) => {
      const payload: CheckoutPayload = typeof input === 'number' ? { book_id: input } : input;
      return apiFetch<Loan>('/circulation/checkout', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    },
    onMutate: async (input: CheckoutInput): Promise<CheckoutContext> => {
      const targetBookId = typeof input === 'number' ? input : input.book_id;

      // 1. Cancel in-flight queries for books to avoid overwriting optimistic update
      await queryClient.cancelQueries({ queryKey: ['books'] });

      // 2. Snapshot current books query cache
      const previousBooks = queryClient.getQueriesData<BookListResponse>({ queryKey: ['books'] });
      const previousBook = queryClient.getQueryData<Book>(['book', targetBookId]);

      // 3. Optimistically update all matching books queries
      queryClient.setQueriesData<BookListResponse>(
        { queryKey: ['books'] },
        (old) => {
          if (!old || !old.items) return old;
          return {
            ...old,
            items: old.items.map((b) =>
              b.id === targetBookId ? { ...b, status: 'CHECKED_OUT' as const } : b
            ),
          };
        }
      );

      if (previousBook) {
        queryClient.setQueryData<Book>(['book', targetBookId], {
          ...previousBook,
          status: 'CHECKED_OUT',
        });
      }

      return { previousBooks, previousBook, targetBookId };
    },
    onError: (_err, _input, context) => {
      // Rollback to prior snapshot on network error or 409 conflict
      if (context?.previousBooks) {
        context.previousBooks.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
      if (context?.previousBook) {
        queryClient.setQueryData(['book', context.targetBookId], context.previousBook);
      }
    },
    onSettled: () => {
      // Re-synchronize authoritative state from backend
      queryClient.invalidateQueries({ queryKey: ['books'] });
      queryClient.invalidateQueries({ queryKey: ['loans'] });
    },
  });
}

/**
 * Mutation hook to discharge an active loan.
 * Transitions book to IN_PROCESSING reverse logistics queue.
 */
export function useReturnBook() {
  const queryClient = useQueryClient();

  return useMutation<Loan, Error, number>({
    mutationFn: (loanId: number) =>
      apiFetch<Loan>(`/circulation/return/${loanId}`, {
        method: 'POST',
      }),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['books'] });
      queryClient.invalidateQueries({ queryKey: ['loans'] });
      queryClient.invalidateQueries({ queryKey: ['circulation', 'intake'] });
    },
  });
}

/**
 * Hook to retrieve books awaiting intake shelving (Librarian only).
 */
export function useIntakeQueue(options?: { enabled?: boolean }) {
  return useQuery<Book[], Error>({
    queryKey: ['circulation', 'intake'],
    queryFn: () => apiFetch<Book[]>('/circulation/intake'),
    enabled: options?.enabled ?? true,
  });
}

/**
 * Mutation hook to shelve a book from IN_PROCESSING back to AVAILABLE (Librarian only).
 */
export function useShelveBook() {
  const queryClient = useQueryClient();

  return useMutation<Book, Error, number>({
    mutationFn: (bookId: number) =>
      apiFetch<Book>(`/circulation/shelve/${bookId}`, {
        method: 'POST',
      }),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['books'] });
      queryClient.invalidateQueries({ queryKey: ['circulation', 'intake'] });
    },
  });
}

