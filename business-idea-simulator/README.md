# Business Idea Simulator And Stress Test

A single-idea-at-a-time business simulator. It runs a bootstrapped business
idea, month by month, through a bank of realistic operational and market
shocks until it either fails or proves itself viable. When an idea fails,
the engine runs a root-cause analysis, picks a new idea that avoids the
traits that killed the last one, resets to default capital, and tries
again - fully automatically.

Pure Python standard library. No dependencies to install, no API keys
required.

## How it works

### 1. Financial framework

Every idea starts from the same defaults (`simulator/config.py`):

- Starting capital: **SGD 500**
- Monthly capital injection: **SGD 350** (added every month regardless of
  performance, like a founder topping up from savings)

Capital injections are cash, not profit. They buy the business more months
of runway but do **not** count toward operating net profit - so injecting
money into a broken business model delays the reckoning but doesn't fix it,
same as in real life.

### 2. Single-idea focus

`simulator/engine.py`'s `SimulationEngine` simulates exactly one
`BusinessIdea` per run, computing customer growth/churn, revenue, COGS,
customer acquisition cost, fixed costs, and any active stress-event effects
for every month, in isolation from every other idea.

### 3. Stress testing

`simulator/events.py` defines a library of ~10 realistic shocks (CAC
spikes, market demand shifts, supplier price hikes, new competitors,
regulatory costs, key-customer loss, equipment breakdowns, seasonal dips,
viral upside, payment holds, and rare cash-flow crises). Each month, every
event has a chance to fire, weighted by how strongly the idea carries that
event's associated risk trait (`ad_dependency`, `market_volatility`,
`capital_intensity`, `supply_chain_risk`, `competitive_pressure`,
`regulatory_exposure`, `customer_concentration`) - an idea that leans
heavily on paid ads gets hit by CAC spikes far more often than one built on
referrals. Triggered effects persist for a random number of months before
wearing off.

### 4. Failure conditions

A run ends the moment one of these is true:

- **Bankruptcy** - cash balance drops to zero or below.
- **Negative-profit streak** - operating net profit is negative for a
  number of consecutive months, randomly drawn between 3 and 6 at the start
  of each run (modeling varying founder patience).
- **Success** - operating net profit is positive for 12 consecutive months
  (the loop then stops early - see below).
- **Timeout** - a 60-month safety cap in case a run drifts indefinitely
  without resolving; reported for completeness but rare in practice.

### 5. Auto-iteration loop

`run_simulator.py` drives the loop end to end:

1. Pick a starting idea from `data/idea_bank.json`.
2. Simulate it from default capital until failure or success.
3. On failure, `simulator/analysis.py`'s `RootCauseAnalyzer` inspects which
   stress-event traits hit hardest and whether the idea's own margin/cost
   structure was already fragile, producing a short list of risk traits to
   avoid.
4. `simulator/selector.py`'s `IdeaSelector` picks the next untried idea from
   the bank that carries the least exposure to those traits.
5. Capital resets to the defaults above and the loop repeats, up to
   `--max-ideas` iterations (default 10) or until an idea succeeds,
   whichever comes first.

## File structure

```
business-idea-simulator/
├── run_simulator.py        # CLI entry point / auto-iteration loop
├── simulator/
│   ├── config.py            # SimulationConfig defaults (capital, thresholds)
│   ├── models.py             # MonthRecord / IdeaOutcome / RootCauseReport dataclasses
│   ├── ideas.py               # BusinessIdea dataclass + idea-bank loader
│   ├── events.py               # Stress event library + trait-weighted trigger engine
│   ├── engine.py                # SimulationEngine - the monthly simulation loop
│   ├── analysis.py               # RootCauseAnalyzer - post-failure diagnosis
│   ├── selector.py                # IdeaSelector - rule-based next-idea picker
│   └── logger.py                   # Console + JSON/CSV output
├── data/
│   └── idea_bank.json       # 12 curated bootstrapped business idea templates
└── results/                  # Generated per-run output (gitignored)
```

## Running it

```bash
python3 run_simulator.py
```

Useful flags:

```bash
python3 run_simulator.py --seed 42          # reproducible run
python3 run_simulator.py --max-ideas 5       # stop after 5 ideas tried
python3 run_simulator.py --starting-capital 800 --monthly-injection 400
python3 run_simulator.py --results-dir out
```

Console output narrates each iteration: the idea being tested, its
outcome, which stress events hit it, and (on failure) the root-cause
analysis and the trait-informed pick of the next idea.

## Output files

Each run writes to `results/` (default):

- `NN_<idea_id>.json` - full idea config + month-by-month outcome for
  iteration `NN`.
- `NN_<idea_id>_months.csv` - the same month-by-month data as CSV, for
  spreadsheet analysis or charting.
- `<idea_id>_root_cause.json` - the root-cause report for any idea that
  failed.
- `master_log.csv` - one row per iteration across the whole run
  (idea, outcome, months survived, final cash), appended across the loop.

## Extending it

- **Add a business idea**: append an entry to `data/idea_bank.json`
  following the existing `BusinessIdea` shape - pricing, growth/churn,
  costs, and a `risk_traits` dict of 0..1 weights.
- **Add a stress event**: add a `StressEvent` to `EVENT_LIBRARY` in
  `simulator/events.py`, tying it to one of the recognized trait keys.
- **Change financial defaults**: edit `simulator/config.py` or pass CLI
  flags.
