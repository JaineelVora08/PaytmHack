import React, { useState } from "react";
import "./styles/ai-khata.css";
import AskPage from "./local/AskPage";
import ScanPage from "./local/ScanPage";
import Dashboard from "./network/Dashboard";

export default function AIKhataRouter() {
  const [tab, setTab] = useState("scan");

  return (
    <main className="kv-shell">
      <header className="kv-topbar">
        <div>
          <p className="kv-eyebrow">Paytm Business Khata</p>
          <h1>KhataVaani AI</h1>
        </div>
        <nav className="kv-tabs">
          <button className={tab === "scan" ? "active" : ""} onClick={() => setTab("scan")}>
            Scan
          </button>
          <button className={tab === "ask" ? "active" : ""} onClick={() => setTab("ask")}>
            Ask
          </button>
          <button className={tab === "network" ? "active" : ""} onClick={() => setTab("network")}>
            Network
          </button>
        </nav>
      </header>

      {tab === "scan" ? <ScanPage /> : null}
      {tab === "ask" ? <AskPage /> : null}
      {tab === "network" ? <Dashboard /> : null}
    </main>
  );
}
