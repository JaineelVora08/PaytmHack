CREATE TABLE IF NOT EXISTS merchants (
  id TEXT PRIMARY KEY,
  display_name TEXT NOT NULL DEFAULT 'Demo Merchant',
  region TEXT NOT NULL DEFAULT 'urban_mumbai',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS udhaar (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  merchant_id TEXT NOT NULL,
  customer_name TEXT NOT NULL,
  amount REAL NOT NULL,
  type TEXT NOT NULL CHECK(type IN ('debit', 'credit')),
  entry_date TEXT NOT NULL,
  source_scan_id TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (merchant_id) REFERENCES merchants(id)
);

CREATE TABLE IF NOT EXISTS inventory_scans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  merchant_id TEXT NOT NULL,
  item_name TEXT NOT NULL,
  quantity REAL NOT NULL,
  scan_date TEXT NOT NULL,
  unit TEXT NOT NULL DEFAULT 'units',
  source_scan_id TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (merchant_id) REFERENCES merchants(id)
);
