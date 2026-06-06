CREATE TABLE IF NOT EXISTS merchants (
  id TEXT PRIMARY KEY,
  display_name TEXT NOT NULL DEFAULT 'Demo Merchant',
  region TEXT NOT NULL DEFAULT 'urban_mumbai',
  language_pref TEXT NOT NULL DEFAULT 'hi-IN',
  region_psi INTEGER NOT NULL DEFAULT 75,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS udhaar (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  merchant_id TEXT NOT NULL,
  customer_name TEXT NOT NULL,
  amount REAL NOT NULL,
  type TEXT NOT NULL CHECK(type IN ('debit', 'credit')),
  entry_date TEXT NOT NULL,
  source TEXT NOT NULL DEFAULT 'scan',
  source_scan_id TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (merchant_id) REFERENCES merchants(id)
);

CREATE TABLE IF NOT EXISTS inventory (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  merchant_id TEXT NOT NULL,
  item_name TEXT NOT NULL,
  category TEXT,
  quantity REAL NOT NULL,
  reorder_threshold INTEGER NOT NULL DEFAULT 5,
  scan_date TEXT NOT NULL,
  unit TEXT NOT NULL DEFAULT 'units',
  source_scan_id TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (merchant_id) REFERENCES merchants(id)
);

CREATE TABLE IF NOT EXISTS network_signal (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  region TEXT NOT NULL,
  category TEXT NOT NULL,
  signal_date TEXT NOT NULL,
  merchant_count INTEGER NOT NULL CHECK(merchant_count >= 5),
  demand_index REAL NOT NULL,
  context_tags TEXT
);
