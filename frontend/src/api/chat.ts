import {apiUrl} from "./baseUrl"

export async function streamChat(message: string, signal: AbortSignal, onChunk: (text: string) => void) {
  const response = await fetch(apiUrl("/api/chat/stream"), {
    method: "POST",
    headers: {
        "Content-Type": "application/json",
        Accept: "text/plain",
    },
    body: JSON.stringify({message}),
    signal,
  })

  if (!response.ok ){
    throw new Error(`Chat request failed (HTTP ${response.status}).`);
  }

  if (!response.headers.get("content-type")?.includes("text/plain")) {
    throw new Error("The server returned an unexpected response format.");
  }

  if (!response.body) {
    throw new Error("The server did not provide a response stream.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  let receivedText = false;

  function emit(text: string) {
    if (!text) return;
    if (text.trim()) receivedText = true;
    onChunk(text);
  }

  try {
    while (true) {
      signal.throwIfAborted();

      const { done, value } = await reader.read();
      signal.throwIfAborted();

      if (done) break;
      emit(decoder.decode(value, { stream: true }));
    }

    emit(decoder.decode());

    if (!receivedText) {
      throw new Error("The assistant returned an empty response. Please retry.");
    }
  } finally {
    reader.releaseLock();
  }
}
