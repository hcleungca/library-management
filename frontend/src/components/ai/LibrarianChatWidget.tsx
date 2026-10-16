import React, { useState, useRef, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Sparkles,
  X,
  Send,
  Loader2,
  BookOpen,
  CheckCircle2,
  RotateCcw,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Bookmark,
  Calendar,
} from 'lucide-react';
import { apiFetch } from '../../lib/api';
import { useRole } from '../../context/RoleContext';
import {
  AgentChatRequest,
  AgentChatResponse,
  AgentMessage,
  InteractiveCardPayload,
  ToolExecutionRecord,
} from '../../types';
// Tokenize and format inline markdown: `code`, **bold**, *italic*
function formatInline(text: string, isUser = false): React.ReactNode[] {
  const parts = text.split(/(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g);
  return parts.map((part, idx) => {
    if (part.startsWith('`') && part.endsWith('`') && part.length > 2) {
      return (
        <code
          key={idx}
          className={`px-1 py-0.5 rounded font-mono text-[11px] ${
            isUser
              ? 'bg-indigo-700/80 text-white border border-indigo-500'
              : 'bg-slate-100 text-indigo-700 border border-slate-200'
          }`}
        >
          {part.slice(1, -1)}
        </code>
      );
    }
    if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
      return (
        <strong
          key={idx}
          className={`font-bold ${isUser ? 'text-white' : 'text-slate-900'}`}
        >
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith('*') && part.endsWith('*') && part.length > 2) {
      return (
        <em
          key={idx}
          className={`italic ${isUser ? 'text-indigo-100' : 'text-slate-700'}`}
        >
          {part.slice(1, -1)}
        </em>
      );
    }
    return part;
  });
}

type Chunk =
  | { type: 'heading'; level: number; text: string }
  | { type: 'bullet-list'; items: string[] }
  | { type: 'numbered-list'; items: string[] }
  | { type: 'paragraph'; lines: string[] };

function parseMarkdownBlocks(text: string): Chunk[] {
  const rawLines = text.split('\n');
  const chunks: Chunk[] = [];
  let currentParagraph: string[] = [];

  const flushParagraph = () => {
    if (currentParagraph.length > 0) {
      chunks.push({ type: 'paragraph', lines: [...currentParagraph] });
      currentParagraph = [];
    }
  };

  let i = 0;
  while (i < rawLines.length) {
    const line = rawLines[i];
    const trimmed = line.trim();

    if (!trimmed) {
      flushParagraph();
      i++;
      continue;
    }

    const headingMatch = trimmed.match(/^(#{1,6})\s+(.*)$/);
    if (headingMatch) {
      flushParagraph();
      chunks.push({
        type: 'heading',
        level: headingMatch[1].length,
        text: headingMatch[2],
      });
      i++;
      continue;
    }

    if (/^\*\*[^*]+\*\*$/.test(trimmed)) {
      flushParagraph();
      chunks.push({
        type: 'heading',
        level: 4,
        text: trimmed.slice(2, -2),
      });
      i++;
      continue;
    }

    if (/^[-*]\s+/.test(trimmed)) {
      flushParagraph();
      const items: string[] = [];
      while (i < rawLines.length && /^[-*]\s+/.test(rawLines[i].trim())) {
        items.push(rawLines[i].trim().replace(/^[-*]\s+/, ''));
        i++;
      }
      chunks.push({ type: 'bullet-list', items });
      continue;
    }

    if (/^\d+\.\s+/.test(trimmed)) {
      flushParagraph();
      const items: string[] = [];
      while (i < rawLines.length && /^\d+\.\s+/.test(rawLines[i].trim())) {
        items.push(rawLines[i].trim().replace(/^\d+\.\s+/, ''));
        i++;
      }
      chunks.push({ type: 'numbered-list', items });
      continue;
    }

    currentParagraph.push(line);
    i++;
  }

  flushParagraph();
  return chunks;
}

function ChatMessageContent({
  content,
  isUser = false,
}: {
  content: string;
  isUser?: boolean;
}) {
  if (isUser) {
    return <p className="whitespace-pre-wrap">{content}</p>;
  }

  const chunks = parseMarkdownBlocks(content);

  return (
    <div className="space-y-2 text-xs sm:text-sm leading-relaxed">
      {chunks.map((chunk, idx) => {
        switch (chunk.type) {
          case 'heading':
            return (
              <h5
                key={idx}
                className={`font-bold text-slate-900 tracking-tight ${
                  chunk.level <= 2
                    ? 'text-sm sm:text-base pt-1 pb-0.5 border-b border-slate-100'
                    : 'text-xs sm:text-sm pt-1'
                }`}
              >
                {formatInline(chunk.text, false)}
              </h5>
            );

          case 'bullet-list':
            return (
              <ul
                key={idx}
                className="space-y-1.5 my-1.5 pl-4 list-disc list-outside text-slate-700"
              >
                {chunk.items.map((item, itemIdx) => (
                  <li key={itemIdx} className="leading-snug">
                    {formatInline(item, false)}
                  </li>
                ))}
              </ul>
            );

          case 'numbered-list':
            return (
              <ol
                key={idx}
                className="space-y-1.5 my-1.5 pl-4 list-decimal list-outside text-slate-700"
              >
                {chunk.items.map((item, itemIdx) => (
                  <li key={itemIdx} className="leading-snug">
                    {formatInline(item, false)}
                  </li>
                ))}
              </ol>
            );

          case 'paragraph':
            return (
              <p key={idx} className="text-slate-800 leading-relaxed">
                {chunk.lines.map((line, lineIdx) => (
                  <React.Fragment key={lineIdx}>
                    {formatInline(line, false)}
                    {lineIdx < chunk.lines.length - 1 && <br />}
                  </React.Fragment>
                ))}
              </p>
            );

          default:
            return null;
        }
      })}
    </div>
  );
}

interface ChatTurn {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  tools_executed?: ToolExecutionRecord[];
  interactive_card?: InteractiveCardPayload | null;
  createdAt: Date;
}

const QUICK_PROMPTS = [
  'Recommend books on distributed systems',
  'What books do I have checked out?',
  'Find Database Internals and check availability',
];

export function LibrarianChatWidget() {
  const { role, isLibrarian } = useRole();
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatTurn[]>([]);
  const [expandedTools, setExpandedTools] = useState<Record<string, boolean>>({});
  const [pendingBorrowBookId, setPendingBorrowBookId] = useState<number | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  // Reset chat history when switching roles
  useEffect(() => {
    setMessages([]);
    setInput('');
  }, [role]);

  // Auto-scroll to bottom of message list on new messages
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  // Focus input on open
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [isOpen]);

  // Send message mutation to POST /api/ai/agent
  const chatMutation = useMutation<AgentChatResponse, Error, string>({
    mutationFn: async (userMessage: string) => {
      // Build conversation history with strict role alternation (merge adjacent turns of same role)
      const sanitizedHistory: AgentMessage[] = [];
      for (const m of messages) {
        if (!m.content?.trim()) continue;
        const last = sanitizedHistory[sanitizedHistory.length - 1];
        if (last && last.role === m.role) {
          last.content = `${last.content}\n\n${m.content}`;
        } else {
          sanitizedHistory.push({ role: m.role, content: m.content });
        }
      }

      const payload: AgentChatRequest = {
        message: userMessage,
        history: sanitizedHistory,
      };

      return apiFetch<AgentChatResponse>('/ai/agent', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    },
    onSuccess: (data) => {
      const assistantTurn: ChatTurn = {
        id: `turn-${Date.now()}-${Math.random()}`,
        role: 'assistant',
        content: data.reply,
        tools_executed: data.tools_executed,
        interactive_card: data.interactive_card,
        createdAt: new Date(),
      };
      setMessages((prev) => [...prev, assistantTurn]);

      // If the agent performed a checkout or updated circulation, sync app caches
      const didBorrow = data.tools_executed?.some((t) => t.tool_name === 'borrow_book');
      if (didBorrow) {
        queryClient.invalidateQueries({ queryKey: ['books'] });
        queryClient.invalidateQueries({ queryKey: ['loans'] });
        queryClient.invalidateQueries({ queryKey: ['intake'] });
      }
    },
    onError: (err) => {
      const errorTurn: ChatTurn = {
        id: `turn-err-${Date.now()}`,
        role: 'assistant',
        content: `Sorry, I encountered an issue: ${err.message || 'Failed to reach AI Librarian service.'}`,
        createdAt: new Date(),
      };
      setMessages((prev) => [...prev, errorTurn]);
    },
  });

  // Direct checkout mutation for Human-in-the-Loop confirmation card
  const borrowMutation = useMutation<any, Error, number>({
    mutationFn: async (bookId: number) => {
      setPendingBorrowBookId(bookId);
      return apiFetch('/circulation/checkout', {
        method: 'POST',
        body: JSON.stringify({ book_id: bookId }),
      });
    },
    onSuccess: (_data, bookId) => {
      queryClient.invalidateQueries({ queryKey: ['books'] });
      queryClient.invalidateQueries({ queryKey: ['loans'] });

      // Append confirmation receipt to chat stream
      const receiptTurn: ChatTurn = {
        id: `turn-receipt-${Date.now()}`,
        role: 'assistant',
        content: '✓ Checkout successfully confirmed! The book is now issued to your account for 14 days.',
        interactive_card: {
          type: 'LOAN_RECEIPT',
          book_id: bookId,
          due_date: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        },
        createdAt: new Date(),
      };
      setMessages((prev) => [...prev, receiptTurn]);
      setPendingBorrowBookId(null);
    },
    onError: (err) => {
      const errorTurn: ChatTurn = {
        id: `turn-borrow-err-${Date.now()}`,
        role: 'assistant',
        content: `Could not complete checkout: ${err.message || 'Book is no longer available.'}`,
        createdAt: new Date(),
      };
      setMessages((prev) => [...prev, errorTurn]);
      setPendingBorrowBookId(null);
    },
  });

  // Helper to record user action in conversation before running checkout
  const handleBorrowBook = (bookId: number, title?: string) => {
    if (borrowMutation.isPending) return;

    const displayTitle = title ? `"${title}"` : `book #${bookId}`;
    const userActionTurn: ChatTurn = {
      id: `turn-user-action-${Date.now()}`,
      role: 'user',
      content: `Confirm borrow for ${displayTitle}.`,
      createdAt: new Date(),
    };

    setMessages((prev) => [...prev, userActionTurn]);
    borrowMutation.mutate(bookId);
  };

  const handleSend = (textToSend?: string) => {
    const text = (textToSend ?? input).trim();
    if (!text || chatMutation.isPending) return;

    const userTurn: ChatTurn = {
      id: `turn-user-${Date.now()}`,
      role: 'user',
      content: text,
      createdAt: new Date(),
    };

    setMessages((prev) => [...prev, userTurn]);
    setInput('');
    chatMutation.mutate(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleTools = (turnId: string) => {
    setExpandedTools((prev) => ({
      ...prev,
      [turnId]: !prev[turnId],
    }));
  };

  const handleResetChat = () => {
    setMessages([]);
    setInput('');
  };

  // The AI Librarian assistant is exclusively for patrons
  if (isLibrarian) {
    return null;
  }

  return (
    <>
      {/* 1. Floating Launch Pill (Bottom-Right) */}
      {!isOpen && (
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 inline-flex items-center space-x-2.5 px-4 py-3 bg-gradient-to-r from-indigo-600 via-indigo-700 to-violet-700 hover:from-indigo-700 hover:to-violet-800 text-white font-semibold text-sm rounded-full shadow-lg hover:shadow-xl transition-all duration-200 cursor-pointer active:scale-95 group border border-white/20"
          aria-label="Open AI Librarian Chat"
        >
          <div className="relative">
            <Sparkles className="w-5 h-5 text-amber-300 fill-amber-300 animate-pulse" />
          </div>
          <span>Ask AI Librarian</span>
          <span className="bg-white/20 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full uppercase tracking-wider">
            Claude
          </span>
        </button>
      )}

      {/* 2. Chat Window Drawer */}
      {isOpen && (
        <div
          role="dialog"
          aria-label="AI Librarian Assistant Chat"
          className="fixed bottom-6 right-6 z-50 w-[420px] max-w-[94vw] h-[580px] max-h-[85vh] bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-200"
        >
          {/* Header */}
          <div className="px-4 py-3.5 bg-gradient-to-r from-indigo-900 via-slate-900 to-indigo-950 text-white flex items-center justify-between shadow-xs">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-amber-400 to-indigo-500 flex items-center justify-center shadow-xs">
                <Sparkles className="w-4 h-4 text-white fill-amber-300" />
              </div>
              <div>
                <h3 className="font-bold text-sm leading-tight flex items-center space-x-1.5">
                  <span>AI Librarian</span>
                  <span className="text-[10px] font-normal text-indigo-200 bg-white/10 px-1.5 py-0.5 rounded">
                    Claude Haiku
                  </span>
                </h3>
                <p className="text-[11px] text-slate-300">Natural language search & circulation assistant</p>
              </div>
            </div>

            <div className="flex items-center space-x-1">
              <button
                type="button"
                onClick={handleResetChat}
                className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors"
                title="Reset conversation"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors"
                title="Close chat"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Message Stream */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3.5 bg-slate-50/50">
            {/* Empty Welcome State */}
            {messages.length === 0 && (
              <div className="text-center py-6 px-3">
                <div className="w-12 h-12 mx-auto mb-3 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
                  <Sparkles className="w-6 h-6 text-indigo-600" />
                </div>
                <h4 className="font-bold text-slate-900 text-sm">Welcome to your AI Librarian!</h4>
                <p className="text-xs text-slate-500 max-w-xs mx-auto mt-1 leading-relaxed">
                  I can search the catalog using semantic vector concepts, check availability, and help you borrow books with your confirmation.
                </p>

                {/* Quick Starter Chips */}
                <div className="mt-5 space-y-2 text-left">
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider px-1">
                    Suggested inquiries:
                  </p>
                  {QUICK_PROMPTS.map((prompt) => (
                    <button
                      key={prompt}
                      type="button"
                      onClick={() => handleSend(prompt)}
                      className="w-full text-left text-xs bg-white hover:bg-indigo-50/70 hover:border-indigo-200 border border-slate-200 p-2.5 rounded-xl text-slate-700 transition-colors flex items-center justify-between group shadow-2xs"
                    >
                      <span className="line-clamp-1">{prompt}</span>
                      <Sparkles className="w-3.5 h-3.5 text-slate-300 group-hover:text-indigo-500 shrink-0 ml-1" />
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Conversation Messages */}
            {messages.map((turn) => (
              <div
                key={turn.id}
                className={`flex flex-col ${turn.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                {/* Bubble */}
                <div
                  className={`max-w-[88%] p-3.5 rounded-2xl text-xs sm:text-sm leading-relaxed shadow-2xs ${
                    turn.role === 'user'
                      ? 'bg-indigo-600 text-white rounded-br-xs'
                      : 'bg-white border border-slate-200 text-slate-800 rounded-bl-xs'
                  }`}
                >
                  <ChatMessageContent content={turn.content} isUser={turn.role === 'user'} />

                  {/* Tool Execution Transparency Badge */}
                  {turn.tools_executed && turn.tools_executed.length > 0 && (
                    <div className="mt-2.5 pt-2 border-t border-slate-100">
                      <button
                        type="button"
                        onClick={() => toggleTools(turn.id)}
                        className="inline-flex items-center space-x-1.5 text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 focus:outline-none"
                      >
                        <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-ping" />
                        <span>
                          {turn.tools_executed.length} tool{turn.tools_executed.length > 1 ? 's' : ''} executed
                        </span>
                        {expandedTools[turn.id] ? (
                          <ChevronUp className="w-3 h-3 text-indigo-400" />
                        ) : (
                          <ChevronDown className="w-3 h-3 text-indigo-400" />
                        )}
                      </button>

                      {expandedTools[turn.id] && (
                        <div className="mt-1.5 space-y-1 pl-1">
                          {turn.tools_executed.map((tool, idx) => (
                            <div
                              key={idx}
                              className="text-[10px] font-mono bg-slate-50 border border-slate-200 rounded p-1.5 text-slate-600"
                            >
                              <span className="font-bold text-indigo-600">{tool.tool_name}</span>
                              <div className="text-slate-400 truncate">
                                args: {JSON.stringify(tool.arguments)}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Interactive Card: CONFIRM_BORROW (Human-in-the-Loop) */}
                  {turn.interactive_card?.type === 'CONFIRM_BORROW' && (
                    <div className="mt-3 p-3 bg-indigo-50/70 border border-indigo-200 rounded-xl text-slate-800">
                      <div className="flex items-center space-x-2.5 mb-2.5">
                        <div className="w-8 h-10 bg-indigo-100 rounded flex items-center justify-center shrink-0">
                          <BookOpen className="w-4 h-4 text-indigo-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h5 className="font-bold text-xs text-slate-900 truncate">
                            {turn.interactive_card.title}
                          </h5>
                          {turn.interactive_card.author && (
                            <p className="text-[11px] text-slate-500 truncate">
                              by {turn.interactive_card.author}
                            </p>
                          )}
                          <span className="inline-block mt-0.5 text-[10px] font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.2 rounded">
                            Available on Stacks
                          </span>
                        </div>
                      </div>

                      <div className="mt-2">
                        {isLibrarian ? (
                          <div className="flex items-center space-x-1.5 px-2.5 py-1.5 bg-slate-100 border border-slate-200 rounded-lg text-slate-500 text-[11px]">
                            <AlertCircle className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                            <span>Staff Mode: Librarians cannot borrow books. Switch to Patron to check out.</span>
                          </div>
                        ) : (
                          <button
                            type="button"
                            disabled={borrowMutation.isPending}
                            onClick={() => {
                              if (turn.interactive_card?.book_id) {
                                handleBorrowBook(
                                  turn.interactive_card.book_id,
                                  turn.interactive_card.title
                                );
                              }
                            }}
                            className="w-full py-1.5 px-3 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-2xs transition-colors flex items-center justify-center space-x-1 cursor-pointer disabled:opacity-50"
                          >
                            {pendingBorrowBookId === turn.interactive_card.book_id ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            ) : (
                              <>
                                <CheckCircle2 className="w-3.5 h-3.5" />
                                <span>Confirm Borrow (14 Days)</span>
                              </>
                            )}
                          </button>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Interactive Card: BOOK_LIST (Multi-book discovery) */}
                  {turn.interactive_card?.type === 'BOOK_LIST' && turn.interactive_card.books && (
                    <div className="mt-3 space-y-2">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                        Discovered Volumes:
                      </p>
                      {turn.interactive_card.books.slice(0, 3).map((book) => {
                        const isAvailable = book.status === 'AVAILABLE';
                        return (
                          <div
                            key={book.id}
                            className="p-2.5 bg-white border border-slate-200 rounded-xl flex items-center justify-between gap-2 shadow-2xs"
                          >
                            <div className="min-w-0 flex-1">
                              <h5 className="font-bold text-xs text-slate-900 truncate" title={book.title}>
                                {book.title}
                              </h5>
                              <p className="text-[11px] text-slate-500 truncate">by {book.author}</p>
                              <div className="flex items-center space-x-1.5 mt-1">
                                <span
                                  className={`text-[9px] font-semibold px-1.5 py-0.2 rounded ${
                                    isAvailable
                                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                      : 'bg-slate-100 text-slate-500 border border-slate-200'
                                  }`}
                                >
                                  {isAvailable ? 'Available' : 'Checked Out'}
                                </span>
                                {book.similarity_score !== undefined && (
                                  <span className="text-[9px] font-semibold text-indigo-600 bg-indigo-50 border border-indigo-100 px-1 py-0.2 rounded">
                                    ✨ {Math.round(book.similarity_score * 100)}% Match
                                  </span>
                                )}
                              </div>
                            </div>

                            {isAvailable && !isLibrarian && (
                              <button
                                type="button"
                                disabled={borrowMutation.isPending}
                                onClick={() => handleBorrowBook(book.id, book.title)}
                                className="px-2.5 py-1 bg-indigo-50 hover:bg-indigo-600 text-indigo-700 hover:text-white border border-indigo-200 rounded-lg text-[11px] font-semibold transition-colors shrink-0 cursor-pointer disabled:opacity-50"
                              >
                                {pendingBorrowBookId === book.id ? (
                                  <Loader2 className="w-3 h-3 animate-spin" />
                                ) : (
                                  'Borrow'
                                )}
                              </button>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {/* Interactive Card: LOAN_RECEIPT (Receipt after borrowing) */}
                  {turn.interactive_card?.type === 'LOAN_RECEIPT' && (
                    <div className="mt-2.5 p-2.5 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center space-x-2 text-emerald-800 text-xs">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                      <div>
                        <span className="font-bold">Active Loan Issued:</span> Due on{' '}
                        {turn.interactive_card.due_date || '14 days'}.
                      </div>
                    </div>
                  )}

                  {/* Interactive Card: ACTIVE_LOANS (Patron loan overview) */}
                  {turn.interactive_card?.type === 'ACTIVE_LOANS' && turn.interactive_card.loans && (
                    <div className="mt-2.5 space-y-1.5">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                        Current Active Loans:
                      </p>
                      {turn.interactive_card.loans.map((loan) => (
                        <div
                          key={loan.loan_id}
                          className="p-2 bg-slate-50 border border-slate-200 rounded-lg text-xs flex items-center justify-between"
                        >
                          <div className="truncate mr-2">
                            <span className="font-semibold text-slate-800">{loan.title}</span>
                          </div>
                          <span
                            className={`text-[10px] font-semibold px-1.5 py-0.2 rounded shrink-0 ${
                              loan.is_overdue
                                ? 'bg-rose-100 text-rose-700'
                                : 'bg-slate-200 text-slate-700'
                            }`}
                          >
                            Due: {loan.due_date}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* In-Flight Thinking Indicator */}
            {chatMutation.isPending && (
              <div className="flex items-center space-x-2 p-3 bg-white border border-slate-200 rounded-2xl rounded-bl-xs text-xs text-slate-500 w-fit shadow-2xs">
                <Loader2 className="w-3.5 h-3.5 text-indigo-600 animate-spin" />
                <span>Claude Haiku is reasoning & searching...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Bar */}
          <div className="p-3 bg-white border-t border-slate-200">
            <div className="flex items-center space-x-2">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask for book recommendations or manage loans..."
                disabled={chatMutation.isPending}
                className="flex-1 px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all disabled:opacity-50"
              />
              <button
                type="button"
                onClick={() => handleSend()}
                disabled={!input.trim() || chatMutation.isPending}
                className="p-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-xs transition-colors disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer shrink-0"
                title="Send message"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default LibrarianChatWidget;

