import React, { useState, useEffect, useRef } from 'react';
import { Search, X, LayoutGrid, List, Sparkles } from 'lucide-react';

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
  isSemantic?: boolean;
  onToggleSemantic?: (val: boolean) => void;
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
  isSemantic = false,
  onToggleSemantic,
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
        {/* Left: Search input + AI Semantic Toggle */}
        <div className="flex items-center gap-2 flex-1 min-w-[260px]">
          <div className="relative flex-1">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              {isSemantic ? (
                <Sparkles className="w-4 h-4 text-indigo-500 animate-pulse" />
              ) : (
                <Search className="w-4 h-4 text-slate-400" />
              )}
            </div>
            <input
              type="text"
              value={inputValue}
              onChange={handleInputChange}
              placeholder={
                isSemantic
                  ? "Search by concept or problem (e.g. 'how to scale databases')..."
                  : "Search by title, author, or keywords..."
              }
              className={`w-full pl-9 pr-9 py-2 rounded-lg text-sm transition-all focus:outline-none ${
                isSemantic
                  ? 'bg-indigo-50/30 border border-indigo-200 text-indigo-950 placeholder-indigo-400/80 focus:bg-white focus:ring-2 focus:ring-indigo-500/25 focus:border-indigo-500'
                  : 'bg-slate-50 border border-slate-200 text-slate-900 placeholder-slate-400 focus:bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500'
              }`}
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

          {/* AI Semantic Toggle Button */}
          {onToggleSemantic && (
            <button
              type="button"
              onClick={() => onToggleSemantic(!isSemantic)}
              className={`inline-flex items-center space-x-1.5 px-3 py-2 rounded-lg text-xs font-semibold border transition-all cursor-pointer whitespace-nowrap shrink-0 ${
                isSemantic
                  ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white border-indigo-600 shadow-xs hover:from-indigo-700 hover:to-violet-700'
                  : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100 hover:text-slate-900'
              }`}
              title={
                isSemantic
                  ? 'Semantic search active: using pgvector cosine similarity'
                  : 'Switch to AI Semantic Vector Search'
              }
            >
              <Sparkles className={`w-3.5 h-3.5 ${isSemantic ? 'text-amber-300 fill-amber-300' : 'text-slate-400'}`} />
              <span>AI Semantic</span>
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

