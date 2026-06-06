import React, { useRef, useState } from "react";
import { askKhata } from "../api/client";
import MicButton from "./MicButton";

export default function AskPage() {
  const audioRef = useRef(null);
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [typedQuestion, setTypedQuestion] = useState("");
  const [error, setError] = useState("");

  async function askWithAudio(blob) {
    setLoading(true);
    setError("");
    try {
      const result = await askKhata(blob);
      setAnswer(result);
      playAnswer(result.audioUrl);
    } catch (err) {
      setError(err?.response?.data?.error || "Voice Ask failed.");
    } finally {
      setLoading(false);
    }
  }

  async function askWithText(event) {
    event.preventDefault();
    if (!typedQuestion.trim()) {
      return;
    }
    setLoading(true);
    setError("");
    try {
      const result = await askKhata(null, typedQuestion.trim());
      setAnswer(result);
      playAnswer(result.audioUrl);
    } catch (err) {
      setError(err?.response?.data?.error || "Ask failed.");
    } finally {
      setLoading(false);
    }
  }

  function playAnswer(audioUrl) {
    if (!audioUrl || !audioRef.current) {
      return;
    }
    audioRef.current.src = audioUrl;
    audioRef.current.play().catch(() => {});
  }

  return (
    <div className="kv-page">
      <section className="kv-hero">
        <p className="kv-eyebrow">Voice Ask</p>
        <h2>Apne khate se seedha poochho.</h2>
        <p>Ask in Hindi, Marathi, Gujarati, Tamil, or English. The answer stays merchant-local.</p>
      </section>

      <div className="kv-ask-panel">
        <MicButton disabled={loading} onRecording={askWithAudio} />
        <form className="kv-text-ask" onSubmit={askWithText}>
          <input
            placeholder="Demo fallback: type a question if Sarvam STT is not configured"
            value={typedQuestion}
            onChange={(event) => setTypedQuestion(event.target.value)}
          />
          <button disabled={loading} type="submit">
            Ask
          </button>
        </form>
      </div>

      {error ? <div className="kv-error">{error}</div> : null}
      {loading ? <div className="kv-note">Thinking through local khata...</div> : null}

      {answer ? (
        <section className="kv-card">
          <div className="kv-card-header">
            <h3>Answer</h3>
            <span>{answer.agent}</span>
          </div>
          <p className="kv-muted">Transcript: {answer.transcript || "Audio transcript unavailable"}</p>
          <p className="kv-answer">{answer.answerText}</p>
          <p className="kv-muted">Detected language: {answer.langDetected}</p>
        </section>
      ) : null}

      <audio ref={audioRef} />
    </div>
  );
}
