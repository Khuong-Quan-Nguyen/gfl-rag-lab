"""gfl-rag-lab ops console: health numbers, trace waterfall, evals and asks on one screen.

Run:  streamlit run dashboard/app.py      (API: uvicorn app.service:app --port 8000)
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

import altair as alt
import pandas as pd
import psycopg
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import settings  # noqa: E402

# Validated (OKLCH band, chroma, protan/deutan dE >= 13.6, contrast 5.8:1) on SURFACE.
TEAL, AMBER = "#1aa395", "#c4851c"
SURFACE, INK, INK_2, MUTED, GRID = "#11161a", "#e6ebee", "#a9b4bb", "#6f7c84", "#222b31"
TYPE_COLORS = alt.Scale(domain=["conceptual", "exact"], range=[TEAL, AMBER])
MODES = ["vector", "hybrid", "vector_rerank", "hybrid_rerank"]
STEPS = [("embed_ms", "embed"), ("retrieve_ms", "retrieve"), ("rerank_ms", "rerank"), ("llm_ms", "LLM")]

st.set_page_config(page_title="GFL RAG Ops", page_icon="♻", layout="wide")
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;700&display=swap');
html, body, [class*="css"], .stMarkdown, p, label {{ font-family: 'Space Grotesk', sans-serif; }}
h1, h2, h3 {{ font-family: 'Space Grotesk', sans-serif; letter-spacing: -0.01em; }}
code, .mono, [data-testid="stDataFrame"] {{ font-family: 'IBM Plex Mono', monospace; }}
.tile {{ background:{SURFACE}; border:1px solid {GRID}; border-radius:10px; padding:14px 16px; height:100%; }}
.tile .k {{ color:{MUTED}; font-size:0.78rem; text-transform:uppercase; letter-spacing:0.08em; }}
.tile .v {{ color:{INK}; font-family:'IBM Plex Mono', monospace; font-size:1.9rem; font-weight:500; line-height:1.2; }}
.tile .s {{ color:{INK_2}; font-size:0.8rem; }}
.badge {{ font-family:'IBM Plex Mono', monospace; font-size:0.78rem; padding:2px 8px; border-radius:6px;
          border:1px solid {GRID}; color:{INK_2}; margin-right:6px; }}
.cite {{ border-left:3px solid {TEAL}; padding:4px 10px; margin:6px 0; color:{INK_2}; font-size:0.85rem; }}
</style>""", unsafe_allow_html=True)


def _base(chart: alt.Chart) -> alt.Chart:
    return (chart.configure(background="transparent")
            .configure_view(stroke=None)
            .configure_axis(labelColor=INK_2, titleColor=MUTED, gridColor=GRID, domainColor=GRID, tickColor=GRID,
                            labelFont="IBM Plex Mono", titleFont="Space Grotesk")
            .configure_legend(labelColor=INK_2, titleColor=MUTED, labelFont="Space Grotesk", orient="top",
                              columnPadding=20, labelLimit=0, symbolType="square"))


def tile(label: str, value: str, sub: str = "") -> str:
    return f'<div class="tile"><div class="k">{label}</div><div class="v">{value}</div><div class="s">{sub}</div></div>'


# ---------- data access ----------
@st.cache_data(ttl=10)
def query_traces(hours: int) -> pd.DataFrame:
    sql = ("SELECT trace_id::text, ts, mode, question, embed_ms, retrieve_ms, rerank_ms, llm_ms, total_ms, "
           "top_score, n_chunks, tokens_in, tokens_out, cost_usd, abstained, status, error "
           "FROM traces WHERE ts > now() - make_interval(hours => %s) ORDER BY ts DESC")
    try:
        with psycopg.connect(settings.pg_dsn) as c:
            cur = c.execute(sql, (hours,))
            cols = [d.name for d in cur.description]
            return pd.DataFrame(cur.fetchall(), columns=cols)
    except Exception as e:  # noqa: BLE001
        st.error(f"Postgres unreachable at {settings.pg_dsn.split('@')[-1]}: {e}")
        return pd.DataFrame()


def api(path: str, body: dict | None = None, timeout: float = 120) -> dict | None:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{settings.api_url}{path}", data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except OSError:
        return None


def eval_runs() -> list[Path]:
    return sorted((p for p in settings.results_dir.glob("*.json") if p.stem[:2] == "20"), reverse=True)


def waterfall(row: dict, height: int = 200) -> alt.Chart:
    """Sequential step spans: embed -> retrieve -> rerank -> LLM."""
    spans, t = [], 0.0
    for key, name in STEPS:
        d = float(row.get(key) or 0.0)
        spans.append({"step": name, "start": t, "end": t + d, "ms": d})
        t += d
    df = pd.DataFrame(spans)
    bars = alt.Chart(df).mark_bar(color=TEAL, cornerRadius=4, height=18).encode(
        y=alt.Y("step:N", sort=[s for _, s in STEPS], title=None,
                axis=alt.Axis(labelOverlap=False, labelLimit=0, labelPadding=8, labelFont="Space Grotesk")),
        x=alt.X("start:Q", title="ms since request start"), x2="end:Q",
        tooltip=[alt.Tooltip("step:N"), alt.Tooltip("ms:Q", format=",.0f", title="duration ms"),
                 alt.Tooltip("start:Q", format=",.0f", title="starts at ms")])
    labels = alt.Chart(df).mark_text(align="left", dx=6, color=INK_2, font="IBM Plex Mono", fontSize=11).encode(
        y=alt.Y("step:N", sort=[s for _, s in STEPS]), x="end:Q", text=alt.Text("ms:Q", format=",.0f"))
    return _base((bars + labels).properties(height=height, padding={"left": 8, "right": 40}))


# ---------- header ----------
health = api("/health", timeout=3)
h1, h2 = st.columns([1, 1])
h1.markdown("## ♻ GFL RAG · ops console")
h1.caption("GFL 2024 Sustainability Report + 2024 Annual Report · pgvector HNSW + Postgres FTS · MiniLM · Claude")
if health:
    llm = "LLM on" if health["llm_enabled"] else "LLM off · no key"
    h2.markdown(f'<div style="text-align:right;padding-top:18px">'
                f'<span class="badge">● API up</span><span class="badge">models loaded in {health["startup_s"]}s</span>'
                f'<span class="badge">{llm}</span><span class="badge">abstain &lt; {health["abstain_threshold"]}</span></div>',
                unsafe_allow_html=True)
else:
    h2.warning(f"API not reachable at {settings.api_url}. Start it: `uvicorn app.service:app --port 8000`")

# ---------- filters (one row) ----------
f1, f2, _ = st.columns([1, 2, 3])
window = f1.selectbox("Window", ["24 hours", "7 days", "30 days"], index=1)
hours = {"24 hours": 24, "7 days": 168, "30 days": 720}[window]
traces = query_traces(hours)
mode_filter = f2.multiselect("Modes", MODES, default=MODES)
if not traces.empty:
    traces = traces[traces["mode"].isin(mode_filter)]

# ---------- the four numbers ----------
st.markdown("#### The four numbers")
c1, c2, c3, c4 = st.columns(4)
if traces.empty:
    for c, k in zip((c1, c2, c3, c4), ("p50 / p99 latency", "tokens / request", "cost / day", "error rate")):
        c.markdown(tile(k, "—", "no traffic in window"), unsafe_allow_html=True)
else:
    p50, p99 = traces["total_ms"].quantile(0.5), traces["total_ms"].quantile(0.99)
    llm_rows = traces[(traces["tokens_in"].fillna(0) + traces["tokens_out"].fillna(0)) > 0]
    tok = (llm_rows["tokens_in"] + llm_rows["tokens_out"]).mean() if not llm_rows.empty else 0
    daily = traces.assign(day=pd.to_datetime(traces["ts"]).dt.date).groupby("day")["cost_usd"].sum()
    err = (traces["status"] == "error").mean()
    c1.markdown(tile("p50 / p99 latency", f"{p50:,.0f} / {p99:,.0f}", f"ms · {len(traces)} requests"),
                unsafe_allow_html=True)
    c2.markdown(tile("tokens / request", f"{tok:,.0f}", f"{len(llm_rows)} requests reached the LLM"),
                unsafe_allow_html=True)
    c3.markdown(tile("cost / day", f"${daily.mean():,.4f}", f"avg over {len(daily)} day(s) · {settings.claude_model}"),
                unsafe_allow_html=True)
    c4.markdown(tile("error rate", f"{err:.1%}", f"abstained {traces['abstained'].fillna(False).mean():.0%} of requests"),
                unsafe_allow_html=True)

# ---------- evals + latency ----------
st.markdown("#### Retrieval evals · mode × question type")
runs = eval_runs()
if not runs:
    st.info("No eval runs yet. Run `python -m evals.run_evals`.")
else:
    e1, e2 = st.columns([3, 2])
    run_path = e1.selectbox("Eval run", runs, format_func=lambda p: p.stem.replace("T", " "), label_visibility="collapsed")
    result = json.loads(run_path.read_text(encoding="utf-8"))
    k = result["k"]
    rows = [{"mode": m, "type": t, f"recall@{k}": v[t][f"recall@{k}"], "top-1": v[t]["top1"], "MRR": v[t]["mrr"]}
            for m, v in result["table"].items() for t in ("conceptual", "exact", "all")]
    df = pd.DataFrame(rows)
    left, right = st.columns([3, 2])
    bar_df = df[df["type"] != "all"]
    bars = alt.Chart(bar_df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, width=22).encode(
        x=alt.X("mode:N", sort=MODES, title=None, axis=alt.Axis(labelAngle=0)),
        xOffset=alt.XOffset("type:N", sort=["conceptual", "exact"], scale=alt.Scale(paddingInner=0.08)),
        y=alt.Y("MRR:Q", scale=alt.Scale(domain=[0, 1]), title="MRR"),
        color=alt.Color("type:N", scale=TYPE_COLORS, title="question type"),
        tooltip=["mode", "type", alt.Tooltip("MRR:Q", format=".3f"), alt.Tooltip(f"recall@{k}:Q", format=".3f"),
                 alt.Tooltip("top-1:Q", format=".3f")])
    best = bar_df.loc[bar_df.groupby("type")["MRR"].idxmax()]
    lbl = alt.Chart(best).mark_text(dy=-8, color=INK, font="IBM Plex Mono", fontSize=11).encode(
        x=alt.X("mode:N", sort=MODES), xOffset=alt.XOffset("type:N", sort=["conceptual", "exact"]),
        y="MRR:Q", text=alt.Text("MRR:Q", format=".3f"))
    left.altair_chart(_base((bars + lbl).properties(height=290, title=alt.TitleParams(
        f"MRR by mode · {result['n_questions']} questions, ±{result['page_tolerance']} page", color=INK_2,
        font="Space Grotesk", anchor="start"))), use_container_width=True)
    right.dataframe(df.style.format({f"recall@{k}": "{:.3f}", "top-1": "{:.3f}", "MRR": "{:.3f}"}),
                    hide_index=True, use_container_width=True, height=290)

lat_path = settings.results_dir / "latency_demo.json"
if lat_path.exists():
    lat = json.loads(lat_path.read_text(encoding="utf-8"))
    l1, l2, l3 = st.columns(3)
    l1.markdown(tile("p50 · model reloaded per query", f"{lat['p50_cold_ms']:,.0f} ms", "fresh process each query (the 7 s bug)"),
                unsafe_allow_html=True)
    l2.markdown(tile("p50 · long-lived service", f"{lat['p50_warm_ms']:,.0f} ms", f"models loaded once · {lat['mode']}"),
                unsafe_allow_html=True)
    l3.markdown(tile("speed-up", f"{lat['p50_cold_ms'] / lat['p50_warm_ms']:.1f}×", "same 10 eval questions"),
                unsafe_allow_html=True)

# ---------- trace waterfall + low confidence ----------
st.markdown("#### Traces")
t1, t2 = st.columns([3, 2])
if traces.empty:
    t1.info("No traces yet. Ask something below, or run `python -m scripts.seed_traffic`.")
else:
    recent = traces.head(200)
    pick = t1.selectbox("Trace", recent.index, format_func=lambda i: (
        f"{pd.to_datetime(recent.at[i, 'ts']):%H:%M:%S} · {recent.at[i, 'mode']} · {recent.at[i, 'question'][:60]}"))
    row = recent.loc[pick].to_dict()
    t1.altair_chart(waterfall(row), use_container_width=True)
    t1.caption(f"trace {row['trace_id']} · status {row['status']} · top_score {row['top_score']:.3f} · "
               f"{int(row['tokens_in'] or 0)}+{int(row['tokens_out'] or 0)} tokens")
    t2.markdown("**Low-confidence feed** · lowest top_score")
    low = traces.nsmallest(12, "top_score")[["top_score", "abstained", "mode", "question"]]
    t2.dataframe(low.style.format({"top_score": "{:.3f}"}), hide_index=True, use_container_width=True, height=300)

# ---------- ask box ----------
st.markdown("#### Ask")
with st.form("ask"):
    a1, a2 = st.columns([4, 1])
    q = a1.text_input("Question", placeholder="How many homes can the Central Missouri RNG facility power?")
    mode = a2.selectbox("Mode", MODES, index=3)
    go = st.form_submit_button("Ask")
if go and q.strip():
    with st.spinner("retrieving…"):
        r = api("/ask", {"question": q, "mode": mode})
    if r is None:
        st.error("API call failed - is the service running?")
    else:
        badge = "abstained" if r["abstained"] else r["status"]
        st.markdown(f'<span class="badge">{badge}</span><span class="badge">top_score {r["top_score"]:.3f}</span>'
                    f'<span class="badge">{r["timings"]["total_ms"]:,.0f} ms</span>', unsafe_allow_html=True)
        st.markdown(r["answer"])
        for c in r["citations"]:
            st.markdown(f'<div class="cite"><b class="mono">[{c["doc"]} p.{c["page"]}]</b> '
                        f'sim {c["similarity"]:.3f} · {c["snippet"]}…</div>', unsafe_allow_html=True)
        st.altair_chart(waterfall(r["timings"], height=170), use_container_width=True)
        query_traces.clear()
