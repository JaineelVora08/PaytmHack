import React from "react";
import { createRoot } from "react-dom/client";
import { AIKhataRouter } from "./features/ai-khata";
import "./features/ai-khata/styles/ai-khata.css";

function App() {
  return <AIKhataRouter />;
}

const container = document.getElementById("root");
const root = createRoot(container);
root.render(<App />);
