import { useEffect, useRef, useState } from "react";
import { streamChatEvents } from "../api/chatEvents";
import type { MapAction } from "../api/mapActions";
import type {
  ConversationContext,
  HistoryMessage,
  MapContext,
} from "../api/chatContext";
import type { DispatchResult } from "../map/dispatchMapActions";
import "./ExplorerAI.css";

type Props = {
  open: boolean;
  onClose: () => void;
  getMapContext: () => MapContext | null;
  beginChatRequest: () => number;
  onMapAction: (
    action: MapAction,
    responseRevision: number,
    signal: AbortSignal,
  ) => DispatchResult;
};

type Message = {
  id: number;
  role: "user" | "assistant";
  text: string;
  status?: "streaming" | "complete" | "stopped" | "error";
};

function collectCompletedHistory(messages: Message[]): HistoryMessage[] {
  const turns: HistoryMessage[][] = [];

  for (let index = 0; index + 1 < messages.length; index += 1) {
    const user = messages[index];
    const assistant = messages[index + 1];

    if (
      user.role !== "user" ||
      assistant.role !== "assistant" ||
      assistant.status !== "complete"
    ) {
      continue;
    }

    const userText = user.text.trim();
    const assistantText = assistant.text.trim();

    if (
      !userText ||
      !assistantText ||
      userText.length > 4000 ||
      assistantText.length > 4000
    ) {
      continue;
    }

    turns.push([
      { role: "user", content: userText },
      { role: "assistant", content: assistantText },
    ]);

    index += 1;
  }

  return turns.slice(-4).flat();
}

const SUGGESTIONS = [
  "Show theft records on E Main Street in 2024.",
  "Show me the five largest properties by lot size.",
];

export default function ExplorerAI({
  open,
  onClose,
  getMapContext,
  beginChatRequest,
  onMapAction,
}: Props) {
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const inputRef = useRef<HTMLTextAreaElement>(null);
  const historyRef = useRef<HTMLDivElement>(null);
  const requestRef = useRef<AbortController | null>(null);
  const nextId = useRef(1);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  useEffect(() => {
    const history = historyRef.current;
    if (open && history) history.scrollTop = history.scrollHeight;
  }, [open, messages, sending]);

  useEffect(() => {
    return () => {
      const controller = requestRef.current;
      requestRef.current = null;
      controller?.abort();
    };
  }, []);

  async function send() {
    const text = draft.trim();

    if (!text || text.length > 2000 || requestRef.current !== null) {
      return;
    }

    const mapContext = getMapContext();

    if (mapContext === null) {
      setError(
        "The map is not ready for a contextual question. " +
        "Wait for loading to finish. If loading failed, return to " +
        "neighborhood view or select another neighborhood.",
      );
      return;
    }

    const conversation: ConversationContext = {
      history: collectCompletedHistory(messages),
      map_context: mapContext,
    };

    const controller = new AbortController();
    requestRef.current = controller;
    const responseRevision = beginChatRequest();

    const userId = nextId.current++;
    const assistantId = nextId.current++;

    setMessages(current => [
      ...current,
      { id: userId, role: "user", text },
      {
        id: assistantId,
        role: "assistant",
        text: "",
        status: "streaming",
      },
    ]);

    setDraft("");
    setError(null);
    setSending(true);

    let timedOut = false;
    const timeout = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, 90_000);

    function updateAssistant(patch: Partial<Pick<Message, "text" | "status">>) {
      setMessages(current =>
        current.map(message =>
          message.id === assistantId ? { ...message, ...patch } : message,
        ),
      );
    }

    try {
      const completion = await streamChatEvents(
        text,
        controller.signal,
        chunk => {
          if (
            requestRef.current !== controller ||
            controller.signal.aborted
          ) {
            return;
          }

          setMessages(current =>
            current.map(message =>
              message.id === assistantId
                ? { ...message, text: message.text + chunk }
                : message,
            ),
          );
        },
        conversation,
      );

      if (
        requestRef.current !== controller ||
        controller.signal.aborted
      ) {
        return;
      }

      updateAssistant({ status: "complete" });

      if (completion.map_action !== null) {
        const dispatch = onMapAction(
          completion.map_action,
          responseRevision,
          controller.signal,
        );

        if (dispatch.status === "rejected") {
          setError(dispatch.message);
        } else if (dispatch.status === "ignored") {
          setError(
            dispatch.reason === "stale"
              ? "The map selection changed while this reply was loading. The street action was not applied."
              : dispatch.reason === "unavailable"
                ? "Street loading is not available."
                : "The street action was cancelled.",
          );
        }
      }
    } catch (cause: unknown) {
      if (requestRef.current !== controller) return;

      if (controller.signal.aborted && !timedOut) {
        updateAssistant({ status: "stopped" });
      } else {
        updateAssistant({ status: "error" });
        setError(
          timedOut
            ? "The request timed out after 90 seconds. Please try again."
            : cause instanceof Error
              ? cause.message
              : "Could not reach the assistant. Please try again.",
        );
      }

      // Restore the original question so it can be edited or submitted again.
      setDraft(text);
    } finally {
      clearTimeout(timeout);

      if (requestRef.current === controller) {
        requestRef.current = null;
        setSending(false);
      }
    }
  }

  return (
    <aside
      id="explorer-ai"
      className="explorer-ai"
      hidden={!open}
      aria-labelledby="explorer-ai-title"
      onKeyDown={event => {
        if (event.key === "Escape") {
          event.stopPropagation();
          onClose();
        }
      }}
    >
      <header className="explorer-ai-header">
        <div>
          <h2 id="explorer-ai-title">
            <span aria-hidden="true">✦</span> Explorer AI
          </h2>
          <p>Ask about Charlottesville property data</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Collapse Explorer AI"
        >
          ×
        </button>
      </header>

      <div ref={historyRef} className="explorer-ai-history">
        {messages.length === 0 && (
          <div className="explorer-ai-empty">
            <p>Try a property lookup:</p>
            <div className="explorer-ai-suggestions">
              {SUGGESTIONS.map(question => (
                <button
                  key={question}
                  type="button"
                  onClick={() => {
                    setDraft(question);
                    inputRef.current?.focus();
                  }}
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        <div
          role="log"
          aria-label="Conversation"
          aria-live="polite"
          aria-busy={sending}
        >
          {messages.map(message => (
            <article
              key={message.id}
              className={`explorer-ai-message is-${message.role}`}
            >
              <strong>
                {message.role === "user" ? "You" : "Explorer AI"}
              </strong>

              {message.text && <p>{message.text}</p>}

              {message.status === "streaming" && !message.text && (
                <p>Waiting for a response…</p>
              )}

              {message.status === "stopped" && (
                <small>
                  Response stopped. Any text above is incomplete.
                </small>
              )}

              {message.status === "error" && (
                <small>
                  Response failed. Any text above may be incomplete.
                </small>
              )}
            </article>
          ))}
        </div>

        {sending && <p role="status">Receiving assistant response…</p>}

        {error && (
          <div className="explorer-ai-error" role="alert">
            <p>{error}</p>
            <button type="button" onClick={() => setError(null)}>
              Dismiss
            </button>
          </div>
        )}
      </div>

      <form
        className="explorer-ai-composer"
        onSubmit={event => {
          event.preventDefault();
          void send();
        }}
      >
        <label htmlFor="explorer-ai-input">Your message</label>
        <textarea
          ref={inputRef}
          id="explorer-ai-input"
          rows={3}
          maxLength={2000}
          value={draft}
          readOnly={sending}
          aria-describedby="explorer-ai-input-help"
          placeholder="Ask about the largest properties…"
          onChange={event => setDraft(event.target.value)}
          onKeyDown={event => {
            if (
              event.key === "Enter" &&
              !event.shiftKey &&
              !event.nativeEvent.isComposing
            ) {
              event.preventDefault();
              void send();
            }
          }}
        />
        <p id="explorer-ai-input-help">
          Enter to send · Shift+Enter for a new line
        </p>
        <div className="explorer-ai-actions">
          {sending && (
            <button
              type="button"
              onClick={() => requestRef.current?.abort()}
            >
              Stop response
            </button>
          )}

          <button type="submit" disabled={sending || !draft.trim()}>
            {sending ? "Sending…" : "Send"}
          </button>
        </div>
      </form>
    </aside>
  );
}
