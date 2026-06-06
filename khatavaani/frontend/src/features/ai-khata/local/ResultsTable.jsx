import React from "react";

export default function ResultsTable({ title, rows, emptyText }) {
  const columns = rows?.length ? Object.keys(rows[0]) : [];

  return (
    <section className="kv-card">
      <div className="kv-card-header">
        <h3>{title}</h3>
        <span>{rows?.length || 0} records</span>
      </div>

      {!rows?.length ? (
        <p className="kv-muted">{emptyText || "No records yet."}</p>
      ) : (
        <div className="kv-table-wrap">
          <table className="kv-table">
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column}>{label(column)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={row.id || `${title}-${index}`}>
                  {columns.map((column) => (
                    <td key={column}>{formatValue(row[column])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function label(column) {
  return column.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatValue(value) {
  if (typeof value === "number") {
    return Number.isInteger(value) ? value : value.toFixed(2);
  }
  return value;
}
