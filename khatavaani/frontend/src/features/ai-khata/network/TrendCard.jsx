import { CalendarDays, CloudSun, Trophy } from "lucide-react";


const iconMap = {
  cricket: Trophy,
  festival: CalendarDays,
  weather: CloudSun,
};


export default function TrendCard({ trend }) {
  const Icon = iconMap[trend.type] || CalendarDays;

  return (
    <article className="network-trend-card">
      <div className="network-trend-card__icon" aria-hidden="true">
        <Icon size={22} />
      </div>

      <div className="network-trend-card__body">
        <div className="network-trend-card__meta">
          <span>{trend.source}</span>
          <span>{trend.region}</span>
        </div>
        <h3 className="network-trend-card__title">{trend.title}</h3>
        <p className="network-trend-card__copy">{trend.body_hi || trend.body_en}</p>

        <div className="network-impact-list" aria-label="Expected impact">
          {trend.impact?.map((item) => (
            <span className="network-impact-pill" key={`${trend.id}-${item.item}`}>
              {item.item}
              <strong>{item.multiplier}</strong>
            </span>
          ))}
        </div>
      </div>

      <div className="network-trend-card__support">
        <strong>{trend.supporting_merchants}</strong>
        <span>merchants</span>
      </div>
    </article>
  );
}
