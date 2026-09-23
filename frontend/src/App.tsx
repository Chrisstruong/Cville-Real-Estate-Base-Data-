import { useState } from "react"
import "./App.css"

function App() {
  const [message, setMessage] = useState("")
  const [response, setResponse] = useState("")
  const [isLoading, setIsLoading] = useState(false)


  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!message.trim()) {
      return;
    }

    console.log("User message: ", message)

    setResponse("");
    setIsLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/chat/stream", {
        method: "POST",
        headers: {
          "Content-type": "application/json",
        },
        body: JSON.stringify({
          message: message,
        }),
      });

      if (!res.ok) {
        throw new Error(`Request failed: ${res.status}`);
      }

      if (!res.body) {
        throw new Error("Response body is missing");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read()

        if (done) {
          break;
        }

        const chunk = decoder.decode(value, { stream: true });

        setResponse((previous) => previous + chunk)
      }
    } catch (error) {
      console.error(error);
      setResponse("Something went wrong while generating the response")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main>
      <h1> Charlottesville Real Estate AI</h1>

      <p>Ask questions about Charlottesville real estate properties</p>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Ask about a property..."
          disabled={isLoading}
        />

        <button type="submit" disabled={isLoading}>{isLoading ? "Generating..." : "Send"}</button>
      </form>
      <div>
        <h2>Response</h2>
        
        {isLoading && !response && <p>Thinking...</p>}

        {response && (
          <p style={{ whiteSpace: "pre-wrap"}}>
            {response}
          </p>
        )}
      </div>

    </main>
  );
}

export default App;