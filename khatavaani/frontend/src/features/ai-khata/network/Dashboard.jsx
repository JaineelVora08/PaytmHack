import { useEffect, useState } from "react";

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
    <main className="network-dashboard">
      <header className="network-dashboard__header">
        <div>
          <span className="network-eyebrow">Paytm Business Khata</span>
          <h1>Network Intelligence</h1>
          <p>Demand signals, local trends, and privacy-preserving customer broadcast.</p>
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
          <NetworkPulseCard pulse={pulse} onBroadcast={() => setBroadcastOpen(true)} />

          <section className="network-dashboard__grid">
            <div className="network-dashboard__column network-dashboard__column--wide">
              <div className="network-section-heading">
                <h2>News and trend signals</h2>
                <span>{trends.length} active</span>
              </div>

              <div className="network-trend-list">
                {trends.map((trend) => (
                  <TrendCard key={trend.id} trend={trend} />
                ))}
              </div>
            </div>

            <aside className="network-dashboard__column">
              <div className="network-section-heading">
                <h2>Group buy</h2>
                <span>Vyapar Mandal</span>
              </div>

              <VyaparMandalCard
                group={groups[0]}
                onJoin={(group) => setLastCampaign({ status: `Joined ${group.item}` })}
              />
            </aside>
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
    </main>
  );
}
