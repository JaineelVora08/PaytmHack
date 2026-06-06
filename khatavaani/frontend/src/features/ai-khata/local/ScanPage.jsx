import React, { useState } from "react";
import { scanKhata, getVelocity } from "../api/client";
import ResultsTable from "./ResultsTable";

export default function ScanPage() {
  const [image, setImage] = useState(null);
  const [result, setResult] = useState(null);
  const [velocity, setVelocity] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    if (!image) {
      setError("Upload a khata photo first.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const scanResult = await scanKhata(image);
      setResult(scanResult);
      const velocityResult = await getVelocity();
      setVelocity(velocityResult.velocity || []);
    } catch (err) {
      setError(err?.response?.data?.error || "Scan failed. Check backend and API key.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="kv-page">
      <section className="kv-hero">
        <p className="kv-eyebrow">Bahi Khata Scan</p>
        <h2>Photo lo. Digital khata ready.</h2>
        <p>
          Sarvam Vision reads the notebook, local extraction stores udhaar and stock
          records under this merchant only.
        </p>
      </section>

      <form className="kv-upload" onSubmit={handleSubmit}>
        <input
          accept="image/png,image/jpeg,image/webp"
          type="file"
          onChange={(event) => setImage(event.target.files?.[0] || null)}
        />
        <button disabled={loading} type="submit">
          {loading ? "Scanning..." : "Scan Khata"}
        </button>
      </form>

      {error ? <div className="kv-error">{error}</div> : null}
      {result?.privacy_note ? <div className="kv-note">{result.privacy_note}</div> : null}

      <div className="kv-grid">
        <ResultsTable title="Udhaar" rows={result?.udhaar || []} />
        <ResultsTable title="Inventory" rows={result?.inventory || []} />
        <ResultsTable title="Velocity" rows={velocity} emptyText="Need two dated scans per item." />
      </div>
    </div>
  );
}
