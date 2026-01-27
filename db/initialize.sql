-- Postgres initialization script for ProjectSeagull
-- Creates core tables and seeds them with entries equivalent to the CSV defaults.

-- Create tables

CREATE TABLE IF NOT EXISTS available_signals (
  id               text PRIMARY KEY,
  source           text NOT NULL CHECK (source IN ('massive','sf1')),
  spec             text NOT NULL,
  model_freq       text,                   -- e.g., '1D','1H','15T'
  description      text,
  enabled          boolean NOT NULL DEFAULT true,
  created_at       timestamptz NOT NULL DEFAULT now(),
  last_access_time timestamptz             -- tracks when signal was last used by an agent
);

-- Revised test_scope schema: key by test_name, and a child table for symbols.
-- (test_scope tables removed per new design: each agent defines the single trading symbol)

CREATE TABLE IF NOT EXISTS agents_registry (
  name         text PRIMARY KEY,
  path         text NOT NULL,          -- reference path (e.g., 'db://agents/{name}')
  code         text,                   -- Python source code stored in database
  description  text,
  enabled      boolean NOT NULL DEFAULT true,
  created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS test_definitions (
  name                 text PRIMARY KEY,
  trials               integer NOT NULL,
  overall_start_date   date NOT NULL,
  overall_end_date     date NOT NULL,
  seed                 integer,
  record_curves        boolean NOT NULL DEFAULT false,
  plot_dir             text,
  trading_days         integer NOT NULL DEFAULT 14,
  created_at           timestamptz NOT NULL DEFAULT now()
);

-- Jobs table: which agent to run against which test definition
CREATE TABLE IF NOT EXISTS test_jobs (
  test_name    text NOT NULL REFERENCES test_definitions(name) ON UPDATE CASCADE ON DELETE CASCADE,
  agent_name   text NOT NULL REFERENCES agents_registry(name) ON UPDATE CASCADE ON DELETE CASCADE,
  created_at   timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (test_name, agent_name)
);

-- Seed: available_signals (from data/available_signals.csv)

INSERT INTO available_signals (id, source, spec, model_freq, description, enabled) VALUES
  ('SPY_day_close','massive','SPY:day:1:close','1D','SPY daily close', true),
  ('QQQ_day_close','massive','QQQ:day:1:close','1D','QQQ daily close', true),
  ('AAPL_arq_revenue','sf1','AAPL:ARQ:revenue','1D','AAPL as-reported quarterly revenue (daily-forward-filled)', true),
  ('AAPL_mrq_assets','sf1','AAPL:MRQ:assets','1D','AAPL most-recent quarterly assets (daily-forward-filled)', true)
ON CONFLICT (id) DO UPDATE
SET source = EXCLUDED.source,
    spec = EXCLUDED.spec,
    model_freq = EXCLUDED.model_freq,
    description = EXCLUDED.description,
    enabled = EXCLUDED.enabled;

-- Seed: test_scope (from Backtesting/config/test_scope.csv)

-- (no test_scope seeds; agents choose their own symbol per test)

-- Seed: agents_registry
-- NOTE: All .py files from Agents/instances/ are automatically registered
-- with their code uploaded to the database when running init_db.py
-- The entries below are legacy seeds and will be overwritten by auto-registration

INSERT INTO agents_registry (name, path, description, enabled) VALUES
  ('example_function_agent','db://agents/example_function_agent','Example instance agent using registry signals', true)
ON CONFLICT (name) DO UPDATE
SET path = EXCLUDED.path,
    description = EXCLUDED.description,
    enabled = EXCLUDED.enabled;

-- Seed: test_types (from Backtesting/config/test_types.csv)

INSERT INTO test_definitions (
  name, trials, overall_start_date, overall_end_date,
  seed, record_curves, plot_dir, trading_days
) VALUES
  ('quick',    1, '2023-01-01','2023-06-30', 42, false, 'D:\Users\zhang\output data from project seagull', 7),
  ('standard', 3, '2022-01-01','2022-12-31', 42, true,  'D:\Users\zhang\output data from project seagull', 14)
ON CONFLICT (name) DO UPDATE
SET trials = EXCLUDED.trials,
    overall_start_date = EXCLUDED.overall_start_date,
    overall_end_date = EXCLUDED.overall_end_date,
    seed = EXCLUDED.seed,
    record_curves = EXCLUDED.record_curves,
    plot_dir = EXCLUDED.plot_dir,
    trading_days = EXCLUDED.trading_days;

-- Seed: test_jobs mapping agents to tests
INSERT INTO test_jobs (test_name, agent_name) VALUES
  ('quick','example_function_agent'),
  ('standard','example_function_agent')
ON CONFLICT (test_name, agent_name) DO NOTHING;
