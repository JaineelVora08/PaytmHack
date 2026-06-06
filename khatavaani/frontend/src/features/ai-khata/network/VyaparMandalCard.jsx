import { ShoppingBag, Users } from "lucide-react";


function getDiscountPercent(group) {
  if (typeof group?.discount_percent === "number") {
    return group.discount_percent;
  }

  if (!group?.regular_price || !group?.group_price) {
    return 0;
  }

  return Math.round(((group.regular_price - group.group_price) / group.regular_price) * 100);
}


export default function VyaparMandalCard({ group, onJoin }) {
  if (!group) {
    return (
      <section className="vyapar-card vyapar-card--empty">
        <p className="network-muted">No active group buy right now.</p>
      </section>
    );
  }

  const discount = getDiscountPercent(group);
  const joinedUnits = group.current_units || group.merchants_count || 0;
  const progress = Math.min(100, Math.round((joinedUnits / group.minimum_units) * 100));

  return (
    <section className="vyapar-card">
      <div className="vyapar-card__accent" aria-hidden="true" />

      <div className="vyapar-card__header">
        <div>
          <span className="network-eyebrow network-eyebrow--orange">
            <Users size={16} aria-hidden="true" />
            Vyapar Mandal
          </span>
          <h2 className="vyapar-card__title">{group.item}</h2>
        </div>
        <div className="vyapar-card__discount">
          <strong>{discount}%</strong>
          <span>off</span>
        </div>
      </div>

      <div className="vyapar-card__price-row">
        <div>
          <span className="network-stat__label">Group price</span>
          <strong className="vyapar-card__price">
            Rs {group.group_price}
            <small>/unit</small>
          </strong>
        </div>
        <div>
          <span className="network-stat__label">Market price</span>
          <strong className="vyapar-card__market-price">
            Rs {group.regular_price}
            <small>/unit</small>
          </strong>
        </div>
      </div>

      <div className="vyapar-card__progress">
        <div className="vyapar-card__progress-label">
          <span>{joinedUnits} joined</span>
          <span>{group.minimum_units} minimum units</span>
        </div>
        <div className="vyapar-card__progress-track">
          <span style={{ "--progress": `${progress}%` }} />
        </div>
      </div>

      <div className="vyapar-card__footer">
        <span className="vyapar-card__members">
          <ShoppingBag size={16} aria-hidden="true" />
          {group.merchants_count} nearby merchants
        </span>
        <button className="network-secondary-button" type="button" onClick={() => onJoin?.(group)}>
          Join Group
        </button>
      </div>
    </section>
  );
}
