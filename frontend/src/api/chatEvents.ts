import { apiUrl } from "./baseUrl";
import type { ConversationContext } from "./chatContext";
import { parseMapAction, type MapAction } from "./mapActions";

export type ChatCompletion = {
  type: "complete";
  contract_version: 1;
  map_action: MapAction | null;
};

type ChatEvent =
  | { type: "text_delta"; text: string }
  | ChatCompletion
  | {
      type: "error";
      code: "agent_failed";
      message: string;
    };

const MAX_EVENT_LENGTH = 65_536;

function requireObject(value: unknown): Record<string, unknown> {
  if (
    typeof value !== "object" ||
    value === null ||
    Array.isArray(value)
  ) {
    throw new Error("Invalid chat event.");
  }

  return value as Record<string, unknown>;
}

function requireKeys(
  value: Record<string, unknown>,
  expected: readonly string[],
): void {
  if (
    Object.keys(value).length !== expected.length ||
    expected.some(
      key => !Object.prototype.hasOwnProperty.call(value, key),
    )
  ) {
    throw new Error("Unexpected chat event fields.");
  }
}

function parseEvent(line: string): ChatEvent {
  const event = requireObject(JSON.parse(line));

  switch (event.type) {
    case "text_delta":
      requireKeys(event, ["type", "text"]);

      if (typeof event.text !== "string") {
        throw new Error("Invalid assistant text.");
      }

      return {
        type: "text_delta",
        text: event.text,
      };

    case "complete":
      requireKeys(event, [
        "type",
        "contract_version",
        "map_action",
      ]);

      if (event.contract_version !== 1) {
        throw new Error("Unsupported chat contract version.");
      }

      return {
        type: "complete",
        contract_version: 1,
        map_action:
          event.map_action === null
            ? null
            : parseMapAction(event.map_action),
      };

    case "error":
      requireKeys(event, ["type", "code", "message"]);

      if (
        event.code !== "agent_failed" ||
        typeof event.message !== "string" ||
        !event.message.trim()
      ) {
        throw new Error("Invalid chat error event.");
      }

      return {
        type: "error",
        code: "agent_failed",
        message: event.message,
      };

    default:
      throw new Error("Unsupported chat event.");
  }
}

export async function streamChatEvents(
  message: string,
  signal: AbortSignal,
  onChunk: (text: string) => void,
  conversation: ConversationContext,
): Promise<ChatCompletion> {
  const response = await fetch(
    apiUrl("/api/chat/stream?response_format=ndjson"),
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/x-ndjson",
      },
      body: JSON.stringify({ message, conversation }),
      signal,
    },
  );

  if (!response.ok) {
    throw new Error(`Chat request failed (HTTP ${response.status}).`);
  }

  const contentType = response.headers
    .get("content-type")
    ?.split(";")[0]
    .trim()
    .toLowerCase();

  if (contentType !== "application/x-ndjson") {
    await response.body?.cancel();
    throw new Error("The server returned an unexpected response format.");
  }

  if (!response.body) {
    throw new Error("The server did not provide a response stream.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8", { fatal: true });

  let buffer = "";
  let completion: ChatCompletion | null = null;
  let receivedText = false;
  let reachedEnd = false;

  function consumeLine(line: string): void {
    if (line.length > MAX_EVENT_LENGTH) {
      throw new Error("Chat event exceeds the supported size.");
    }

    if (!line.trim()) return;

    if (completion !== null) {
      throw new Error("Unexpected data after chat completion.");
    }

    const event = parseEvent(line);

    if (event.type === "error") {
      throw new Error(event.message);
    }

    if (event.type === "complete") {
      completion = event;
      return;
    }

    if (event.text.trim()) receivedText = true;
    if (event.text) onChunk(event.text);
  }

  function consumeBuffer(): void {
    let newline = buffer.indexOf("\n");

    while (newline !== -1) {
      const line = buffer.slice(0, newline);
      buffer = buffer.slice(newline + 1);
      consumeLine(line);
      newline = buffer.indexOf("\n");
    }

    if (buffer.length > MAX_EVENT_LENGTH) {
      throw new Error("Chat event exceeds the supported size.");
    }
  }

  try {
    while (true) {
      signal.throwIfAborted();

      const { done, value } = await reader.read();
      signal.throwIfAborted();

      if (done) {
        reachedEnd = true;
        buffer += decoder.decode();
        consumeBuffer();
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      consumeBuffer();
    }

    // The server writes every event with a terminating newline.
    if (buffer.trim()) {
      throw new Error("The chat stream ended with an incomplete event.");
    }

    if (completion === null) {
      throw new Error("The assistant did not finish the response.");
    }

    if (!receivedText) {
      throw new Error("The assistant returned an empty response.");
    }

    signal.throwIfAborted();
    return completion;
  } finally {
    if (!reachedEnd) {
      try {
        await reader.cancel();
      } catch {
        // Preserve the original request or parsing error.
      }
    }

    reader.releaseLock();
  }
}