import { Send, X } from "lucide-react";
import { useMemo, useState } from "react";

import { sendBroadcast } from "../api/client";


const languageOptions = [
  { code: "hi-IN", label: "Hi" },
  { code: "mr-IN", label: "Mr" },
  { code: "gu-IN", label: "Gu" },
  { code: "en-IN", label: "En" },
];

const segmentOptions = [
  { id: "nearby_2km", label: "Nearby 2km", reach: 12400 },
  { id: "lapsed_21d", label: "Lapsed 21 days", reach: 6800 },
  { id: "category_groc", label: "Grocery buyers", reach: 18500 },
  { id: "festival_buyers", label: "Festival buyers", reach: 9200 },
];


export default function BroadcastModal({ eventId = "network_pulse", open, onClose, onSent }) {
  const [activeLang, setActiveLang] = useState("hi-IN");
  const [selectedSegment, setSelectedSegment] = useState("nearby_2km");
  const [selectedLanguages, setSelectedLanguages] = useState(["hi-IN", "mr-IN", "gu-IN", "en-IN"]);
  const [result, setResult] = useState(null);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");

  const segment = useMemo(
    () => segmentOptions.find((option) => option.id === selectedSegment) || segmentOptions[0],
    [selectedSegment],
  );

  if (!open) {
    return null;
  }

  function toggleLanguage(code) {
    setActiveLang(code);
    setSelectedLanguages((current) => {
      if (current.includes(code)) {
        return current.length === 1 ? current : current.filter((lang) => lang !== code);
      }
      return [...current, code];
    });
  }

  async function handleSend() {
    setSending(true);
    setError("");

    try {
      const response = await sendBroadcast({
        event_id: eventId,
        target_segment: {
          segment_id: selectedSegment,
        },
        languages: selectedLanguages,
      });
      setResult(response);
      onSent?.(response);
    } catch (err) {
      setError(err.message || "Broadcast failed");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="broadcast-modal" role="dialog" aria-modal="true" aria-labelledby="broadcast-title">
      <button className="broadcast-modal__backdrop" type="button" aria-label="Close" onClick={onClose} />

      <section className="broadcast-modal__panel">
        <header className="broadcast-modal__header">
          <div>
            <span className="network-eyebrow">Paytm Ads Broadcast</span>
            <h2 id="broadcast-title">Create customer broadcast</h2>
          </div>
          <button className="network-icon-button" type="button" aria-label="Close" onClick={onClose}>
            <X size={18} aria-hidden="true" />
          </button>
        </header>

        <div className="broadcast-modal__section">
          <label className="broadcast-modal__label" htmlFor="segment-select">
            Target segment
          </label>
          <select
            className="broadcast-modal__select"
            id="segment-select"
            value={selectedSegment}
            onChange={(event) => setSelectedSegment(event.target.value)}
          >
            {segmentOptions.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className="broadcast-modal__reach">
          <span>Estimated reach</span>
          <strong>{segment.reach.toLocaleString("en-IN")}</strong>
        </div>

        <div className="broadcast-modal__section">
          <span className="broadcast-modal__label">Languages</span>
          <div className="broadcast-modal__tabs" role="tablist" aria-label="Broadcast languages">
            {languageOptions.map((language) => {
              const selected = selectedLanguages.includes(language.code);
              return (
                <button
                  className={
                    selected
                      ? "broadcast-modal__tab broadcast-modal__tab--selected"
                      : "broadcast-modal__tab"
                  }
                  key={language.code}
                  type="button"
                  role="tab"
                  aria-selected={activeLang === language.code}
                  onClick={() => toggleLanguage(language.code)}
                >
                  {language.label}
                </button>
              );
            })}
          </div>
        </div>

        <div className="broadcast-modal__preview">
          <span className="broadcast-modal__label">Preview</span>
          <p>
            {result?.messages?.[activeLang] ||
              "Hi! IPL Final tomorrow - get your snacks today. 10% off on Rs 200+!"}
          </p>
        </div>

        {error ? <p className="broadcast-modal__error">{error}</p> : null}

        <footer className="broadcast-modal__footer">
          <p className="network-privacy-note">
            No customer PII exposed. Paytm Ads handles targeting on platform side.
          </p>
          <button
            className="network-primary-button"
            type="button"
            onClick={handleSend}
            disabled={sending}
          >
            <Send size={18} aria-hidden="true" />
            <span>{sending ? "Sending..." : "Send Broadcast"}</span>
          </button>
        </footer>
      </section>
    </div>
  );
}
