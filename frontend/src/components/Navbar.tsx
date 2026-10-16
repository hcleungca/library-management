import React, { useEffect } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { useRole } from '../context/RoleContext';
import { BookOpen, BookMarked, Inbox, Plus, LogOut } from 'lucide-react';

export interface NavbarProps {
  onOpenAddBookModal?: () => void;
  intakeQueueCount?: number;
}

export function Navbar({ onOpenAddBookModal, intakeQueueCount = 0 }: NavbarProps) {
  const { isLibrarian, currentUser, logout } = useRole();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const pathname = location.pathname;

  // Guard: Role-based navigation redirects
  useEffect(() => {
    if (!isLibrarian && pathname === '/intake') {
      navigate('/catalog', { replace: true });
    } else if (isLibrarian && pathname === '/my-loans') {
      navigate('/catalog', { replace: true });
    }
  }, [isLibrarian, pathname, navigate]);

  const isCatalogActive = pathname === '/' || pathname.startsWith('/catalog') || pathname.startsWith('/books');
  const isLoansActive = pathname.startsWith('/my-loans');
  const isIntakeActive = pathname.startsWith('/intake');

  return (
    <header className="border-b border-slate-200 bg-white sticky top-0 z-30 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left: Branding & Navigation Tabs */}
          <div className="flex items-center space-x-8">
            {/* App Logo & Title */}
            <Link to="/catalog" className="flex items-center space-x-3 cursor-pointer">
              <span className="text-2xl" role="img" aria-label="Library Books">📚</span>
              <div>
                <h1 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight leading-none">
                  Intelligent Library
                </h1>
                <p className="text-[11px] text-slate-500 font-medium">
                  Reverse Logistics & Circulation
                </p>
              </div>
            </Link>

            {/* Navigation Tabs */}
            <nav className="hidden md:flex space-x-1" aria-label="Main Navigation">
              {/* Catalog Tab */}
              <Link
                to="/catalog"
                className={`flex items-center space-x-1.5 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isCatalogActive
                    ? 'bg-slate-100 text-slate-900 font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50 font-medium'
                }`}
              >
                <BookOpen className="w-4 h-4 text-slate-500" />
                <span>Catalog</span>
              </Link>

              {/* My Loans Tab (Patrons Only) */}
              {!isLibrarian && (
                <Link
                  to="/my-loans"
                  className={`flex items-center space-x-1.5 px-3 py-2 rounded-lg text-sm transition-colors ${
                    isLoansActive
                      ? 'bg-slate-100 text-slate-900 font-semibold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50 font-medium'
                  }`}
                >
                  <BookMarked className="w-4 h-4 text-slate-500" />
                  <span>My Loans</span>
                </Link>
              )}

              {/* Intake Shelving Desk (Staff/Librarian Only) */}
              {isLibrarian && (
                <Link
                  to="/intake"
                  className={`flex items-center space-x-1.5 px-3 py-2 rounded-lg text-sm transition-colors ${
                    isIntakeActive
                      ? 'bg-amber-50 text-amber-900 font-semibold border border-amber-200'
                      : 'text-slate-600 hover:text-amber-800 hover:bg-amber-50/50 font-medium'
                  }`}
                >
                  <Inbox className="w-4 h-4 text-amber-600" />
                  <span>Intake Shelving Desk</span>
                  {intakeQueueCount > 0 && (
                    <span className="ml-1 inline-flex items-center px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-amber-200 text-amber-800">
                      {intakeQueueCount}
                    </span>
                  )}
                </Link>
              )}
            </nav>
          </div>

          {/* Right: Actions & Role Switcher */}
          <div className="flex items-center space-x-3 sm:space-x-4">
            {/* Add Book Button (Staff Only) */}
            {isLibrarian && onOpenAddBookModal && (
              <button
                type="button"
                onClick={onOpenAddBookModal}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-2xs transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-indigo-500"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Book</span>
              </button>
            )}

            {/* User Profile Info & Sign Out */}
            <div className="flex items-center space-x-2.5 pl-2 border-l border-slate-200">
              <div className="hidden sm:flex flex-col items-end">
                <span className="text-xs font-bold text-slate-800 leading-tight">
                  {currentUser?.full_name || (isLibrarian ? 'Demo Librarian' : 'Demo Patron')}
                </span>
                <span
                  className={`text-[9px] font-bold px-1.5 py-0.2 rounded ${
                    isLibrarian
                      ? 'bg-amber-100 text-amber-800 border border-amber-200'
                      : currentUser?.email?.includes('gmail') || currentUser?.full_name?.includes('(SSO)')
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                  }`}
                >
                  {isLibrarian
                    ? 'Librarian (Staff)'
                    : currentUser?.email?.includes('gmail') || currentUser?.full_name?.includes('(SSO)')
                    ? 'SSO Patron'
                    : 'Demo Patron'}
                </span>
              </div>

              {/* Sign Out Button */}
              <button
                type="button"
                onClick={handleLogout}
                className="inline-flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:text-rose-600 hover:bg-rose-50 border border-slate-200 hover:border-rose-200 shadow-2xs transition-colors cursor-pointer"
                title="Sign out of your session"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span className="hidden md:inline">Sign Out</span>
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation Tabs */}
        <div className="flex md:hidden border-t border-slate-100 py-2 space-x-1 overflow-x-auto">
          <Link
            to="/catalog"
            className={`flex items-center space-x-1 px-3 py-1.5 rounded-md text-xs whitespace-nowrap ${
              isCatalogActive
                ? 'bg-slate-100 text-slate-900 font-semibold'
                : 'text-slate-600'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Catalog</span>
          </Link>

          {!isLibrarian && (
            <Link
              to="/my-loans"
              className={`flex items-center space-x-1 px-3 py-1.5 rounded-md text-xs whitespace-nowrap ${
                isLoansActive
                  ? 'bg-slate-100 text-slate-900 font-semibold'
                  : 'text-slate-600'
              }`}
            >
              <BookMarked className="w-3.5 h-3.5" />
              <span>My Loans</span>
            </Link>
          )}

          {isLibrarian && (
            <Link
              to="/intake"
              className={`flex items-center space-x-1 px-3 py-1.5 rounded-md text-xs whitespace-nowrap ${
                isIntakeActive
                  ? 'bg-amber-100 text-amber-900 font-semibold'
                  : 'text-slate-600'
              }`}
            >
              <Inbox className="w-3.5 h-3.5" />
              <span>Intake Desk</span>
              {intakeQueueCount > 0 && (
                <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-amber-200 text-amber-800">
                  {intakeQueueCount}
                </span>
              )}
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}

export default Navbar;
