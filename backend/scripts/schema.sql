-- =============================================================================
-- Intelligent Library & Reverse Logistics Platform
-- Production Supabase PostgreSQL Schema with pgvector & HNSW Indexing
-- =============================================================================

-- 1. Vector Extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Custom Enumeration Types
DO $$ BEGIN
    CREATE TYPE book_status AS ENUM ('AVAILABLE', 'CHECKED_OUT', 'IN_PROCESSING');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('PATRON', 'LIBRARIAN');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 3. User Profiles Table (Linked to Supabase Auth)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT,
    role user_role NOT NULL DEFAULT 'PATRON',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Attach foreign key to Supabase auth.users if running in Supabase environment
DO $$ BEGIN
    ALTER TABLE profiles
    ADD CONSTRAINT fk_profiles_auth_users
    FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE;
EXCEPTION
    WHEN undefined_table THEN null;
    WHEN duplicate_object THEN null;
END $$;

-- 4. Books Table (Physical Inventory & Semantic Embeddings)
CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    isbn VARCHAR(32) UNIQUE,
    genre VARCHAR(100),
    publication_year INT,
    dewey_decimal VARCHAR(32),
    summary TEXT,
    cover_image_url TEXT,
    status book_status NOT NULL DEFAULT 'AVAILABLE',
    embedding vector(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for Catalog Filtering and Lookups
CREATE INDEX IF NOT EXISTS idx_books_title ON books (title);
CREATE INDEX IF NOT EXISTS idx_books_author ON books (author);
CREATE INDEX IF NOT EXISTS idx_books_genre ON books (genre);
CREATE INDEX IF NOT EXISTS idx_books_status ON books (status);

-- HNSW Vector Index (Cosine Distance for Fast Semantic Search)
CREATE INDEX IF NOT EXISTS books_embedding_idx ON books USING hnsw (embedding vector_cosine_ops);

-- 5. Loans Table (Circulation History)
CREATE TABLE IF NOT EXISTS loans (
    id SERIAL PRIMARY KEY,
    book_id INT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    borrowed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    due_date TIMESTAMPTZ NOT NULL,
    returned_at TIMESTAMPTZ,
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE'
);

-- Concurrency Safety: Partial unique index guaranteeing at most 1 active loan per physical book
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_active_loan_per_book ON loans (book_id) WHERE status = 'ACTIVE';

