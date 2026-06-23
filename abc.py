import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import io

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Excel Data Analyser",
    page_icon="📊",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .stApp { background: #0f1117; color: #e8eaf0; }

    .hero {
        background: linear-gradient(135deg, #1a1f2e 0%, #151b2d 100%);
        border: 1px solid #2a3150;
        border-radius: 16px;
        padding: 2.5rem 2rem 2rem;
        margin-bottom: 2rem;
        text-align: center;
    }
    .hero h1 { font-size: 2.4rem; font-weight: 700; color: #7c9fff; margin: 0 0 .4rem; letter-spacing: -1px; }
    .hero p  { color: #8892b0; font-size: 1rem; margin: 0; }

    .stat-card {
        background: #151b2d;
        border: 1px solid #2a3150;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1rem;
    }
    .stat-card h4 { margin: 0 0 .6rem; color: #7c9fff; font-size: .85rem; text-transform: uppercase; letter-spacing: 1px; }
    .stat-card .val { font-family: 'JetBrains Mono', monospace; font-size: 1.4rem; font-weight: 600; color: #e8eaf0; }
    .stat-card .sub { font-size: .8rem; color: #8892b0; margin-top: .25rem; }

    .verdict-good {
        background: linear-gradient(135deg, #0d2818, #0a3020);
        border: 1px solid #2ecc71;
        border-radius: 10px;
        padding: .9rem 1.2rem;
        color: #2ecc71;
        font-weight: 600;
        font-size: .95rem;
        margin-top: .8rem;
    }
    .verdict-warn {
        background: linear-gradient(135deg, #1f1a0a, #281e08);
        border: 1px solid #f39c12;
        border-radius: 10px;
        padding: .9rem 1.2rem;
        color: #f39c12;
        font-weight: 600;
        font-size: .95rem;
        margin-top: .8rem;
    }

    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #e8eaf0;
        margin: 2rem 0 1rem;
        border-left: 4px solid #7c9fff;
        padding-left: .8rem;
    }

    div[data-testid="stFileUploader"] {
        background: #151b2d;
        border: 2px dashed #2a3150;
        border-radius: 12px;
        padding: 1.5rem;
    }
    div[data-testid="stFileUploader"]:hover { border-color: #7c9fff; }
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>📊 Excel Data Analyser</h1>
    <p>Upload an Excel file · Explore distributions · Check forecasting readiness</p>
</div>
""", unsafe_allow_html=True)

# ── Upload ────────────────────────────────────────────────────────────────────
uploaded = st.file_uploader("Upload your Excel file (.xlsx or .xls)", type=["xlsx", "xls"])

if uploaded is None:
    st.info("👆 Upload an Excel file above to get started.")
    st.stop()

# ── Load data ─────────────────────────────────────────────────────────────────
try:
    df = pd.read_excel(uploaded)
except Exception as e:
    st.error(f"Could not read file: {e}")
    st.stop()

st.markdown(f"<div class='section-title'>Preview — {uploaded.name}</div>", unsafe_allow_html=True)
st.dataframe(df.head(10), use_container_width=True)
st.caption(f"{df.shape[0]:,} rows · {df.shape[1]} columns")

# ── Filter numeric columns ────────────────────────────────────────────────────
num_cols = df.select_dtypes(include=[np.number]).columns.tolist()

if not num_cols:
    st.warning("No numerical columns found in this file.")
    st.stop()

st.markdown(f"<div class='section-title'>Numerical Columns Found ({len(num_cols)})</div>", unsafe_allow_html=True)
st.write(", ".join([f"`{c}`" for c in num_cols]))

# ── Threshold slider ──────────────────────────────────────────────────────────
threshold_pct = st.slider(
    "Mean–Median similarity threshold (%)",
    min_value=1, max_value=20, value=5,
    help="If |mean − median| / mean < threshold, data is considered suitable for forecasting."
)

# ── Analysis + Histograms ─────────────────────────────────────────────────────
st.markdown("<div class='section-title'>Column Analysis & Histograms</div>", unsafe_allow_html=True)

COLS_PER_ROW = 2
rows = [num_cols[i:i+COLS_PER_ROW] for i in range(0, len(num_cols), COLS_PER_ROW)]

for row in rows:
    grid = st.columns(COLS_PER_ROW)
    for col_idx, col in enumerate(row):
        series = df[col].dropna()
        mean   = series.mean()
        median = series.median()
        std    = series.std()
        skew   = series.skew()

        # Determine forecasting verdict
        if abs(mean) > 1e-9:
            diff_pct = abs(mean - median) / abs(mean) * 100
        else:
            diff_pct = abs(mean - median) * 100

        suitable = diff_pct <= threshold_pct

        with grid[col_idx]:
            # Stat cards
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""
                <div class='stat-card'>
                    <h4>Mean</h4>
                    <div class='val'>{mean:,.3f}</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class='stat-card'>
                    <h4>Median</h4>
                    <div class='val'>{median:,.3f}</div>
                </div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div class='stat-card'>
                    <h4>Std Dev</h4>
                    <div class='val'>{std:,.3f}</div>
                </div>""", unsafe_allow_html=True)

            # Verdict
            if suitable:
                st.markdown(f"""
                <div class='verdict-good'>
                    ✅ <strong>{col}</strong> — Mean ≈ Median (diff {diff_pct:.1f}%) · <em>Suitable for forecasting</em>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class='verdict-warn'>
                    ⚠️ <strong>{col}</strong> — Mean ≠ Median (diff {diff_pct:.1f}%) · <em>Data may be skewed (skew={skew:.2f}); review before forecasting</em>
                </div>""", unsafe_allow_html=True)

            # Histogram
            fig, ax = plt.subplots(figsize=(6, 3.2))
            fig.patch.set_facecolor("#151b2d")
            ax.set_facecolor("#0f1117")

            n, bins, patches = ax.hist(series, bins=30, color="#7c9fff", edgecolor="#0f1117", linewidth=0.4, alpha=0.85)
            ax.axvline(mean,   color="#2ecc71", linewidth=1.8, linestyle="--", label=f"Mean {mean:,.2f}")
            ax.axvline(median, color="#e74c3c", linewidth=1.8, linestyle=":",  label=f"Median {median:,.2f}")

            ax.set_title(col, color="#e8eaf0", fontsize=11, fontweight="bold", pad=8)
            ax.set_xlabel("Value", color="#8892b0", fontsize=9)
            ax.set_ylabel("Frequency", color="#8892b0", fontsize=9)
            ax.tick_params(colors="#8892b0", labelsize=8)
            for spine in ax.spines.values():
                spine.set_edgecolor("#2a3150")
            ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
            ax.legend(fontsize=8, facecolor="#1a1f2e", edgecolor="#2a3150", labelcolor="#e8eaf0")
            fig.tight_layout()

            st.pyplot(fig)
            plt.close(fig)

# ── Summary table ─────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>Summary Table</div>", unsafe_allow_html=True)

records = []
for col in num_cols:
    s = df[col].dropna()
    mean   = s.mean()
    median = s.median()
    std    = s.std()
    skew   = s.skew()
    diff_pct = abs(mean - median) / abs(mean) * 100 if abs(mean) > 1e-9 else abs(mean - median) * 100
    records.append({
        "Column":       col,
        "Count":        len(s),
        "Mean":         round(mean,   4),
        "Median":       round(median, 4),
        "Std Dev":      round(std,    4),
        "Skewness":     round(skew,   4),
        "Mean≈Median Diff %": round(diff_pct, 2),
        "Forecast Ready": "✅ Yes" if diff_pct <= threshold_pct else "⚠️ Review",
    })

summary_df = pd.DataFrame(records)
st.dataframe(summary_df, use_container_width=True)

# ── Download summary ──────────────────────────────────────────────────────────
buf = io.BytesIO()
with pd.ExcelWriter(buf, engine="openpyxl") as writer:
    summary_df.to_excel(writer, index=False, sheet_name="Summary")
buf.seek(0)

st.download_button(
    label="⬇️ Download Summary as Excel",
    data=buf,
    file_name="analysis_summary.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.caption("Built with Streamlit · Analyse → Visualise → Forecast")
