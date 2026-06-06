export { default as AIKhataRouter } from "./AIKhataRouter";
export { default as ScanPage } from "./local/ScanPage";
export { default as AskPage } from "./local/AskPage";
export { default as Dashboard } from "./network/Dashboard";

export function ImportButton({ onClick }) {
  return (
    <button className="kv-import-button" onClick={onClick} type="button">
      Open KhataVaani AI
    </button>
  );
}
