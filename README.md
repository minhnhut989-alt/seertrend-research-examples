# SeerTrend Research Examples

Small, runnable examples for checking assumptions in trading research. Maintained for [SeerTrend](https://seertrend.com/).

The first example reconstructs the latest **published and received** data vintage at a decision cutoff. It runs offline with Python 3.11+ and the standard library. It does not connect to a broker, submit orders or calculate strategy returns.

## Why publication time is not enough

Suppose a fictional observation is published at 09:00:00 UTC, reaches your system at 09:00:02, and is revised at 10:00:00. A historical decision at 09:00:01 cannot use the first value yet. A decision at 09:30 cannot use the later revision either.

The example uses two rules:

1. A vintage becomes available at the later of `published_at` and `received_at`.
2. Among available vintages for the same `(series, period)`, select the latest source publication time. A delayed arrival of an old release must not overwrite a newer revision.

All timestamps require an explicit UTC offset. Equal-to-cutoff observations are included; a real system that needs processing time should set an earlier information cutoff or model that delay separately.

## Run it

No package installation, credentials or API keys are required. From the repository directory:

```sh
python point_in_time.py examples/fictional_vintages.csv --at 2026-02-05T09:30:00Z
```

The output contains `DEMO_ACTIVITY=100` and `DEMO_PRICES=2.4`. It excludes the later `DEMO_ACTIVITY=105` revision. At `09:00:01Z` the output contains only the header because no observation has arrived. At `10:00:03Z` the revision is available.

The input file is never changed. Output is CSV on standard output, so it can be inspected or redirected to a new file.

```sh
python -m unittest discover -s tests -v
```

Tests cover receipt latency, the exact cutoff, equivalent timezone offsets, future revisions, out-of-order delivery, independent series, conflicting vintages and invalid timestamps/values.

## Input contract

| Column | Meaning |
| --- | --- |
| `series` | Stable identifier for an observation series |
| `period` | Observation period; separate periods are not merged |
| `value` | Finite decimal value, without an implied unit |
| `published_at` | Timestamp identifying the source's publication/vintage |
| `received_at` | Timestamp when the research system received that vintage |

The included CSV is entirely **fictional**. Its series, values and timestamps are not economic releases or market data. Replace it only with data you are permitted to use and whose historical availability you can establish.

Conflicting values sharing a series, period and source publication timestamp raise an error: this input format cannot resolve that ambiguity. Keep a source revision identifier or sequence number in a production dataset rather than inventing an ordering. Invalid or missing fields fail with an error; they are not silently filled.

## What this check cannot prove

This is an educational selection example, not a full backtesting engine or an audit certificate. It assumes the timestamps and identifiers supplied by the caller are trustworthy. The conservative `max()` gate does not repair clock errors. It does not implement record withdrawals, permission windows, historical constituent lists, corporate actions, feature-label overlap handling, fill simulation, slippage, financing or model-selection corrections.

Selecting the right vintage does not establish that a strategy has an edge. A model can still overfit, use unavailable features elsewhere or depend on unrealistic execution assumptions. Preserve the raw source versions and decision log, and evaluate the rest of the research process separately.

## Companion reading and disclosure

For the broader distinction between prediction, decisions, execution and implementation evidence, see SeerTrend's [AI in Trading: What Academic Research Shows—and What Backtests Cannot Prove](https://seertrend.com/ai-in-trading-academic-evidence-backtest-limits/). It links to the underlying academic papers and states its review limits. This code is an original teaching example; it is not a replication of those papers.

The repository and linked website share an owner. Code and documentation were prepared with AI assistance; the test suite was executed locally before publication. No independent academic peer review, live performance result, third-party endorsement or investment recommendation is claimed. No private SeerTrend application source or real account data is included.
