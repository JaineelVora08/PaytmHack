import { MapPin, ShieldCheck, TrendingUp } from "lucide-react";


export default function NetworkPulseCard({ pulse }) {
  if (!pulse) {
    return (
      <section className="network-pulse-card network-pulse-card--empty">
        <p className="network-muted">Network pulse unavailable right now.</p>
      </section>
    );
  }

  const bars = pulse.viz_data?.length ? pulse.viz_data : [12, 18, 24, 36, 52, 68, 82];
  const maxBar = Math.max(...bars);

  return (
    <section className="network-pulse-card">
      <div className="network-pulse-card__content">
        <div className="network-eyebrow">
          <TrendingUp size={16} aria-hidden="true" />
          Other Merchants Around You
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

        <div className="network-insight-list">
          <span>
            <MapPin size={16} aria-hidden="true" />
            Nearby merchant behavior, not customer data
          </span>
          <span>
            <ShieldCheck size={16} aria-hidden="true" />
            k-anonymous and noisy aggregate
          </span>
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

        <p className="network-chart-caption">7-day restocking curve across nearby merchants</p>
      </div>
    </section>
  );
}
