# Business Idea Simulator And Stress Test

A single-idea-at-a-time business simulator. It generates a fully
Claude-Code-automatable business idea, runs it month by month through a
library of realistic operational and market shocks until it either fails or
proves itself viable, and - unlike a simple stochastic toy - doesn't trust a
single lucky pass. A candidate that clears the success bar is re-simulated
dozens more times and only declared the final winner if it holds up across
almost all of them. When an idea fails (or fails that validation), the
engine runs a root-cause analysis, generates a new idea informed by the
lessons learned, resets to default capital, and tries again - fully
automatically.

Pure Python standard library. No dependencies to install, no API keys, no
network calls, no LLM calls - fully deterministic and seedable.

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

### 3. Automation-only rule

Every idea the generator can produce must be something Claude Code (or an
equivalent AI coding agent) can run and operate **end to end via code and
APIs** - content generation, product listings, scheduling, fulfillment
routing, customer support - with **no required physical presence or manual
human labor**. This is a curation discipline enforced in
`data/archetypes.json`, not a runtime check: every archetype in that file is
one an AI agent could plausibly run alone (AI-written content sites,
micro-SaaS tools, print-on-demand brands, digital publishing pipelines,
automated lead-gen, etc.) - nothing that requires a human body to show up
somewhere.

### 4. Unlimited ideas via a combinatorial generator

Instead of a small fixed list, `simulator/generator.py`'s `IdeaGenerator`
draws from three axes and combines them at runtime:

- **14 business-model archetypes** (`data/archetypes.json`) - e.g. an
  AI-written SEO/affiliate blog, a micro-SaaS subscription tool, a
  print-on-demand apparel brand, an AI-generated ebook publishing pipeline,
  a faceless AI video content channel, a niche directory site, and more.
  Each carries numeric *ranges* (not fixed numbers) for pricing, customer
  counts, CAC, margins, and risk exposure.
- **20 niches/verticals** (`data/niches.json`) - personal finance, pet care,
  B2B SaaS tooling, fitness, gaming, real estate, crypto, and more - each
  applying multiplicative/additive deltas on top of the archetype (e.g. a
  finance niche raises regulatory exposure and price).
- **4 monetization variants** (`data/monetization.json`) - subscription,
  one-time purchase, affiliate/ads, usage-based.

14 × 20 × 4 = **1,120 categorical combinations**, each further perturbed by
the run's RNG into a unique concrete idea - practically unlimited relative
to any realistic `--max-ideas` setting. Generation is fully deterministic:
given the same `--seed`, the exact same sequence of ideas is produced every
time, same as the rest of the simulation.

Archetypes encode a `churn` range and a `net_edge` range rather than
independent growth/churn ranges (`growth = churn + edge`), which makes the
"growth must exceed churn for a baseline-viable idea" calibration rule
structurally guaranteed rather than something that can accidentally be
violated - a real bug that once made every idea in an earlier version of
this bank fail even with zero stress events.

### 5. Stress testing

`simulator/events.py` defines a library of ~11 realistic shocks (CAC spikes,
market demand shifts, supplier price hikes, new competitors, regulatory
costs, key-customer loss, equipment breakdowns, seasonal dips, viral upside,
payment holds, platform account suspensions/API revocations, and rare cash-
flow crises). Each month, every event has a chance to fire, weighted by how
strongly the idea carries that event's associated risk trait
(`ad_dependency`, `market_volatility`, `capital_intensity`,
`supply_chain_risk`, `competitive_pressure`, `regulatory_exposure`,
`customer_concentration`, `platform_dependency`) - an idea that leans
heavily on paid ads gets hit by CAC spikes far more often than one built on
organic content, and an idea that depends entirely on one marketplace or API
is far more exposed to a platform suspension event. Triggered effects
persist for a random number of months before wearing off.

### 6. A tougher, two-layer success bar

Because whatever the simulator declares a "winner" is meant to be taken into
real life, a single easy-to-scrape-by pass isn't good enough evidence.

**Layer 1 - a harder single run.** A run only clears the bar if **all** of
these hold:
- Operating net profit is positive **and** margin is at least **15%** for
  **18 consecutive months** (up from a laxer "just don't lose money"
  standard) - tracked completely independently from the negative-profit
  failure streak, so a barely-positive month resets the success streak
  without counting as a failure.
- Cash on hand has reached at least **3x** the idea's monthly fixed costs -
  proof of a real buffer, not just scraping by.

A run still ends early in bankruptcy, a 3-6 month negative-profit streak, or
a 78-month safety-cap timeout, exactly as before, just with the cap extended
to comfortably absorb the longer success streak.

**Layer 2 - repeated-trial validation ("graduation").** Clearing layer 1
once doesn't crown a winner. `simulator/validation.py`'s
`GraduationValidator` re-simulates the *same* idea **100 more times** (fresh
capital and RNG each trial) and only counts it as validated if its
empirical success rate is **≥ 95%**. That's a genuinely hard bar - testing
across the strongest archetypes showed true win rates typically in the
50-92% range, with only the luckiest specific niche/monetization draws
clearing 95% at all - so expect most candidates to fail graduation and the
loop to need well more than a handful of ideas (median ~13-18 in testing,
occasionally 40+) before one holds up; `max_ideas` defaults to **30**
accordingly. If a candidate falls short, its win rate is remembered as the
best candidate so far, a batch root-cause analysis steers the next idea
pick, and the loop keeps going. If `--max-ideas` is exhausted with nothing
graduating, the run reports the strongest candidate observed - clearly
labeled **NOT FULLY VALIDATED** - so it's never mistaken for a proven
winner.

**Favouring speed among validated candidates.** The loop does not stop at
the first idea that graduates. Since the winner is meant to be built in
real life, a business that takes 60 months to prove itself is a much bigger
commitment than one that takes 15 - so the loop keeps searching the full
`--max-ideas` budget, collects *every* candidate that clears the 95% bar,
and declares the final winner as whichever one reaches the success bar
**fastest on average** (`avg_months_to_success`, the mean months-to-success
across its 100 graduation trials - not a single run's noisy timing).
Because there's no early stop, every run uses its full iteration budget;
this is pure-Python arithmetic, so even 30 iterations complete in about a
second. Every validated candidate (not just the winner) is written to
`results/graduated_candidates.json`, ranked fastest-first, so you can see
the runner-ups too.

### 7. Auto-iteration loop

`run_simulator.py` drives the loop end to end:

1. Generate a starting idea via `IdeaGenerator` + `IdeaSelector`.
2. Simulate it from default capital until failure or the layer-1 success bar.
3. On failure, `simulator/analysis.py`'s `RootCauseAnalyzer` inspects which
   stress-event traits hit hardest and whether the idea's own margin/cost
   structure was already fragile, producing risk traits to avoid.
4. On a layer-1 success, `GraduationValidator` runs the layer-2 repeated
   trials. A pass is recorded as a graduated candidate (search continues -
   see above); on graduation failure, `RootCauseAnalyzer.analyze_batch()`
   aggregates root causes across the whole trial batch.
5. `IdeaSelector` generates the next candidate combo, scored to avoid the
   accumulated risk traits.
6. Capital resets to the defaults above and the loop repeats for the full
   `--max-ideas` budget (default 30). At the end, the winner is the fastest
   graduated candidate, or the best-observed-but-unvalidated candidate if
   nothing graduated.

## File structure

```
business-idea-simulator/
├── run_simulator.py        # CLI entry point / auto-iteration loop
├── simulator/
│   ├── config.py            # SimulationConfig defaults (capital, success bar, graduation)
│   ├── models.py             # MonthRecord / IdeaOutcome / RootCauseReport dataclasses
│   ├── ideas.py               # BusinessIdea dataclass (produced by the generator)
│   ├── generator.py            # IdeaGenerator - archetype x niche x monetization sampling
│   ├── events.py                 # Stress event library + trait-weighted trigger engine
│   ├── engine.py                   # SimulationEngine - the monthly simulation loop
│   ├── analysis.py                   # RootCauseAnalyzer - single-run and batch diagnosis
│   ├── selector.py                     # IdeaSelector - generator-aware next-idea picker
│   ├── validation.py                     # GraduationValidator - repeated-trial validation
│   └── logger.py                           # Console + JSON/CSV output
├── data/
│   ├── archetypes.json      # 14 automatable business-model archetypes
│   ├── niches.json           # 20 niche/vertical modifiers
│   └── monetization.json      # 4 monetization variants
└── results/                  # Generated per-run output (gitignored)
```

## Running it

```bash
python3 run_simulator.py
```

Useful flags:

```bash
python3 run_simulator.py --seed 42                  # reproducible run
python3 run_simulator.py --max-ideas 50               # try up to 50 ideas before giving up
python3 run_simulator.py --graduation-trials 40 --graduation-threshold 0.80  # loosen the bar
python3 run_simulator.py --starting-capital 800 --monthly-injection 400
python3 run_simulator.py --results-dir out
```

Console output narrates each iteration: the generated idea, its outcome,
which stress events hit it, and (on failure) the root-cause analysis and the
trait-informed pick of the next idea. On a layer-1 success, it also narrates
the graduation trial results and whether the idea passed.

## Output files

Each run writes to `results/` (default):

- `NN_<idea_id>.json` - full idea config + month-by-month outcome for
  iteration `NN`.
- `NN_<idea_id>_months.csv` - the same month-by-month data as CSV (including
  the per-month `margin`), for spreadsheet analysis or charting.
- `<idea_id>_root_cause.json` - the root-cause report for any idea that
  failed a single run or failed graduation.
- `<idea_id>_graduation.json` - the graduation trial breakdown (including
  `avg_months_to_success`) for any idea that cleared the single-run bar.
- `graduated_candidates.json` - every candidate that passed graduation,
  ranked fastest-first by `avg_months_to_success` - written only if at
  least one candidate graduated.
- `winner.json` - the fastest validated winner's idea + graduation stats
  (and how many candidates it was chosen among), if one graduated.
- `best_candidate_not_validated.json` - the strongest candidate observed if
  `--max-ideas` was exhausted without any graduation.
- `master_log.csv` - one row per iteration across the whole run (idea,
  outcome, months survived, final cash), appended across the loop.

## Extending it

- **Add a business-model archetype**: append an entry to
  `data/archetypes.json` with unit_price/customers/churn/net_edge/variance/
  cac/cogs_pct/fixed_costs ranges and risk_traits ranges for all 8 keys -
  make sure it satisfies the automation-only rule (no physical presence or
  manual human labor required).
- **Add a niche or monetization variant**: append an entry to
  `data/niches.json` or `data/monetization.json` with its deltas.
- **Add a stress event**: add a `StressEvent` to `EVENT_LIBRARY` in
  `simulator/events.py`, tying it to one of the 8 recognized trait keys.
- **Change financial defaults or the success/graduation bar**: edit
  `simulator/config.py` or pass CLI flags.
