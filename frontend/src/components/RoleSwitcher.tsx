import React from 'react';
import { useRole } from '@/context/RoleContext';
import { User, ShieldCheck, Loader2 } from 'lucide-react';

export interface RoleSwitcherProps {
  className?: string;
}

export function RoleSwitcher({ className = '' }: RoleSwitcherProps) {
  const { role, setRole, isLoading } = useRole();

  const handleRoleChange = async (newRole: 'PATRON' | 'LIBRARIAN') => {
    if (newRole === role || isLoading) return;
    await setRole(newRole);
  };

  return (
    <div className={`inline-flex flex-col items-end ${className}`}>
      <div
        role="group"
        aria-label="Demo Role Switcher"
        className="bg-slate-100 p-1 rounded-full border border-slate-200 inline-flex items-center shadow-xs"
      >
        {/* Patron Option */}
        <button
          type="button"
          disabled={isLoading}
          onClick={() => handleRoleChange('PATRON')}
          className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-slate-400 ${
            role === 'PATRON'
              ? 'bg-white text-slate-900 shadow-xs font-semibold'
              : 'text-slate-500 hover:text-slate-900 font-medium'
          } ${isLoading ? 'opacity-70 cursor-not-allowed' : 'cursor-pointer'}`}
          title="Patron Mode: Borrow books and view personal loan history"
        >
          <User className="w-3.5 h-3.5 text-slate-500" />
          <span>Patron</span>
        </button>

        {/* Librarian Option */}
        <button
          type="button"
          disabled={isLoading}
          onClick={() => handleRoleChange('LIBRARIAN')}
          className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-slate-400 ${
            role === 'LIBRARIAN'
              ? 'bg-white text-indigo-900 shadow-xs font-semibold'
              : 'text-slate-500 hover:text-slate-900 font-medium'
          } ${isLoading ? 'opacity-70 cursor-not-allowed' : 'cursor-pointer'}`}
          title="Librarian Mode: Cataloging, book editing, and intake reverse logistics shelving"
        >
          {isLoading && role !== 'LIBRARIAN' ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-600" />
          ) : (
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" />
          )}
          <span>Librarian <span className="text-[10px] text-slate-400 font-normal">(Staff)</span></span>
        </button>
      </div>

      {/* Privileges Indicator Hint */}
      <span className="text-[10px] text-slate-400 font-medium mt-1 pr-1">
        {role === 'LIBRARIAN' ? 'Staff permissions active (Full CRUD & Shelving)' : 'Patron permissions active (Borrow & Return)'}
      </span>
    </div>
  );
}

export default RoleSwitcher;

