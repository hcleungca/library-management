/**
 * Core domain type definitions for the Intelligent Library System.
 * Matches backend Pydantic models from Phase 2.
 */

export type BookStatus = 'AVAILABLE' | 'CHECKED_OUT' | 'IN_PROCESSING';
export type UserRole = 'PATRON' | 'LIBRARIAN';

export interface Book {
  id: number;
  title: string;
  author: string;
  isbn?: string | null;
  genre?: string | null;
  publication_year?: number | null;
  dewey_decimal?: string | null;
  summary?: string | null;
  cover_image_url?: string | null;
  status: BookStatus;
  similarity_score?: number;
  cosine_distance?: number;
  created_at: string;
  updated_at: string;
}

export interface SearchResultBook extends Book {
  similarity_score?: number;
  cosine_distance?: number;
}

export interface SemanticSearchResponse {
  query: string;
  results: SearchResultBook[];
  total_results: number;
}

export interface BookCreateInput {
  title: string;
  author: string;
  isbn?: string;
  genre?: string;
  publication_year?: number;
  dewey_decimal?: string;
  summary?: string;
  cover_image_url?: string;
}

export interface Loan {
  id: number;
  book_id: number;
  user_id: string;
  borrowed_at: string;
  due_date: string;
  returned_at?: string | null;
  status: 'ACTIVE' | 'RETURNED';
  is_overdue?: boolean;
  book_title?: string;
  book_author?: string;
  cover_image_url?: string | null;
  patron_email?: string | null;
}

export interface TokenUser {
  id: string;
  email: string;
  role: UserRole;
  full_name?: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: TokenUser;
}

