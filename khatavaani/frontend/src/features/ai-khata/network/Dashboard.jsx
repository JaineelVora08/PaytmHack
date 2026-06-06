import { useEffect, useState } from "react";
import { Megaphone, PackagePlus, Store, UsersRound } from "lucide-react";

import { getGroupBuy, getNewsTrends, getPulse } from "../api/client";
import BroadcastModal from "./BroadcastModal";
import NetworkPulseCard from "./NetworkPulseCard";
import TrendCard from "./TrendCard";
import VyaparMandalCard from "./VyaparMandalCard";


export default function Dashboard() {
  const [pulse, setPulse] = useState(null);
  const [trends, setTrends] = useState([]);
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [broadcastOpen, setBroadcastOpen] = useState(false);
  const [lastCampaign, setLastCampaign] = useState(null);
  const [joinedGroup, setJoinedGroup] = useState(null);

  useEffect(() => {
    let mounted = true;

    async function loadDashboard() {
      setLoading(true);
      setError("");

      try {
        const [pulseResponse, trendsResponse, groupResponse] = await Promise.all([
          getPulse(),
          getNewsTrends(),
          getGroupBuy(),
        ]);

        if (!mounted) {
          return;
        }

        setPulse(pulseResponse.pulse);
        setTrends(trendsResponse.trends || []);
        setGroups(groupResponse.active_groups || []);
      } catch (err) {
        if (mounted) {
          setError(err.message || "Unable to load network intelligence");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    loadDashboard();

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="network-dashboard">
      <header className="network-dashboard__header">
        <div>
          <span className="network-eyebrow">Paytm Business Khata</span>
          <h2>Network Intelligence</h2>
          <p>Separate tools for nearby merchant signals, restocking, group buys, and ads broadcast.</p>
        </div>
        {lastCampaign ? (
          <div className="network-dashboard__campaign">
            <span>Last campaign</span>
            <strong>{lastCampaign.status}</strong>
          </div>
        ) : null}
      </header>

      {error ? <p className="network-dashboard__error">{error}</p> : null}

      {loading ? (
        <section className="network-dashboard__loading">Loading network signals...</section>
      ) : (
        <>
          <section className="network-feature-strip" aria-label="Network intelligence features">
            <FeaturePill
              icon={Store}
              title="Nearby merchants"
              text="See anonymized demand moves around your shop."
            />
            <FeaturePill
              icon={PackagePlus}
              title="Restocking signals"
              text="Turn news, weather, and festival events into stock actions."
            />
            <FeaturePill
              icon={UsersRound}
              title="Group buy"
              text="Join nearby merchants to unlock better purchase prices."
            />
            <FeaturePill
              icon={Megaphone}
              title="Paytm Ads"
              text="Broadcast offers by segment without seeing customer PII."
            />
          </section>

          <section className="network-feature-section">
            <div className="network-section-heading">
              <div>
                <span className="network-section-kicker">Feature 1</span>
                <h3>Other merchants around you</h3>
              </div>
              <span>Privacy preserved</span>
            </div>
            <NetworkPulseCard pulse={pulse} />
          </section>

          <section className="network-dashboard__grid">
            <div className="network-dashboard__column network-dashboard__column--wide">
              <div className="network-section-heading">
                <div>
                  <span className="network-section-kicker">Feature 2</span>
                  <h3>Restocking from news and trends</h3>
                </div>
                <span>{trends.length} active</span>
              </div>

              <div className="network-trend-list">
                {trends.length === 0 ? (
                  <p className="network-muted">No active trend signals right now.</p>
                ) : (
                  trends.map((trend) => (
                    <TrendCard key={trend.id} trend={trend} />
                  ))
                )}
              </div>
            </div>

            <aside className="network-dashboard__column">
              <div className="network-section-heading">
                <div>
                  <span className="network-section-kicker">Feature 3</span>
                  <h3>Vyapar Mandal group buy</h3>
                </div>
                <span>Bulk savings</span>
              </div>

              <VyaparMandalCard
                group={groups[0]}
                onJoin={(group) => setJoinedGroup(group)}
              />
              {joinedGroup ? (
                <p className="network-dashboard__campaign">
                  Joined group buy: <strong>{joinedGroup.item}</strong>
                </p>
              ) : null}
            </aside>
          </section>

          <section className="network-feature-section">
            <div className="network-section-heading">
              <div>
                <span className="network-section-kicker">Feature 4</span>
                <h3>Paytm Ads broadcast</h3>
              </div>
              <span>No PII exposed</span>
            </div>
            <AdsBroadcastCard
              lastCampaign={lastCampaign}
              onBroadcast={() => setBroadcastOpen(true)}
            />
          </section>
        </>
      )}

      <BroadcastModal
        eventId="network_pulse_ors"
        open={broadcastOpen}
        onClose={() => setBroadcastOpen(false)}
        onSent={(campaign) => {
          setLastCampaign(campaign);
          setBroadcastOpen(false);
        }}
      />
    </div>
  );
}

function FeaturePill({ icon: Icon, title, text }) {
  return (
    <article className="network-feature-pill">
      <Icon size={20} aria-hidden="true" />
      <div>
        <strong>{title}</strong>
        <span>{text}</span>
      </div>
    </article>
  );
}

function AdsBroadcastCard({ lastCampaign, onBroadcast }) {
  return (
    <article className="ads-broadcast-card">
      <div>
        <span className="network-eyebrow">
          <Megaphone size={16} aria-hidden="true" />
          Customer Broadcast
        </span>
        <h3>Send offers through Paytm Ads segments</h3>
        <p>
          Choose audience segments like nearby users, lapsed buyers, grocery buyers, or
          festival buyers. Paytm Ads handles targeting; merchants never see phone numbers,
          names, or customer IDs.
        </p>
      </div>
      <div className="ads-broadcast-card__side">
        <div className="ads-broadcast-card__reach">
          <span>Mock reach starts at</span>
          <strong>12,400</strong>
          <small>nearby users</small>
        </div>
        {lastCampaign ? (
          <p className="network-dashboard__campaign">
            Last campaign: <strong>{lastCampaign.status}</strong>
          </p>
        ) : null}
        <button className="network-primary-button" type="button" onClick={onBroadcast}>
          <Megaphone size={18} aria-hidden="true" />
          <span>Create Broadcast</span>
        </button>
      </div>
    </article>
  );
}
