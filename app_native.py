"""How a Video Gets Trending - Streamlit version.

All numbers come from data.json (results computed earlier in Python on the
Kaggle "Trending YouTube Video Statistics" US + Canada files).
"""
import json
import math
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="How a Video Gets Trending", page_icon="📈", layout="wide")

D = json.loads((Path(__file__).parent / "data.json").read_text(encoding="utf-8"))

# ---------- constants ----------
CYAN, VIOLET, GREEN, AMBER, PINK, SLATE, GREY = (
    "#58D6FF", "#8B7CFF", "#4CE08B", "#F5C66A", "#F08A9B", "#7F93B5", "#2A3650")
CAT = D["cats"]
CC = [CYAN, VIOLET, GREEN, AMBER, PINK, SLATE]
WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
K, CL = D["kpi"], D["clean"]

st.markdown(
    """
<style>
.big{background:#172033;border:1px solid #243044;border-left:3px solid #58D6FF;
     border-radius:14px;padding:14px 18px;margin:8px 0 14px}
.big p{margin:0 0 6px}.big p:last-child{margin:0}
.insight{color:#A8B3C7;border-top:1px solid #243044;padding-top:10px;margin-top:6px}
.insight b{color:#58D6FF}
.tag-ok{background:rgba(76,224,139,.12);color:#4CE08B;padding:2px 10px;border-radius:999px;font-size:12px}
.tag-ns{background:rgba(245,198,106,.12);color:#F5C66A;padding:2px 10px;border-radius:999px;font-size:12px}
.chip-off{display:inline-block;border:1px solid #243044;border-radius:999px;padding:4px 12px;
          margin:0 6px 6px 0;color:#A8B3C7;font-size:13px;opacity:.6}
</style>""",
    unsafe_allow_html=True,
)


# ---------- helpers ----------
def fmt(n):
    return f"{n:,}"


def fm(n):
    if n >= 1e6:
        return f"{n / 1e6:.2f}M"
    if n >= 1e3:
        return f"{n / 1e3:.0f}K"
    return f"{round(n)}"


def hi(d, f=lambda x: x):
    return max(d, key=lambda k: f(d[k]))


def lo(d, f=lambda x: x):
    return min(d, key=lambda k: f(d[k]))


def insight(text):
    st.markdown(f'<div class="insight"><b>Key insight</b> {text}</div>', unsafe_allow_html=True)


def big(html):
    st.markdown(f'<div class="big">{html}</div>', unsafe_allow_html=True)


def style(fig, height=340, legend=False, xtitle=None, ytitle=None):
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=height, margin=dict(l=10, r=10, t=10, b=10), showlegend=legend,
        font=dict(color="#A8B3C7"),
    )
    fig.update_xaxes(title=xtitle, gridcolor="rgba(36,48,68,.6)")
    fig.update_yaxes(title=ytitle, gridcolor="rgba(36,48,68,.6)")
    return fig


def show(fig):
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})


def goto(key):
    st.session_state["page"] = key


# ---------- pages ----------
def p_overview():
    st.title("How does a video end up on the trending list?")
    st.caption("YouTube trending videos dataset: view and engagement pattern analysis across "
               "categories and regions. Pick a stage to see what happens behind the scenes "
               "and what the data shows.")
    S = [
        ("Upload", "A creator publishes. Category, title, tags and upload time are set.",
         f"Uploads that trend peak at different hours by category: {CAT[0]} at "
         f"{D['peak'][CAT[0]]}:00 UTC, {CAT[5]} at {D['peak'][CAT[5]]}:00 UTC.", "upload"),
        ("Early traction", "Views, likes and comments arrive in the first hours.",
         f"On a video's first trending day, views and likes are strongly linked "
         f"(r = {D['r']['likes']}), and so are views and comments (r = {D['r']['comm']}).", "early"),
        ("Trending signal", "YouTube's system spots videos growing faster than normal and adds them to the list.",
         f"Half of all videos trend within {D['lagmed']} day(s) of publishing, "
         f"and {D['lag3']}% within 3 days.", "lag"),
        ("Staying on the list", "Daily views peak a few days in, then fade until the video drops off.",
         f"{hi(D['stayd'])} videos stay longest ({D['stayd'][hi(D['stayd'])]} days); "
         f"{lo(D['stayd'])} the shortest ({D['stayd'][lo(D['stayd'])]}).", "stay"),
        ("Spreading", "The same video can trend in several countries, each reacting differently.",
         f"{fmt(D['both']['n'])} videos trended in both the US and Canada. "
         f"{D['both']['same']}% appeared in both on the same day.", "reg"),
    ]
    with st.container(border=True):
        names = [f"{i + 1}. {s[0]}" for i, s in enumerate(S)]
        pick = st.radio("Stage", names, horizontal=True, label_visibility="collapsed")
        s = S[names.index(pick)]
        big(f"<p><b>Behind the scenes:</b> {s[1]}</p><p><b>What the data shows:</b> {s[2]}</p>")
        st.button("Open this step →", on_click=goto, args=(s[3],), key="open_step")
    c = st.columns(4)
    c[0].metric("Trending records", fmt(K["rows"]))
    c[1].metric("Unique videos", fmt(K["videos"]))
    c[2].metric("Channels", fmt(K["channels"]))
    c[3].metric("Countries", "US and Canada")
    st.caption(f"Daily trending lists from {K['from']} to {K['to']}.")


COLS = [
    ("video_id", "Identity", "The same ID repeats on every day it stays on the list, so one row is one video on one day."),
    ("title", "Upload choice", "Title length is tested as a factor."),
    ("channel_title", "Who", "Large channels trend more often."),
    ("category_id", "Upload choice", "Maps to Music, Gaming, News and so on."),
    ("publish_time", "Start of the clock", "Needed to measure how long a video takes to trend."),
    ("trending_date", "Moment it appeared", "trending_date minus publish_time gives time to trend."),
    ("tags", "Upload choice", "Gives the tag_count feature."),
    ("views", "Reach", "The main outcome we explain."),
    ("likes", "Engagement", "Early positive reaction."),
    ("dislikes", "Engagement", "Negative reaction, weakly linked to the rest."),
    ("comment_count", "Engagement", "Conversation around the video."),
    ("country", "Where", "One file per country (US and CA), so we can compare regions."),
]


def p_data():
    st.title("What we can see, and what we can't")
    st.caption(f"Each row is one video on one trending day: {fmt(K['rows'])} rows from the US and Canada.")
    a, b = st.columns(2)
    with a:
        st.subheader("Columns")
        col = st.radio("Column", [c[0] for c in COLS], label_visibility="collapsed")
    with b:
        st.subheader("Role in the story")
        c = next(x for x in COLS if x[0] == col)
        big(f"<p><b>{c[0]}</b> ({c[1]})</p><p>{c[2]}</p>")
        st.subheader("Not in the data")
        st.markdown("".join(f'<span class="chip-off">{t}</span>' for t in
                            ["watch time", "click-through rate", "audience retention", "shares", "hourly views"]),
                    unsafe_allow_html=True)


FE = {
    "engagement_rate": "(likes + comments) / views × 100",
    "like_ratio": "likes / views",
    "comment_ratio": "comments / views",
    "days_to_trend": "first trending date − publish date",
    "trending_days": "number of days a video appears on the list",
    "upload_hour": "hour of publish_time (UTC)",
    "upload_weekday": "weekday of publish_time",
    "title_length": "characters in title",
    "tag_count": "number of tags",
}


def p_clean():
    st.title("Turning raw files into an analysis table")
    st.caption("Move the slider to step through the pipeline.")
    CD = [
        f"{fmt(CL[0][1])} rows from the US and Canada files.",
        f"{fmt(CL[0][1] - CL[1][1])} repeated rows (same video, same day, same country) dropped.",
        f"{fmt(CL[1][1] - CL[2][1])} rows with missing key fields dropped. Missing descriptions are kept.",
        f"{fmt(CL[2][1] - CL[3][1])} rows dropped for unreadable dates. Dates are now real timestamps.",
        f"{fmt(CL[3][1] - CL[4][1])} rows dropped for unknown categories. category_id becomes names like Music.",
        f"{fmt(D['cap'])} rows are above the 99th percentile of views and are flagged as outliers.",
        f"Features added for {fmt(K['videos'])} unique videos.",
    ]
    with st.container(border=True):
        i = st.slider("Step", 0, len(CL) - 1, 0, format="%d")
        colors = [CYAN if j == i else VIOLET if j < i else GREY for j in range(len(CL))]
        fig = go.Figure(go.Bar(x=[c[0] for c in CL], y=[c[1] for c in CL], marker_color=colors))
        show(style(fig, 260, ytitle="rows"))
        big(f"<p><b>{CL[i][0]}: {fmt(CL[i][1])} rows.</b> {CD[i]}</p>")
    with st.container(border=True):
        st.subheader("Engineered features")
        f = st.radio("Feature", list(FE), horizontal=True, label_visibility="collapsed")
        big(f"<p><code>{f}</code> = {FE[f]}</p>")


def p_upload():
    st.title("Step 1: the upload")
    st.caption("Before anything else, the creator chooses a category and a moment.")
    cat = st.radio("Category", CAT, horizontal=True)
    mode = st.radio("View", ["By hour", "By weekday"], horizontal=True)
    if mode == "By hour":
        x, y, ytitle = [f"{h}:00" for h in range(24)], D["hour"][cat], "share of trending uploads (%)"
        text = f"{cat} videos that trend are most often uploaded at {D['peak'][cat]}:00 UTC."
    else:
        x, y, ytitle = WD, D["wday"][cat], "average engagement rate (%)"
        b = D["bestwd"][cat]
        text = (f"{cat} videos uploaded on {WD[b]} have the highest average "
                f"engagement rate ({D['wday'][cat][b]}%).")
    fig = go.Figure(go.Bar(x=x, y=y, marker_color=CC[CAT.index(cat)]))
    show(style(fig, 380, ytitle=ytitle))
    insight(text)


def p_early():
    st.title("Step 2: early traction")
    st.caption("Each dot is one video on its first trending day. Click legend items to hide categories.")
    met = st.radio("Metric", ["Likes", "Comments"], horizontal=True)
    ix = 1 if met == "Likes" else 2
    fig = go.Figure()
    for i, c in enumerate(CAT):
        pts = D["sc"][c]
        fig.add_trace(go.Scatter(
            x=[p[0] for p in pts], y=[p[ix] for p in pts], mode="markers", name=c,
            marker=dict(color=CC[i], size=8, opacity=0.65),
            hovertemplate=f"{c}<br>views ≈ %{{customdata[0]}}<br>{met.lower()} ≈ %{{customdata[1]}}<extra></extra>",
            customdata=[[fm(10 ** p[0]), fm(10 ** p[ix])] for p in pts]))
    show(style(fig, 420, legend=True, xtitle="log10 views", ytitle=f"log10 {met.lower()}"))
    r = D["r"]["likes"] if met == "Likes" else D["r"]["comm"]
    insight(f"Views and {met.lower()} move together across all {fmt(K['videos'])} videos "
            f"(r = {r}). Showing 60 videos per category.")


def p_lag():
    st.title("Step 3: how long until it trends")
    st.caption("The gap between publishing and first appearing on the list.")
    cat = st.radio("Category", CAT, horizontal=True)
    n = st.slider("Within N day(s)", 0, 10, 2)
    d = D["lag"][cat]
    cum = sum(d[: n + 1])
    fig = go.Figure(go.Bar(x=[str(i) for i in range(11)] + ["11+"], y=d,
                           marker_color=[CYAN if i <= n else GREY for i in range(12)]))
    show(style(fig, 340, xtitle="days from publish to trending", ytitle="share of videos (%)"))
    insight(f"{cum:.0f}% of {cat} videos trend within {n} day(s). The average gap is "
            f"{D['lagm'][cat]} days; {lo(D['lagm'])} is fastest and {hi(D['lagm'])} slowest.")


def p_stay():
    st.title("Step 4: staying on the list")
    st.caption("Once listed, views keep growing for a few days. Click legend items to compare categories.")
    m = st.radio("Metric", ["Daily views", "Total views"], horizontal=True)
    key = "day" if m == "Daily views" else "tot"
    fig = go.Figure()
    for i, c in enumerate(CAT):
        fig.add_trace(go.Scatter(x=[f"Day {d + 1}" for d in range(12)], y=D["stay"][c][key],
                                 mode="lines+markers", name=c, line=dict(color=CC[i], width=2)))
    fig.update_layout(hovermode="x unified")
    ytitle = ("views gained that day" if key == "day" else "total views") + " (millions, average)"
    show(style(fig, 420, legend=True, ytitle=ytitle))
    t = hi(D["stayd"])
    insight(f"{t} videos stay longest on the list ({D['stayd'][t]} days on average); "
            f"{lo(D['stayd'])} videos leave after {D['stayd'][lo(D['stayd'])]} days. "
            "Lines get noisier on later days because fewer videos last that long.")


def p_reg():
    st.title("Step 5: where it trends")
    st.caption("The same category behaves differently in the US and Canada.")
    M = {"Engagement rate (%)": "eng", "Share of country's list (%)": "share",
         "Average views (millions)": "views", "Average days on list": "days"}
    a, b = st.columns(2)
    with a:
        cur = st.radio("Metric", list(M), horizontal=True)
        fig = go.Figure()
        for k, colr in (("US", CYAN), ("CA", VIOLET)):
            fig.add_trace(go.Bar(name=k, x=CAT, y=[D["reg"][k][c][M[cur]] for c in CAT], marker_color=colr))
        fig.update_layout(barmode="group")
        show(style(fig, 340, legend=True, ytitle=cur))
        ua, ca = hi(D["reg"]["US"], lambda x: x[M[cur]]), hi(D["reg"]["CA"], lambda x: x[M[cur]])
        insight(f"Highest {cur.lower()}: {ua} in the US, {ca} in Canada.")
    with b:
        B = D["both"]
        st.subheader("Videos that trended in both countries")
        st.metric("Videos", fmt(B["n"]))
        st.caption(f"{B['pctUS']}% of US trending videos and {B['pctCA']}% of Canadian ones.")
        txt = {"Who trended first?": f"{B['usFirst']}% reached the US list first, {B['caFirst']}% "
                                     f"reached Canada first, and {B['same']}% appeared on both the same day.",
               "How far apart?": f"On average the two appearances are {B['gap']} days apart."}
        q = st.radio("Question", list(txt), horizontal=True, label_visibility="collapsed")
        big(f"<p>{txt[q]}</p>")


def p_stats():
    st.title("Is the pattern real or luck?")
    st.caption(f"Tests run on {fmt(K['videos'])} videos. Move the significance level to see which results hold.")
    a = st.slider("Significance level α", 0.001, 0.100, 0.050, 0.001, format="%.3f")
    cols = st.columns(2)
    for i, t in enumerate(D["stats"]):
        name, question, stat, p, meaning = t
        sig = p < a
        with cols[i % 2].container(border=True):
            st.markdown(f"**{name}**")
            st.caption(question)
            ptxt = "< 0.001" if p < 0.001 else f"= {p:.3f}"
            st.markdown(f"`{stat}`  &nbsp; `p {ptxt}`")
            if sig:
                st.markdown(f'<span class="tag-ok">Significant: {meaning}</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="tag-ns">Not significant at this α</span>', unsafe_allow_html=True)
            with st.expander("How to read this"):
                st.write(f"If p is below α, the pattern is unlikely to be chance. Here p "
                         f"{'is below' if sig else 'is not below'} {a:.3f}.")


def p_model():
    MD, LN, LG, RG = D["model"], D["lin"], D["log"], D["rng"]
    FN = ["Likes", "Comments", "Tag count", "Category", "Upload hour"]
    st.title("Can we predict it?")
    st.caption(f"Four models trained on {fmt(D['nm'])} videos to predict first-day views from likes, "
               "comments, tags, category and upload hour (tested on a held-out 20%).")
    a, b = st.columns(2)
    with a:
        m = st.radio("Model", list(MD), index=list(MD).index("Random Forest"), horizontal=True)
        mae, rmse, r2, imp = MD[m]
        big(f"<b>{m}</b>: MAE {mae}, RMSE {rmse}, R² {r2} (log10 views). "
            f"A typical prediction is off by about ×{10 ** mae:.1f}.")
        fig = go.Figure(go.Bar(x=imp, y=FN, orientation="h", marker_color=CYAN))
        fig.update_yaxes(autorange="reversed")
        show(style(fig, 260, xtitle="feature importance"))
        st.dataframe(pd.DataFrame(
            {k: {"MAE": v[0], "RMSE": v[1], "R²": v[2]} for k, v in MD.items()}).T, use_container_width=True)
    with b:
        st.subheader("What-if")
        l = st.slider("Likes (log scale)", RG["ll"][0], RG["ll"][1], (RG["ll"][0] + RG["ll"][1]) / 2, 0.05)
        c = st.slider("Comments (log scale)", RG["lc"][0], RG["lc"][1], (RG["lc"][0] + RG["lc"][1]) / 2, 0.05)
        t = st.slider("Tags", 0, RG["tags"][1], RG["tags"][1] // 2)
        st.caption(f"Likes ≈ {fm(10 ** l)}, comments ≈ {fm(10 ** c)}, tags = {t}")
        pred = 10 ** (LN["b"] + LN["c"][0] * l + LN["c"][1] * c + LN["c"][2] * t)
        prob = 100 / (1 + math.exp(-(LG["b"] + LG["c"][0] * l + LG["c"][1] * c + LG["c"][2] * t)))
        st.metric("Predicted views", fm(pred))
        st.metric("Chance of staying 5+ days on the list", f"{round(prob)}%")
        st.caption(f"Across all videos, {LG['base']}% stay 5 days or more.")


def p_spark():
    SC = D["scale"]
    st.title("Doing it at scale")
    st.caption(f"The same category aggregation, timed in Pandas and PySpark on this data repeated up to "
               f"{SC[-1][0]} million rows (run on one machine).")
    st.markdown("".join(f'<span class="chip-off">{s}</span>' for s in
                        ["CSV files → ", "PySpark DataFrame → ", "Clean and transform → ",
                         "Aggregate → ", "Spark SQL → ", "Dashboard"]), unsafe_allow_html=True)
    a, b = st.columns(2)
    with a:
        i = st.select_slider("Rows (millions)", options=list(range(len(SC))), value=2,
                             format_func=lambda j: str(SC[j][0]))
        r = SC[i]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[s[0] for s in SC], y=[s[1] for s in SC], name="Pandas",
                                 mode="lines+markers", line=dict(color=VIOLET)))
        fig.add_trace(go.Scatter(x=[s[0] for s in SC], y=[s[2] for s in SC], name="PySpark",
                                 mode="lines+markers", line=dict(color=CYAN)))
        fig.add_trace(go.Scatter(x=[r[0], r[0]], y=[r[1], r[2]], name="Selected", mode="markers",
                                 marker=dict(size=12, color="#F3F7FF")))
        show(style(fig, 340, legend=True, xtitle="rows (millions)", ytitle="seconds"))
        insight(f"At {r[0]}M rows Pandas took {r[1]} s and Spark {r[2]} s. "
                + ("On one machine Pandas is faster. Spark's advantage appears when data no longer "
                   "fits in one machine's memory." if r[1] < r[2] else "Spark is faster here."))
    with b:
        st.subheader("Category aggregation in Spark SQL")
        st.code('df.createOrReplaceTempView("videos")\nspark.sql("""\n  SELECT country, category_id,\n'
                '         AVG(views) AS avg_views,\n         SUM(likes) AS total_likes\n'
                '  FROM videos\n  GROUP BY country, category_id\n""").show()', language="python")
        st.caption(f"Spark session start-up: {D['sparkstart']} s (one time).")


def p_end():
    MD = D["model"]
    FN = ["likes", "comments", "tag count", "category", "upload hour"]
    bm = max(MD, key=lambda k: MD[k][2])
    TK = [
        ("Upload", f"{CAT[0]} peaks at {D['peak'][CAT[0]]}:00 UTC and {CAT[5]} at {D['peak'][CAT[5]]}:00; "
                   "weekday engagement differs by category.", "upload"),
        ("Early traction", f"Views, likes and comments move together (r = {D['r']['likes']} and {D['r']['comm']}).", "early"),
        ("Time to trend", f"Half of videos trend within {D['lagmed']} day(s); {D['lag3']}% within 3 days.", "lag"),
        ("Staying on the list", f"{hi(D['stayd'])} lasts {D['stayd'][hi(D['stayd'])]} days on average; "
                                f"{lo(D['stayd'])} only {D['stayd'][lo(D['stayd'])]}.", "stay"),
        ("Where it spreads", f"{fmt(D['both']['n'])} videos trended in both the US and Canada, "
                             f"{D['both']['same']}% on the same day.", "reg"),
        ("Prediction", f"{bm} predicts views best (R² {MD[bm][2]}), led by "
                       f"{FN[MD[bm][3].index(max(MD[bm][3]))]}.", "model"),
    ]
    st.title("How a video gets trending")
    st.caption("The full story in six lines. Use the buttons to revisit a step.")
    cols = st.columns(2)
    for i, (title, text, key) in enumerate(TK):
        with cols[i % 2].container(border=True):
            st.markdown(f"**{title}**")
            st.write(text)
            st.button("Revisit →", key=f"rv_{key}", on_click=goto, args=(key,))
    big("<p><b>Bottom line.</b> Videos that trend are the ones whose views, likes and comments build up "
        "quickly after upload. How long they stay on the list depends on their category.</p>")


PAGES = {
    "overview": ("The question", p_overview), "data": ("The data", p_data), "clean": ("Cleaning", p_clean),
    "upload": ("1 · Upload", p_upload), "early": ("2 · Early traction", p_early),
    "lag": ("3 · Time to trend", p_lag), "stay": ("4 · Staying on the list", p_stay),
    "reg": ("5 · Where it spreads", p_reg), "stats": ("Proof", p_stats),
    "model": ("Prediction", p_model), "spark": ("Scale", p_spark), "end": ("Takeaways", p_end),
}

if "page" not in st.session_state:
    st.session_state["page"] = "overview"

with st.sidebar:
    st.markdown("### How a video gets **trending**")
    st.radio("Navigate", list(PAGES), key="page", format_func=lambda k: PAGES[k][0],
             label_visibility="collapsed")
    st.caption("Data: Kaggle Trending YouTube Video Statistics (US + Canada).")

PAGES[st.session_state["page"]][1]()
