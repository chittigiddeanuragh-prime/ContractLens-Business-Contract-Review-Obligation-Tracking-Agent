import React, { useState, useEffect, useRef } from 'react';
import { ChatMessage, QAMessageItem } from './ChatMessage';

interface ChatPanelProps {
  contractId: string;
  versionId: string;
  onHighlightQuote?: (start: number, end: number, page: number) => void;
  onHighlightCitation?: (start: number, end: number, page: number) => void;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  contractId,
  versionId,
  onHighlightQuote,
  onHighlightCitation,
}) => {
  const triggerHighlight = onHighlightCitation || onHighlightQuote || (() => {});
  const [messages, setMessages] = useState<QAMessageItem[]>([]);
  const [inputQuestion, setInputQuestion] = useState<string>('');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Fetch suggested questions for version
    fetch(`/api/v1/contracts/${contractId}/versions/${versionId}/qa/suggested-questions`)
      .then((res) => res.json())
      .then((data) => {
        if (data.suggested_questions) {
          setSuggestedQuestions(data.suggested_questions);
        }
      })
      .catch((err) => console.error('Failed to fetch suggested questions:', err));
  }, [contractId, versionId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendQuestion = async (textToSend?: string) => {
    const text = (textToSend || inputQuestion).trim();
    if (!text || isLoading) return;


    setInputQuestion('');

    const tempUserMsg: QAMessageItem = {
      id: 'temp-' + Date.now(),
      role: 'user',
      content: text,
    };

    setMessages((prev) => [...prev, tempUserMsg]);
    setIsLoading(true);

    try {
      const response = await fetch(`/api/v1/contracts/${contractId}/versions/${versionId}/qa/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: text,
          conversation_id: conversationId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to ask question');
      }

      const data = await response.json();
      setConversationId(data.conversation_id);

      const assistantMsg: QAMessageItem = {
        id: data.id,
        role: 'assistant',
        content: data.content,
        answer_status: data.answer_status,
        route: data.route,
        confidence: data.confidence,
        confidence_breakdown: data.confidence_breakdown,
        answer_payload: data.answer_payload,
        suggested_followups: data.suggested_followups,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: QAMessageItem = {
        id: 'err-' + Date.now(),
        role: 'assistant',
        content: `Error: ${err.message || 'Something went wrong.'}`,
        answer_status: 'unavailable',
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 dark:bg-slate-950 border-l border-slate-200 dark:border-slate-800">
      {/* Header */}
      <div className="p-4 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            💬 Grounded Contract Q&A
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Answers backed by code-verified contract citations.
          </p>
        </div>

        <button
          onClick={() => {
            setMessages([]);
            setConversationId(null);
          }}
          className="text-xs text-slate-500 hover:text-indigo-600 px-2 py-1 rounded border border-slate-200 dark:border-slate-800"
        >
          + New Chat
        </button>
      </div>

      {/* Messages list */}
      <div className="flex-1 p-4 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-6">
            <div className="text-4xl mb-3">🛡️</div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 mb-1">
              Ask Anything About This Contract
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-xs mb-4">
              Get precise answers with verified quotes and click-to-highlight PDF citations.
            </p>

            {suggestedQuestions.length > 0 && (
              <div className="w-full space-y-2">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                  Suggested Starter Questions
                </span>
                <div className="flex flex-col gap-2">
                  {suggestedQuestions.map((q, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendQuestion(q)}
                      className="p-2.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-indigo-500 text-xs text-left font-medium text-slate-700 dark:text-slate-300 transition-all shadow-sm hover:shadow"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          messages.map((msg) => (
            <ChatMessage
              key={msg.id}
              message={msg}
              onHighlightQuote={triggerHighlight}
              onSelectSuggestion={(s) => handleSendQuestion(s)}
            />
          ))
        )}

        {isLoading && (
          <div className="flex items-center gap-2 text-xs text-slate-400 p-3 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 w-fit animate-pulse mb-4">
            <span className="font-bold text-indigo-600">✨ Analyzing text & verifying citations...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="p-3 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendQuestion();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={inputQuestion}
            onChange={(e) => setInputQuestion(e.target.value)}
            placeholder="Ask a question about this contract..."
            maxLength={1000}
            className="flex-1 bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <button
            type="submit"
            disabled={!inputQuestion.trim() || isLoading}
            className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow transition-colors disabled:opacity-50"
          >
            Send
          </button>

        </form>
        <div className="flex justify-between items-center text-[10px] text-slate-400 mt-1.5 px-1">
          <span>Press Enter to send</span>
          <span>{inputQuestion.length} / 1000</span>
        </div>
      </div>
    </div>
  );
};
