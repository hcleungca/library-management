import React, { useState } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { useRole } from './context/RoleContext';
import { useIntakeQueue } from './hooks/useCirculation';
import { Navbar } from './components/Navbar';
import { BookCatalogView } from './components/catalog/BookCatalogView';
import { BookDetailPage } from './components/catalog/BookDetailPage';
import { MyLoansView } from './components/circulation/MyLoansView';
import { TriageDeskView } from './components/logistics/TriageDeskView';
import { BookFormModal } from './components/modals/BookFormModal';
import { LibrarianChatWidget } from './components/ai/LibrarianChatWidget';
import { LoginPage } from './components/auth/LoginPage';
import { AuthCallback } from './components/auth/AuthCallback';
import { Book } from './types';

export default function App() {
  const { isLibrarian, isAuthenticated } = useRole();
  const navigate = useNavigate();
  const [isAddBookModalOpen, setIsAddBookModalOpen] = useState(false);
  const [bookToEdit, setBookToEdit] = useState<Book | null>(null);

  // Fetch intake queue for live badge counter in navbar (only if librarian)
  const { data: intakeQueue = [] } = useIntakeQueue({ enabled: isLibrarian && isAuthenticated });

  const handleOpenAddBook = () => {
    setBookToEdit(null);
    setIsAddBookModalOpen(true);
  };

  const handleEditBook = (book: Book) => {
    setBookToEdit(book);
    setIsAddBookModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsAddBookModalOpen(false);
    setBookToEdit(null);
  };

  // Unauthenticated Barrier: Redirect unauthenticated traffic to /login (except /auth/callback)
  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/auth/callback" element={<AuthCallback />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      {/* Top Application Navigation Bar */}
      <Navbar
        onOpenAddBookModal={handleOpenAddBook}
        intakeQueueCount={intakeQueue.length}
      />

      {/* Main Viewport Router */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
        <Routes>
          <Route path="/login" element={<Navigate to="/catalog" replace />} />
          <Route path="/" element={<Navigate to="/catalog" replace />} />
          <Route
            path="/catalog"
            element={<BookCatalogView onEditBook={handleEditBook} />}
          />
          <Route
            path="/books/:id"
            element={<BookDetailPage onEditBook={handleEditBook} />}
          />
          <Route
            path="/my-loans"
            element={!isLibrarian ? <MyLoansView onBrowseCatalog={() => navigate('/catalog')} /> : <Navigate to="/catalog" replace />}
          />
          <Route
            path="/intake"
            element={isLibrarian ? <TriageDeskView /> : <Navigate to="/catalog" replace />}
          />
          <Route path="*" element={<Navigate to="/catalog" replace />} />
        </Routes>
      </main>

      {/* Global Add / Edit Book Modal Dialog (Staff Only) */}
      <BookFormModal
        isOpen={isAddBookModalOpen}
        onClose={handleCloseModal}
        bookToEdit={bookToEdit}
      />

      {/* Autonomous AI Librarian Floating Chat Assistant (Patrons only) */}
      {!isLibrarian && <LibrarianChatWidget />}
    </div>
  );
}
