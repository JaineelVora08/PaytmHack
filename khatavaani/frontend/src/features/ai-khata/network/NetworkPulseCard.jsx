import { Megaphone, Play, TrendingUp } from "lucide-react";


export default function NetworkPulseCard({ pulse, onBroadcast }) {
  if (!pulse) {
    return (
      <section className="network-pulse-card network-pulse-card--empty">
        <p className="network-muted">Network pulse unavailable right now.</p>
      </section>
    );
  }

  const bars = pulse.viz_data?.length ? pulse.viz_data : [12, 18, 24, 36, 52, 68, 82];
  const maxBar = Math.max(...bars);

  function playPulseAudio() {
    if (!pulse.audio_url) {
      return;
    }

    new Audio(pulse.audio_url).play();
  }

  return (
    <section className="network-pulse-card">
      <div className="network-pulse-card__content">
        <div className="network-eyebrow">
          <TrendingUp size={16} aria-hidden="true" />
          Network Pulse
        </div>

        <h2 className="network-pulse-card__title">{pulse.category}</h2>
        <p className="network-pulse-card__headline">
          {pulse.headline_hi || pulse.headline_en}
        </p>

        <div className="network-pulse-card__stats" aria-label="Pulse stats">
          <div>
            <span className="network-stat__value">{pulse.merchant_count}</span>
            <span className="network-stat__label">merchants</span>
          </div>
          <div>
            <span className="network-stat__value">{pulse.demand_multiplier}x</span>
            <span className="network-stat__label">demand</span>
          </div>
          <div>
            <span className="network-stat__value">{pulse.region}</span>
            <span className="network-stat__label">region</span>
          </div>
        </div>

        <p className="network-privacy-note">{pulse.privacy_note}</p>
      </div>

      <div className="network-pulse-card__side">
        <div className="network-pulse-chart" aria-label="Seven day demand trend">
          {bars.map((value, index) => (
            <span
              className="network-pulse-chart__bar"
              key={`${value}-${index}`}
              style={{ "--bar-height": `${Math.max(12, (value / maxBar) * 100)}%` }}
              title={`Day ${index + 1}: ${value}`}
            />
          ))}
        </div>

        <div className="network-pulse-card__actions">
          <button className="network-icon-button" type="button" onClick={playPulseAudio}>
            <Play size={18} aria-hidden="true" />
            <span>Play</span>
          </button>
          <button className="network-primary-button" type="button" onClick={onBroadcast}>
            <Megaphone size={18} aria-hidden="true" />
            <span>Broadcast</span>
          </button>
        </div>
      </div>
    </section>
  );
}
