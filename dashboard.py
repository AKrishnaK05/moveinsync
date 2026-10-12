"""
MoveInSync Play Store Review Intelligence Platform
Real-Time Telemetry & Root-Cause Engineering Diagnostics
Branded with the Official MoveInSync App Identity (Iconic Emerald Green #16A34A / #22C55E)

Run with:
    streamlit run dashboard.py
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# -----------------------------------------------------------------------------
# Page Configuration & MoveInSync App Theme
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="MoveInSync | Review Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
)

MOVEINSYNC_APP_THEME = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: #0f172a;
    }

    /* MoveInSync Brand Header */
    .mis-header {
        background: #0f172a;
        border-radius: 12px;
        padding: 1.75rem 2rem;
        margin-bottom: 1.75rem;
        color: #ffffff;
        box-shadow: 0 4px 20px rgba(15, 23, 42, 0.12);
        position: relative;
        overflow: hidden;
        border: 1px solid #1e293b;
    }
    .mis-header::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #22c55e 0%, #16a34a 60%, #15803d 100%);
    }
    .mis-badge-logo {
        display: inline-flex;
        align-items: center;
        background: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.35);
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.6rem;
    }
    .mis-dot {
        width: 8px;
        height: 8px;
        background-color: #22c55e;
        border-radius: 50%;
        display: inline-block;
        margin-right: 0.45rem;
        box-shadow: 0 0 8px #22c55e;
    }
    .mis-title {
        font-size: 1.85rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        margin: 0;
        color: #ffffff;
    }
    .mis-subtitle {
        font-size: 0.95rem;
        color: #94a3b8;
        margin-top: 0.35rem;
        font-weight: 400;
    }

    /* MoveInSync Metric Cards */
    .mis-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.15rem 1.25rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        position: relative;
        overflow: hidden;
        transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
    }
    .mis-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(22, 163, 74, 0.08);
        border-color: #cbd5e1;
    }
    .mis-card-stripe {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
    }
    .stripe-green { background: #16a34a; }
    .stripe-emerald { background: #10b981; }
    .stripe-blue { background: #0284c7; }
    .stripe-red { background: #ef4444; }
    .stripe-amber { background: #f59e0b; }

    .mis-card-label {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #475569;
        margin-bottom: 0.4rem;
    }
    .mis-card-value {
        font-size: 1.75rem;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.02em;
        line-height: 1.15;
    }
    .mis-card-sub {
        font-size: 0.78rem;
        margin-top: 0.35rem;
        color: #64748b;
        font-weight: 500;
    }
    .sub-green { color: #16a34a; font-weight: 600; }
    .sub-red { color: #dc2626; font-weight: 600; }

    /* MoveInSync Badges */
    .mis-badge {
        display: inline-block;
        padding: 0.22rem 0.55rem;
        font-size: 0.72rem;
        font-weight: 700;
        border-radius: 4px;
        letter-spacing: 0.03em;
    }
    .badge-mis-green {
        background: #f0fdf4;
        color: #166534;
        border: 1px solid #bbf7d0;
    }
    .badge-mis-red {
        background: #fef2f2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }
    .badge-mis-neutral {
        background: #f8fafc;
        color: #334155;
        border: 1px solid #e2e8f0;
    }

    /* Review Cards */
    .mis-review-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #16a34a;
        border-radius: 8px;
        padding: 1.1rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .review-neg {
        border-left-color: #ef4444;
    }
    .review-pos {
        border-left-color: #16a34a;
    }
    .mis-quote {
        font-size: 0.9rem;
        color: #0f172a;
        line-height: 1.5;
        font-style: italic;
        margin: 0.5rem 0;
    }
    .mis-meta {
        font-size: 0.75rem;
        color: #64748b;
        font-weight: 500;
    }

    /* Dark Mode Adaptability */
    @media (prefers-color-scheme: dark) {
        .mis-card {
            background: #1e293b !important;
            border-color: #334155 !important;
        }
        .mis-card-value {
            color: #f8fafc !important;
        }
        .mis-card-label {
            color: #94a3b8 !important;
        }
        .mis-card-sub {
            color: #cbd5e1 !important;
        }
        .mis-review-card {
            background: #1e293b !important;
            border-color: #334155 !important;
        }
        .mis-quote {
            color: #f1f5f9 !important;
        }
        .mis-meta {
            color: #94a3b8 !important;
        }
    }

    .stButton>button {
        background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        letter-spacing: 0.02em;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
        box-shadow: 0 4px 12px rgba(22, 163, 74, 0.25);
    }

    /* MoveInSync Green Multiselect Pills */
    span[data-baseweb="tag"] {
        background-color: #f0fdf4 !important;
        border: 1px solid #bbf7d0 !important;
        border-radius: 4px !important;
    }
    span[data-baseweb="tag"] span {
        color: #166534 !important;
        font-weight: 600 !important;
        font-size: 0.78rem !important;
    }
    span[data-baseweb="tag"] svg {
        fill: #166534 !important;
    }

    /* MoveInSync Active Tab Highlight */
    button[data-baseweb="tab"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #16a34a !important;
        border-bottom-color: #16a34a !important;
    }
</style>
"""
st.markdown(MOVEINSYNC_APP_THEME, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
DATA_PROCESSED_PATH = Path("data/processed/moveinsync_reviews_2025_2026.csv")
DATA_LABELED_PATH = Path("data/labeled/moveinsync_reviews_2025_2026_labels.jsonl")
MATRIX_CSV_PATH = Path("outputs/reports/action_plan_priority_matrix.csv")

# -----------------------------------------------------------------------------
# Real-Time Data Ingestion & Cache Management
# -----------------------------------------------------------------------------
def get_dataset_mtime_signature() -> tuple[float, float, float, str]:
    """Returns file modification timestamps to invalidate cache automatically when files change on disk."""
    p_mtime = DATA_PROCESSED_PATH.stat().st_mtime if DATA_PROCESSED_PATH.exists() else 0.0
    l_mtime = DATA_LABELED_PATH.stat().st_mtime if DATA_LABELED_PATH.exists() else 0.0
    m_mtime = MATRIX_CSV_PATH.stat().st_mtime if MATRIX_CSV_PATH.exists() else 0.0
    latest_ts = max(p_mtime, l_mtime, m_mtime)
    formatted = (
        datetime.datetime.fromtimestamp(latest_ts).strftime("%Y-%m-%d %H:%M:%S")
        if latest_ts > 0
        else "N/A"
    )
    return (p_mtime, l_mtime, m_mtime, formatted)


@st.cache_data(ttl=30, show_spinner="Synchronizing MoveInSync review datasets...")
def load_review_data(cache_signature: tuple) -> pd.DataFrame:
    """Loads CSV reviews and labeled JSONL, automatically invalidating when files on disk change."""
    if not DATA_PROCESSED_PATH.exists() or not DATA_LABELED_PATH.exists():
        return pd.DataFrame()

    df_meta = pd.read_csv(DATA_PROCESSED_PATH)
    df_meta["at"] = pd.to_datetime(df_meta["at"], errors="coerce")
    df_meta["date"] = df_meta["at"].dt.date
    df_meta["year_month"] = df_meta["at"].dt.strftime("%Y-%m")

    labels_records: List[Dict[str, Any]] = []
    with open(DATA_LABELED_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                labels_records.append(
                    {
                        "reviewId": rec.get("review_id"),
                        "primary_label": rec.get("primary_label", "UNCATEGORIZED"),
                        "all_labels": rec.get("labels", []),
                        "sentiment": rec.get("sentiment", "unspecified"),
                        "issue_type": rec.get("issue_type", "OTHER"),
                        "confidence": rec.get("confidence", 3),
                        "evidence": rec.get("evidence", []),
                    }
                )
            except Exception:
                continue

    df_labels = pd.DataFrame(labels_records)
    if df_labels.empty:
        return pd.DataFrame()

    merged = pd.merge(df_meta, df_labels, on="reviewId", how="inner")
    merged["has_reply"] = (
        merged["replyContent"].notna() & (merged["replyContent"].astype(str).str.strip() != "")
    )
    merged["reviewCreatedVersion"] = merged["reviewCreatedVersion"].fillna("Unknown").astype(str)
    return merged


@st.cache_data(ttl=30)
def load_priority_matrix(cache_mtime: float) -> pd.DataFrame:
    if MATRIX_CSV_PATH.exists():
        return pd.read_csv(MATRIX_CSV_PATH)
    return pd.DataFrame()


# -----------------------------------------------------------------------------
# Main Application
# -----------------------------------------------------------------------------
def main():
    # Branded Header (MoveInSync App Theme)
    st.markdown(
        """
        <div class="mis-header">
            <span class="mis-badge-logo">
                <span class="mis-dot"></span>MoveInSync ETS &bull; Official Play Store: 4.6&#9733; &bull; Telemetry Hub
            </span>
            <div class="mis-title">Play Store Customer Telemetry & Action Hub</div>
            <div class="mis-subtitle">Empirical ratings tracking, root-cause diagnostics, and Day-1 engineering resolution matrix</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    p_mtime, l_mtime, m_mtime, last_disk_update = get_dataset_mtime_signature()
    df = load_review_data((p_mtime, l_mtime))
    if df.empty:
        st.error(
            f"Required data assets not found in {DATA_PROCESSED_PATH} or {DATA_LABELED_PATH}. "
            "Ensure data pipeline steps 01-05 have completed."
        )
        return

    # -------------------------------------------------------------------------
    # Sidebar Filters & Telemetry Sync
    # -------------------------------------------------------------------------
    st.sidebar.markdown(
        """
        <div style="padding: 0.5rem 0 1rem 0;">
            <div style="font-weight: 800; font-size: 1.15rem; color: #16a34a; letter-spacing: -0.02em;">MoveInSync</div>
            <div style="font-size: 0.78rem; color: #64748b;">Enterprise Commute Platform</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Real-Time Telemetry Status & Manual Sync
    sync_ts = datetime.datetime.now().strftime("%H:%M:%S")
    st.sidebar.caption(
        f"**Live Pipeline Reactive** &bull; Active\n\n"
        f"Last Synced: `{sync_ts}`\n\n"
        f"On-Disk Data Updated: `{last_disk_update}`"
    )
    if st.sidebar.button("Sync Data & Clear Cache", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Operational Filters**")

    # Date Window
    min_date = df["date"].min()
    max_date = df["date"].max()
    date_range = st.sidebar.date_input(
        "Date Window",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    # Star Rating Tier
    selected_stars = st.sidebar.multiselect(
        "Rating Tier",
        options=[1, 2, 3, 4, 5],
        default=[1, 2, 3, 4, 5],
        format_func=lambda s: f"{s} Star{'s' if s > 1 else ''}",
    )

    # Issue Category
    all_categories = sorted(df["primary_label"].dropna().unique().tolist())
    selected_categories = st.sidebar.multiselect(
        "Category",
        options=all_categories,
        default=all_categories,
    )

    # Sentiment Filter
    sentiments = sorted(df["sentiment"].dropna().unique().tolist())
    selected_sentiments = st.sidebar.multiselect(
        "Sentiment",
        options=sentiments,
        default=sentiments,
        format_func=lambda s: s.capitalize(),
    )

    # Developer Response
    reply_filter = st.sidebar.selectbox(
        "Support Engagement",
        options=["All Reviews", "Replied Only", "Unaddressed Only"],
        index=0,
    )

    # Application Release Version
    top_versions = df["reviewCreatedVersion"].value_counts().head(10).index.tolist()
    if "Unknown" not in top_versions and "Unknown" in df["reviewCreatedVersion"].values:
        top_versions.append("Unknown")
    version_options = ["All Releases"] + top_versions
    selected_version = st.sidebar.selectbox("App Release Version", options=version_options, index=0)

    # Search Query
    search_query = st.sidebar.text_input("Review Keyword Search", placeholder="e.g. crash, otp, route, driver")

    # -------------------------------------------------------------------------
    # Apply Slicing
    # -------------------------------------------------------------------------
    filtered_df = df.copy()

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_d, end_d = date_range
        filtered_df = filtered_df[(filtered_df["date"] >= start_d) & (filtered_df["date"] <= end_d)]

    if selected_stars:
        filtered_df = filtered_df[filtered_df["score"].isin(selected_stars)]

    if selected_sentiments:
        filtered_df = filtered_df[filtered_df["sentiment"].isin(selected_sentiments)]

    if selected_categories:
        filtered_df = filtered_df[filtered_df["primary_label"].isin(selected_categories)]

    if reply_filter == "Replied Only":
        filtered_df = filtered_df[filtered_df["has_reply"] == True]
    elif reply_filter == "Unaddressed Only":
        filtered_df = filtered_df[filtered_df["has_reply"] == False]

    if selected_version != "All Releases":
        filtered_df = filtered_df[filtered_df["reviewCreatedVersion"] == selected_version]

    if search_query.strip():
        q = search_query.strip().lower()
        filtered_df = filtered_df[filtered_df["content"].fillna("").str.lower().str.contains(q, regex=False)]

    # -------------------------------------------------------------------------
    # MoveInSync Key Metric Cards
    # -------------------------------------------------------------------------
    total_reviews = len(filtered_df)
    avg_score = filtered_df["score"].mean() if total_reviews > 0 else 0.0
    positive_count = len(filtered_df[filtered_df["score"].isin([4, 5])])
    negative_count = len(filtered_df[filtered_df["score"].isin([1, 2])])
    positive_pct = (positive_count / total_reviews * 100) if total_reviews > 0 else 0.0
    negative_pct = (negative_count / total_reviews * 100) if total_reviews > 0 else 0.0
    replied_count = int(filtered_df["has_reply"].sum())
    reply_rate_pct = (replied_count / total_reviews * 100) if total_reviews > 0 else 0.0

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.markdown(
            f"""
            <div class="mis-card">
                <div class="mis-card-stripe stripe-green"></div>
                <div class="mis-card-label">Evaluated Volume</div>
                <div class="mis-card-value">{total_reviews:,}</div>
                <div class="mis-card-sub">Filtered reviews cohort</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="mis-card">
                <div class="mis-card-stripe stripe-emerald"></div>
                <div class="mis-card-label">Review Cohort Mean</div>
                <div class="mis-card-value" style="color: #16a34a;">{avg_score:.2f} <span style="font-size:0.95rem;color:#94a3b8;">/ 5.0</span></div>
                <div class="mis-card-sub">Storefront Benchmark: <b>4.6&#9733;</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="mis-card">
                <div class="mis-card-stripe stripe-green"></div>
                <div class="mis-card-label">Positive Baseline</div>
                <div class="mis-card-value">{positive_pct:.1f}%</div>
                <div class="mis-card-sub sub-green">{positive_count:,} reviews (4-5 Stars)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""
            <div class="mis-card">
                <div class="mis-card-stripe stripe-red"></div>
                <div class="mis-card-label">Critical Drag</div>
                <div class="mis-card-value">{negative_pct:.1f}%</div>
                <div class="mis-card-sub sub-red">{negative_count:,} reviews (1-2 Stars)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c5:
        st.markdown(
            f"""
            <div class="mis-card">
                <div class="mis-card-stripe stripe-blue"></div>
                <div class="mis-card-label">Support Reply Rate</div>
                <div class="mis-card-value">{reply_rate_pct:.1f}%</div>
                <div class="mis-card-sub">{replied_count:,} developer replies</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-bottom: 1.75rem;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # Main Navigation Tabs
    # -------------------------------------------------------------------------
    tab_overview, tab_diagnostics, tab_explorer, tab_matrix = st.tabs([
        "Overview & Trajectory",
        "Root Cause Diagnostics",
        "Review & Evidence Explorer",
        "Engineering Priority Matrix",
    ])

    # -------------------------------------------------------------------------
    # Tab 1: Overview & Trajectory
    # -------------------------------------------------------------------------
    with tab_overview:
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.markdown("##### Rating Distribution Across Tiers")
            if total_reviews > 0:
                dist = filtered_df["score"].value_counts().sort_index().reset_index()
                dist.columns = ["score", "count"]
                dist["tier"] = dist["score"].apply(lambda s: f"{s} Star{'s' if s > 1 else ''}")

                # High-Contrast MoveInSync Color Palette
                mis_colors = ["#dc2626", "#ea580c", "#d97706", "#059669", "#16a34a"]
                fig_dist = go.Figure(
                    go.Bar(
                        x=dist["tier"],
                        y=dist["count"],
                        marker=dict(color=mis_colors, line=dict(color="rgba(255, 255, 255, 0.2)", width=1)),
                        text=dist["count"].apply(lambda v: f"{v:,}"),
                        textposition="outside",
                        textfont=dict(size=12, family="Plus Jakarta Sans"),
                        hovertemplate="<b>%{x}</b><br>Reviews: %{y:,}<extra></extra>",
                    )
                )
                fig_dist.update_layout(
                    margin=dict(l=10, r=10, t=25, b=10),
                    height=330,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor="rgba(148, 163, 184, 0.2)", zeroline=False),
                    font=dict(family="Plus Jakarta Sans"),
                )
                st.plotly_chart(fig_dist, use_container_width=True)
            else:
                st.info("No records match the active criteria.")

        with col_g2:
            st.markdown("##### Monthly Rating Trajectory & Inflow")
            if total_reviews > 0:
                monthly_data = filtered_df.groupby("year_month").agg(
                    avg_score=("score", "mean"),
                    volume=("score", "count"),
                ).reset_index()

                fig_traj = go.Figure()
                fig_traj.add_trace(
                    go.Bar(
                        x=monthly_data["year_month"],
                        y=monthly_data["volume"],
                        name="Review Volume",
                        marker=dict(
                            color="#22c55e",
                            line=dict(color="#16a34a", width=1),
                        ),
                        opacity=0.75,
                        yaxis="y2",
                        hovertemplate="Month: %{x}<br>Volume: %{y:,}<extra></extra>",
                    )
                )
                fig_traj.add_trace(
                    go.Scatter(
                        x=monthly_data["year_month"],
                        y=monthly_data["avg_score"],
                        name="Average Rating",
                        line=dict(color="#16a34a", width=3.5),
                        mode="lines+markers",
                        marker=dict(size=8, color="#15803d", line=dict(color="#ffffff", width=2)),
                        hovertemplate="Month: %{x}<br>Score: %{y:.2f} / 5.0<extra></extra>",
                    )
                )
                fig_traj.update_layout(
                    margin=dict(l=10, r=10, t=25, b=10),
                    height=330,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False),
                    yaxis=dict(
                        title="Average Rating",
                        range=[1.0, 5.0],
                        showgrid=True,
                        gridcolor="rgba(148, 163, 184, 0.2)",
                    ),
                    yaxis2=dict(
                        title="Review Volume",
                        overlaying="y",
                        side="right",
                        showgrid=False,
                    ),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    font=dict(family="Plus Jakarta Sans"),
                )
                st.plotly_chart(fig_traj, use_container_width=True)
            else:
                st.info("No records match the active criteria.")

        st.markdown("---")
        st.markdown("##### Enterprise Commute Journey Observations")
        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown(
                """
                <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:8px; padding:1.1rem;">
                    <div style="font-weight:700; color:#166534; margin-bottom:0.3rem;">Reliable Core Commute Experience</div>
                    <div style="font-size:0.86rem; color:#334155; line-height:1.5;">
                        68.4% of evaluated employees award 4 or 5 stars, regularly praising trip safety, driver verification, and corporate route convenience.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with k2:
            st.markdown(
                """
                <div style="background:#fef2f2; border:1px solid #fecaca; border-radius:8px; padding:1.1rem;">
                    <div style="font-weight:700; color:#991b1b; margin-bottom:0.3rem;">Acute Friction Bottlenecks</div>
                    <div style="font-size:0.86rem; color:#334155; line-height:1.5;">
                        Negative drag (28.8%) is concentrated during high-stress moments: cold-start crashes post-update and authentication dropouts when the cab arrives.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with k3:
            st.markdown(
                """
                <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:1.1rem;">
                    <div style="font-weight:700; color:#0f172a; margin-bottom:0.3rem;">Operational SLA Opportunity</div>
                    <div style="font-size:0.86rem; color:#334155; line-height:1.5;">
                        95.5% of critical reviews are publicly unaddressed. Implementing an operational triage webhook within 4 hours provides a direct recovery mechanism.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # -------------------------------------------------------------------------
    # Tab 2: Root Cause Diagnostics
    # -------------------------------------------------------------------------
    with tab_diagnostics:
        st.markdown("##### Actionable Negative Friction Drivers (1-2 Star Reviews)")

        negatives = filtered_df[filtered_df["score"].isin([1, 2])]
        if not negatives.empty:
            cat_ranked = (
                negatives.groupby("primary_label")
                .agg(count=("reviewId", "count"), upvotes=("thumbsUpCount", "sum"))
                .reset_index()
                .sort_values("count", ascending=True)
            )
            cat_ranked["share"] = (cat_ranked["count"] / len(negatives) * 100).round(1)

            col_diag1, col_diag2 = st.columns([1.3, 1])

            with col_diag1:
                fig_hbar = go.Figure(
                    go.Bar(
                        x=cat_ranked["count"],
                        y=cat_ranked["primary_label"],
                        orientation="h",
                        marker=dict(
                            color=cat_ranked["count"],
                            colorscale=[
                                [0.0, "#f97316"],
                                [0.5, "#22c55e"],
                                [1.0, "#15803d"],
                            ],
                            line=dict(color="rgba(255, 255, 255, 0.2)", width=0.5),
                            showscale=False,
                        ),
                        text=cat_ranked.apply(lambda r: f"{r['count']:,} ({r['share']}%)", axis=1),
                        textposition="outside",
                        textfont=dict(size=11, family="Plus Jakarta Sans"),
                        hovertemplate="<b>%{y}</b><br>Volume: %{x:,}<extra></extra>",
                    )
                )
                fig_hbar.update_layout(
                    margin=dict(l=10, r=60, t=10, b=10),
                    height=460,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=True, gridcolor="rgba(148, 163, 184, 0.2)"),
                    yaxis=dict(showgrid=False),
                    font=dict(family="Plus Jakarta Sans"),
                )
                st.plotly_chart(fig_hbar, use_container_width=True)

            with col_diag2:
                tbl = cat_ranked.sort_values("count", ascending=False).rename(
                    columns={
                        "primary_label": "Domain Category",
                        "count": "Negative Reviews",
                        "share": "Negatives Share (%)",
                        "upvotes": "Helpful Votes",
                    }
                )
                st.dataframe(tbl, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("##### Category Concentration Across App Release Versions")
            valid_vers = negatives[negatives["reviewCreatedVersion"] != "Unknown"]
            if not valid_vers.empty:
                top_v = valid_vers["reviewCreatedVersion"].value_counts().head(8).index.tolist()
                sub_v = valid_vers[valid_vers["reviewCreatedVersion"].isin(top_v)].copy()

                curated_cats = [
                    ("APP_RELIABILITY", "App Reliability", "#ef4444"),
                    ("LOGIN_ACCESS", "Login & Access", "#f97316"),
                    ("DRIVER_TRANSPORT_OPERATIONS", "Driver Operations", "#eab308"),
                    ("BOOKING_SCHEDULING", "Booking & Rostering", "#3b82f6"),
                    ("TRACKING_MAPS", "GPS & Maps", "#10b981"),
                ]
                curated_keys = [c[0] for c in curated_cats]
                
                pivot_v = pd.crosstab(sub_v["reviewCreatedVersion"], sub_v["primary_label"]).reindex(top_v, fill_value=0)

                fig_stacked = go.Figure()
                for cat_key, cat_label, cat_color in curated_cats:
                    if cat_key in pivot_v.columns:
                        fig_stacked.add_trace(
                            go.Bar(
                                name=cat_label,
                                x=top_v,
                                y=pivot_v[cat_key],
                                marker=dict(color=cat_color),
                                hovertemplate=f"<b>{cat_label}</b><br>Version %{{x}}: %{{y:,}} complaints<extra></extra>",
                            )
                        )
                
                other_cols = [c for c in pivot_v.columns if c not in curated_keys]
                if other_cols:
                    other_counts = pivot_v[other_cols].sum(axis=1)
                    fig_stacked.add_trace(
                        go.Bar(
                            name="Other Drivers",
                            x=top_v,
                            y=other_counts,
                            marker=dict(color="#64748b"),
                            hovertemplate="<b>Other Drivers</b><br>Version %{x}: %{y:,} complaints<extra></extra>",
                        )
                    )

                fig_stacked.update_layout(
                    barmode="stack",
                    margin=dict(l=10, r=10, t=30, b=10),
                    height=380,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(
                        type="category",
                        title=dict(text="App Release Version", font=dict(family="Plus Jakarta Sans")),
                        showgrid=False,
                    ),
                    yaxis=dict(
                        title=dict(text="Negative Reviews (1-2 Stars)", font=dict(family="Plus Jakarta Sans")),
                        showgrid=True,
                        gridcolor="rgba(148, 163, 184, 0.2)",
                    ),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.03,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=11, family="Plus Jakarta Sans"),
                    ),
                    font=dict(family="Plus Jakarta Sans"),
                )
                st.plotly_chart(fig_stacked, use_container_width=True)
        else:
            st.info("No negative records found within the active filter parameters.")

    # -------------------------------------------------------------------------
    # Tab 3: Review & Evidence Explorer
    # -------------------------------------------------------------------------
    with tab_explorer:
        st.markdown("##### Verified Customer Quotes & Extracted Substring Evidence")
        st.caption(f"Showing {total_reviews:,} matching reviews. Filter by category, sentiment, or keywords in the sidebar.")

        # Dataframe
        grid_df = filtered_df[
            [
                "at",
                "score",
                "primary_label",
                "issue_type",
                "reviewCreatedVersion",
                "thumbsUpCount",
                "has_reply",
                "content",
            ]
        ].rename(
            columns={
                "at": "Date",
                "score": "Rating",
                "primary_label": "Category",
                "issue_type": "Issue Type",
                "reviewCreatedVersion": "Version",
                "thumbsUpCount": "Helpful Votes",
                "has_reply": "Replied",
                "content": "Review Content",
            }
        )
        st.dataframe(grid_df.head(250), use_container_width=True, height=360)

        export_csv = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Filtered Reviews (CSV)",
            data=export_csv,
            file_name=f"moveinsync_reviews_{datetime.date.today()}.csv",
            mime="text/csv",
        )

        st.markdown("---")
        st.markdown("##### Real Feedback Verification Cards")
        cards = filtered_df.head(8).to_dict("records")
        card_col1, card_col2 = st.columns(2)

        for idx, rec in enumerate(cards):
            t_col = card_col1 if (idx % 2 == 0) else card_col2
            with t_col:
                score_val = int(rec["score"])
                cls_type = "review-neg" if score_val <= 2 else ("review-pos" if score_val >= 4 else "")
                reply_pill = (
                    '<span class="mis-badge badge-mis-green">Replied</span>'
                    if rec["has_reply"]
                    else '<span class="mis-badge badge-mis-red">Unaddressed</span>'
                )

                st.markdown(
                    f"""
                    <div class="mis-review-card {cls_type}">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:800; color:#16a34a;">{rec['score']}.0 / 5.0 Rating</span>
                            <div>
                                <span class="mis-badge badge-mis-neutral">{rec['primary_label']}</span>
                                {reply_pill}
                            </div>
                        </div>
                        <div class="mis-quote">"{rec['content']}"</div>
                        <div class="mis-meta">
                            Release: {rec['reviewCreatedVersion']} &bull; Date: {str(rec['at'])[:10]} &bull; Helpful Votes: {rec['thumbsUpCount']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # -------------------------------------------------------------------------
    # Tab 4: Engineering Priority Matrix
    # -------------------------------------------------------------------------
    with tab_matrix:
        st.markdown("##### Candidate Engineering Action Plan & Priority Matrix")
        st.caption("Root-cause initiatives sequenced by frequency, customer upvote endorsements, and commute friction severity.")

        mat_df = load_priority_matrix(m_mtime)
        if not mat_df.empty:
            st.dataframe(mat_df, use_container_width=True, hide_index=True)
        else:
            st.info("Priority matrix CSV not found. Run pipeline/06_report.py to regenerate.")

        st.markdown("---")
        mx1, mx2 = st.columns(2)
        with mx1:
            st.markdown(
                """
                <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:8px; padding:1.25rem;">
                    <div style="font-weight:800; font-size:1.05rem; color:#166534; margin-bottom:0.5rem;">
                        Core Strategic Pillars
                    </div>
                    <p style="font-size:0.88rem; color:#334155; margin-bottom:0.5rem;">
                        <strong>1. App Reliability (P0):</strong> Eliminate cold-start crash loops post-update; implement client SQLite caching for offline roster access.
                    </p>
                    <p style="font-size:0.88rem; color:#334155; margin-bottom:0.5rem;">
                        <strong>2. Login Resilience (P0):</strong> Extend OAuth refresh token TTL to 30 days with biometric session unlock; add secondary WhatsApp OTP gateway.
                    </p>
                    <p style="font-size:0.88rem; color:#334155;">
                        <strong>3. Operational Geofencing (P1):</strong> Enforce 100m geofence validation and mandatory passenger OTP verification before allowing drivers to mark trips 'Boarded'.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with mx2:
            st.markdown(
                """
                <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:1.25rem;">
                    <div style="font-weight:800; font-size:1.05rem; color:#0f172a; margin-bottom:0.5rem;">
                        Authoritative Technical Deliverable
                    </div>
                    <p style="font-size:0.88rem; color:#334155; line-height:1.5;">
                        The complete, candidate-authored executive strategy paper, empirical hypotheses, and 90-day Day-1 engineering roadmap are documented in:
                    </p>
                    <p style="margin-top:0.75rem;">
                        <a href="file:///c:/Users/adwai/OneDrive/Documents/LPU/moveinsync/RECOMMENDATIONS.md" style="display:inline-block; background:#16a34a; color:#ffffff; padding:0.4rem 0.85rem; border-radius:6px; font-weight:700; text-decoration:none; font-size:0.85rem;">
                            View RECOMMENDATIONS.md
                        </a>
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()
