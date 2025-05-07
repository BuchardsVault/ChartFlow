

import matplotlib
matplotlib.use("TkAgg")                # macOS / linux‑desktop stability
from datetime import date, timedelta
from pathlib import Path
from textx import metamodel_from_file
from dateutil.relativedelta import relativedelta
import pandas as pd
import pandas_market_calendars as mcal
import yfinance as yf
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from tabulate import tabulate
from mplfinance.original_flavor import candlestick_ohlc
import matplotlib.dates as mdates
import sys

# ───────────────────────────  helpers  ──────────────────────────
class CFError(Exception):
    """Language‑level error (adds line number when raised from eval loop)."""
    pass

class ChartCtx:
    """Holds a figure/axes + style options so multiple series share one plot."""
    def __init__(self): self.reset()
    def reset(self):
        self.fig = self.ax = None
        self.opts = dict(theme="light", width=12, height=6, grid=True)
    def apply(self, opts):
        self.opts.update(opts)
        plt.style.use("default" if self.opts["theme"] == "light"
                    else "dark_background")

# ───────────────────────────── trading‑day helper ─────────────────────────────
def last_n_trading_days(n):
    nyse  = mcal.get_calendar("NYSE")
    today = pd.Timestamp.now(tz="America/New_York").date()
    trad  = nyse.valid_days(
        start_date=pd.Timestamp(today) - pd.DateOffset(months=18),
        end_date=pd.Timestamp(today) + pd.DateOffset(days=1)
    ).date
    trad  = [d for d in trad if d <= today]
    if len(trad) < n:
        raise CFError(f"Only {len(trad)} trading days available")
    return trad[-n].isoformat(), trad[-1].isoformat()

# ───────────────────────── date‑clause parser ─────────────────────────
def parse_date(clause):
    if getattr(clause, "start", None):
        return clause.start, clause.end
    if getattr(clause, "year", None):
        y = int(clause.year)
        return f"{y}-01-01", f"{y}-12-31"
    if getattr(clause, "amount", None):
        n    = int(clause.amount)
        unit = clause.unit.lower()
        today = date.today()
        if unit.startswith("day"):
            return last_n_trading_days(n)
        elif unit.startswith("week"):
            start = today - timedelta(weeks=n)
        elif unit.startswith("month"):
            start = today - relativedelta(months=n)
        elif unit.startswith("year"):
            start = today - relativedelta(years=n)
        else:
            raise CFError(f"Unknown time unit '{unit}'")
        return start.isoformat(), today.isoformat()
    raise CFError("Bad date clause")

# ────────────────────────── asset spec -> list ─────────────────────────
def asset_list(spec, env):
    if getattr(spec, "var", None):
        v = env.get(spec.var)
        if isinstance(v, str):  return [v]
        if isinstance(v, list): return v
        raise CFError(f"Variable '{spec.var}' is not string/list")
    if getattr(spec, "symbol", None):
        return [spec.symbol.strip('"')]
    if getattr(spec, "symbols", None):
        return [s.strip('"') for s in spec.symbols]
    raise CFError("Bad asset specification")

# ───────────────────────── expression evaluator ─────────────────────────
def eval_expr(expr, env):
    kind = expr.__class__.__name__
    if kind == "List":
        return [eval_expr(e, env) for e in expr.elements]
    if kind == "FunctionCall":
        fn  = env.get(expr.name)
        if not callable(fn):
            raise CFError(f"Unknown function '{expr.name}'")
        args = [eval_expr(a, env) for a in expr.args]
        return fn(*args)
    if isinstance(expr, str):
        if expr.startswith('"'): return expr[1:-1]
        if expr.isdigit():       return int(expr)
        return env.get(expr, expr)
    return expr

# ───────────────────────── tidy volume for tables ─────────────────────────
def tidy_volume(df):
    if "Volume" in df.columns:
        df = df.copy()
        df["Volume"] = df["Volume"].fillna(0).astype(int)
    return df

# ─────────────────────────── chart helpers ───────────────────────────
def plot_candles(ax, df):
    d = df.reset_index()
    d["num"] = d["Date"].map(mdates.date2num)
    candlestick_ohlc(ax, d[["num","Open","High","Low","Close"]].values,
                    width=.6, colorup="g", colordown="r")
    ax.xaxis_date(); ax.set_xlabel("Date"); ax.set_ylabel("Price")

def plot_series(sym, df, ctype, opts, ctx):
    if not ctx.ax:
        ctx.fig, ctx.ax = plt.subplots(
            figsize=(ctx.opts["width"], ctx.opts["height"]))
    plotters = {
        "candlestick": plot_candles,
        "line":        lambda ax, d: d["Close"].plot(ax=ax),
        "bar":         lambda ax, d: d["Close"].plot.bar(ax=ax),
        "ohlc":        lambda ax, d: d["Close"].plot(ax=ax)
    }
    if ctype not in plotters:
        raise CFError(f"Unknown chart type '{ctype}'")
    plotters[ctype](ctx.ax, df)
    if "sma" in opts:
        p = int(opts["sma"])
        df["Close"].rolling(p).mean().plot(ax=ctx.ax, linestyle="--",
            label=f"SMA {p}")
        ctx.ax.legend()
    ctx.ax.set_title(opts.get("title", f"{sym} – {ctype}"))
    ctx.ax.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
    plt.setp(ctx.ax.get_xticklabels(), rotation=45)
    ctx.ax.grid(ctx.opts["grid"])

# ─────────────────────────── core eval ──────────────────────────
def run(model):
    env = {"sma": lambda s,p: s.rolling(p).mean()}
    ctx = ChartCtx()

    for st in model.statements:
        name = st.__class__.__name__

        if name == "LetStmt":
            env[st.name] = eval_expr(st.expr, env)
            continue

        if name == "ClearStmt":
            # drop vars, or reset to only built‑ins
            if st.vars:
                for v in st.vars:
                    env.pop(v, None)
            else:
                env = {k:v for k,v in env.items() if callable(v)}
            # ensure any open charts get closed
            plt.close("all")
            ctx.reset()
            continue

        tickers = asset_list(st.asset, env)
        start, end = parse_date(st.date)

        if name == "ShowStmt":
            for sym in tickers:
                raw = yf.download(sym,
                                start=pd.Timestamp(start).tz_localize("America/New_York"),
                                end  =pd.Timestamp(end).tz_localize("America/New_York") + pd.Timedelta(days=1),
                                progress=False, auto_adjust=False)
                if raw.empty:
                    print(f"{sym}: no data ({start} → {end})")
                    continue
                df = tidy_volume(raw)
                if hasattr(df.columns, 'nlevels') and df.columns.nlevels > 1:
                    df.columns = df.columns.get_level_values(0)
                cols = [c for c in ['Open','High','Low','Close','Adj Close','Volume'] if c in df.columns]
                out = df[cols].copy()
                out.index = out.index.strftime("%Y-%m-%d")
                out.index.name = "Date"
                for c in out.columns:
                    if c != 'Volume':
                        out[c] = out[c].map(lambda v: f"{v:.2f}")
                    else:
                        out[c] = out[c].map(lambda v: f"{v:,}")
                print(f"\n=== {sym} ({start} → {end}) ===")
                print(tabulate(out, headers="keys", tablefmt="github"))
            continue

        if name == "ChartStmt":
            ctype   = getattr(st, "charttype", "line") or "line"
            options = {o.key: eval_expr(o.value, env) for o in getattr(st, "options", [])}
            ctx.apply(options)
            for sym in tickers:
                df = yf.download(sym,
                                    start=pd.Timestamp(start),
                                    end  =pd.Timestamp(end) + pd.Timedelta(days=1),
                                    progress=False, auto_adjust=False)
                if df.empty:
                    raise CFError(f"No data for {sym}")
                plot_series(sym, df, ctype, options, ctx)
            if ctx.fig:
                plt.tight_layout()
                plt.show()
                ctx.reset()
            continue

        raise CFError(f"Unhandled statement {name}")


if __name__ == "__main__":
    import argparse, sys
    from pathlib import Path
    from textx import metamodel_from_file

    ap = argparse.ArgumentParser(description="ChartFlow interpreter")
    ap.add_argument("file", help="*.cf program file")
    ns = ap.parse_args()

    # locate the bundled grammar
    grammar = Path(__file__).parent.parent / "grammar" / "chartFlow.tx"
    try:
        mm    = metamodel_from_file(grammar)
        model = mm.model_from_file(Path(ns.file))   # this is your model object
        run(model)                                  # pass the model, not ns.file
    except CFError as e:
        print("ChartFlow error:", e)
        sys.exit(1)
    except Exception as e:
        print("Internal error:", e)
        sys.exit(2)
