import React, { useState, useEffect, useRef } from 'react';
import { Search, X, LayoutGrid, List } from 'lucide-react';

export interface BookFiltersProps {
  search: string;
  onSearchChange: (value: string) => void;
  selectedGenre: string;
  onGenreChange: (genre: string) => void;
  selectedStatus: string;
  onStatusChange: (status: string) => void;
  viewMode: 'grid' | 'table';
  onViewModeChange: (mode: 'grid' | 'table') => void;
  genres?: string[];
}

export const CANONICAL_GENRES = [
  'Algorithms & Data Structures',
  'Cloud Infrastructure',
  'Computer Networks',
  'Database Systems',
  'DevOps & Reliability',
  'Distributed Systems',
  'Machine Learning',
  'Microservices & Cloud',
  'Operating Systems',
  'Programming Languages',
  'Software Architecture',
  'Software Engineering',
  'System Design',
];

export function BookFilters({
  search,
  onSearchChange,
  selectedGenre,
  onGenreChange,
  selectedStatus,
  onStatusChange,
  viewMode,
  onViewModeChange,
  genres = CANONICAL_GENRES,
}: BookFiltersProps) {
  // Local state for immediate typing feedback
  const [inputValue, setInputValue] = useState(search);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Sync external search prop changes back to local input without triggering race conditions
  useEffect(() => {
    setInputValue(search);
  }, [search]);

  // Clean up timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const nextVal = e.target.value;
    setInputValue(nextVal);

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Debounce propagation to parent query hook by 300ms
    debounceTimerRef.current = setTimeout(() => {
      onSearchChange(nextVal);
    }, 300);
  };

  const handleClearSearch = () => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    setInputValue('');
    onSearchChange('');
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-3 sm:p-4 shadow-xs mb-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        {/* Left: Search input */}
        <div className="relative flex-1 min-w-[220px]">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="w-4 h-4 text-slate-400" />
          </div>
          <input
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            placeholder="Search by title, author, or keywords..."
            className="w-full pl-9 pr-9 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
          />
          {inputValue && (
            <button
              type="button"
              onClick={handleClearSearch}
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 focus:outline-none"
              title="Clear search"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Right: Dropdown Filters & View Mode */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Genre Dropdown */}
          <select
            value={selectedGenre}
            onChange={(e) => onGenreChange(e.target.value)}
            className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs sm:text-sm font-medium text-slate-700 hover:border-slate-300 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 cursor-pointer transition-colors"
          >
            <option value="">All Genres</option>
            {genres.map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>

          {/* Status Dropdown */}
          <select
            value={selectedStatus}
            onChange={(e) => onStatusChange(e.target.value)}
            className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs sm:text-sm font-medium text-slate-700 hover:border-slate-300 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 cursor-pointer transition-colors"
          >
            <option value="">All Statuses</option>
            <option value="AVAILABLE">AVAILABLE (On Stack)</option>
            <option value="CHECKED_OUT">CHECKED OUT (On Loan)</option>
            <option value="IN_PROCESSING">IN PROCESSING (Intake)</option>
          </select>

          {/* View Mode Toggle (Grid vs Table) */}
          <div
            role="group"
            aria-label="View Mode Toggle"
            className="bg-slate-100 p-1 rounded-lg border border-slate-200 inline-flex items-center"
          >
            <button
              type="button"
              onClick={() => onViewModeChange('grid')}
              className={`p-1.5 rounded-md text-xs transition-all focus:outline-none ${
                viewMode === 'grid'
                  ? 'bg-white text-slate-900 shadow-xs font-semibold'
                  : 'text-slate-500 hover:text-slate-900'
              }`}
              title="Grid View"
              aria-label="Grid View"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => onViewModeChange('table')}
              className={`p-1.5 rounded-md text-xs transition-all focus:outline-none ${
                viewMode === 'table'
                  ? 'bg-white text-slate-900 shadow-xs font-semibold'
                  : 'text-slate-500 hover:text-slate-900'
              }`}
              title="Table View"
              aria-label="Table View"
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default BookFilters;

