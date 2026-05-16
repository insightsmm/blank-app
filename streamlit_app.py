import streamlit as st
import anthropic
import requests
import json
import re
import html
import time
import io
from datetime import datetime, date
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
# Page configuration
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="WordPress SEO Agent",
    page_icon="🔍",
    layout="wide",
)

# ─────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────
st.markdown(
    """
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 1rem; max-width: 1200px;}
    .stButton > button {
        background: linear-gradient(135deg, #10B981 0%, #3B82F6 100%);
        color: white; border: 0; border-radius: 10px;
        padding: 0.6rem 1.2rem; font-weight: 600;
    }
    .metric-card {
        background: #161B22; border: 1px solid #21262D;
        border-radius: 12px; padding: 1.2rem; text-align: center;
    }
    .score-green { color: #10B981; font-weight: 700; font-size: 1.4rem; }
    .score-orange { color: #F59E0B; font-weight: 700; font-size: 1.4rem; }
    .score-red { color: #EF4444; font-weight: 700; font-size: 1.4rem; }
    .log-box {
        background: #0D1117; border: 1px solid #21262D; border-radius: 8px;
        padding: 0.8rem; font-family: monospace; font-size: 0.78rem;
        height: 300px; overflow-y: auto; color: #C9D1D9;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# Session state initialisation
# ─────────────────────────────────────────────
_defaults = {
    "agent_running": False,
    "agent_log": [],
    "processed_posts": [],   # list of dicts with processing results
    "drafts_cache": [],      # cached list of drafts
    "last_cycle_time": None,
    "selected_draft_id": None,
    "manual_post_data": None,
    "manual_seo_result": None,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
# Helpers — logging
# ─────────────────────────────────────────────

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.agent_log.append(f"[{ts}] {msg}")


# ─────────────────────────────────────────────
# WordPress API helpers
# ─────────────────────────────────────────────

def wp_request(method: str, endpoint: str, wp_url: str, wp_user: str, wp_pass: str,
               data=None, files=None, params=None):
    base = wp_url.rstrip("/") + "/wp-json/wp/v2/"
    url = base + endpoint
    auth = (wp_user, wp_pass)
    try:
        if files:
            resp = requests.request(method, url, auth=auth, files=files, params=params, timeout=30)
        elif data is not None:
            resp = requests.request(method, url, auth=auth, json=data, params=params, timeout=30)
        else:
            resp = requests.request(method, url, auth=auth, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(f"WP API HTTP error {exc.response.status_code}: {exc.response.text[:300]}") from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"WP API request failed: {exc}") from exc


def test_wp_connection(wp_url: str, wp_user: str, wp_pass: str) -> tuple[bool, str]:
    try:
        result = wp_request("GET", "users/me", wp_url, wp_user, wp_pass)
        return True, f"Connected as: {result.get('name', wp_user)}"
    except RuntimeError as exc:
        return False, str(exc)


def get_drafts(wp_url: str, wp_user: str, wp_pass: str,
               include_posts: bool = True, include_pages: bool = True) -> list[dict]:
    drafts = []
    if include_posts:
        try:
            posts = wp_request("GET", "posts", wp_url, wp_user, wp_pass,
                               params={"status": "draft", "per_page": 20})
            for p in posts:
                p["_type"] = "post"
            drafts.extend(posts)
        except RuntimeError as exc:
            log(f"Error fetching draft posts: {exc}")
    if include_pages:
        try:
            pages = wp_request("GET", "pages", wp_url, wp_user, wp_pass,
                               params={"status": "draft", "per_page": 20})
            for p in pages:
                p["_type"] = "page"
            drafts.extend(pages)
        except RuntimeError as exc:
            log(f"Error fetching draft pages: {exc}")
    return drafts


# ─────────────────────────────────────────────
# SEO Scoring
# ─────────────────────────────────────────────

def calculate_seo_score(title: str, content_html: str, meta_desc: str,
                        focus_keyword: str, slug: str,
                        featured_image_set: bool = False) -> tuple[int, list[dict]]:
    """Return (total_score, breakdown_list)."""
    keyword_lower = focus_keyword.lower().strip() if focus_keyword else ""
    title_lower = title.lower() if title else ""
    meta_lower = meta_desc.lower() if meta_desc else ""
    slug_lower = slug.lower() if slug else ""

    soup = BeautifulSoup(content_html or "", "lxml")
    text = soup.get_text(separator=" ")
    words = re.findall(r"\b\w+\b", text.lower())
    word_count = len(words)
    keyword_count = words.count(keyword_lower) if keyword_lower else 0
    keyword_density = (keyword_count / word_count * 100) if word_count > 0 else 0.0

    h2_tags = soup.find_all("h2")
    h3_tags = soup.find_all("h3")
    img_tags = soup.find_all("img")
    imgs_with_alt = [i for i in img_tags if i.get("alt", "").strip()]

    first_100_words = " ".join(words[:100])
    keyword_in_first_100 = keyword_lower in first_100_words if keyword_lower else False

    criteria = [
        {
            "criterion": "Title contains focus keyword",
            "max": 15,
            "score": 15 if keyword_lower and keyword_lower in title_lower else 0,
            "detail": f"Keyword '{focus_keyword}' in title",
        },
        {
            "criterion": "Title length 50–60 chars",
            "max": 10,
            "score": 10 if 50 <= len(title) <= 60 else (5 if 40 <= len(title) <= 70 else 0),
            "detail": f"Title length: {len(title)} chars",
        },
        {
            "criterion": "Meta description has keyword",
            "max": 15,
            "score": 15 if keyword_lower and meta_desc and keyword_lower in meta_lower else 0,
            "detail": f"Keyword in meta: {'Yes' if keyword_lower and keyword_lower in meta_lower else 'No'}",
        },
        {
            "criterion": "Meta description 150–160 chars",
            "max": 5,
            "score": 5 if meta_desc and 150 <= len(meta_desc) <= 160 else (3 if meta_desc and 140 <= len(meta_desc) <= 170 else 0),
            "detail": f"Meta desc length: {len(meta_desc) if meta_desc else 0} chars",
        },
        {
            "criterion": "Content ≥ 600 words",
            "max": 15,
            "score": 15 if word_count >= 600 else (8 if word_count >= 300 else 0),
            "detail": f"Word count: {word_count}",
        },
        {
            "criterion": "Keyword density 1–3%",
            "max": 15,
            "score": 15 if 1.0 <= keyword_density <= 3.0 else (8 if 0.5 <= keyword_density <= 5.0 else 0),
            "detail": f"Density: {keyword_density:.2f}%",
        },
        {
            "criterion": "H2/H3 headers present",
            "max": 10,
            "score": 10 if (h2_tags or h3_tags) else 0,
            "detail": f"H2: {len(h2_tags)}, H3: {len(h3_tags)}",
        },
        {
            "criterion": "Images with alt text",
            "max": 5,
            "score": 5 if imgs_with_alt else 0,
            "detail": f"Images with alt: {len(imgs_with_alt)}",
        },
        {
            "criterion": "Featured image set",
            "max": 5,
            "score": 5 if featured_image_set else 0,
            "detail": "Featured image: " + ("Yes" if featured_image_set else "No"),
        },
        {
            "criterion": "Clean keyword-based slug",
            "max": 5,
            "score": 5 if keyword_lower and keyword_lower.replace(" ", "-") in slug_lower else (
                5 if slug_lower and re.match(r"^[a-z0-9\-]+$", slug_lower) else 0
            ),
            "detail": f"Slug: {slug}",
        },
    ]
    total = sum(c["score"] for c in criteria)
    return total, criteria


def score_color_class(score: int) -> str:
    if score >= 85:
        return "score-green"
    if score >= 70:
        return "score-orange"
    return "score-red"


def colored_score_html(score: int) -> str:
    cls = score_color_class(score)
    return f'<span class="{cls}">{score}/100</span>'


# ─────────────────────────────────────────────
# Claude SEO optimisation
# ─────────────────────────────────────────────

SYSTEM_PROMPT = "You are an expert SEO content optimizer. Always respond with valid JSON only, no markdown."

SEO_USER_TEMPLATE = """
Analyse this WordPress post and return a JSON object with SEO optimisations.

POST TITLE: {title}
POST SLUG: {slug}
POST CONTENT (HTML):
{content}

Return ONLY valid JSON (no markdown fences) with exactly these keys:
{{
  "focus_keyword": "the best single focus keyword/phrase for this content",
  "optimized_title": "SEO-optimised title, 50-60 chars, keyword near front",
  "meta_description": "compelling meta description 150-160 chars, keyword included, ends with CTA",
  "optimized_content_html": "full rewritten HTML content with proper H2/H3 structure, keyword in first 100 words, at least 600 words",
  "suggested_slug": "clean-keyword-slug-no-stopwords",
  "reasoning": "brief explanation of changes"
}}
"""


def run_claude_seo(title: str, content_html: str, slug: str,
                   claude_api_key: str, model: str) -> dict:
    client = anthropic.Anthropic(api_key=claude_api_key)
    user_msg = SEO_USER_TEMPLATE.format(
        title=title,
        slug=slug,
        content=html.unescape(content_html or ""),
    )
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = message.content[0].text.strip()
    # Strip possible markdown fences defensively
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


# ─────────────────────────────────────────────
# Pexels + WP media
# ─────────────────────────────────────────────

def fetch_pexels_image(query: str, pexels_key: str) -> tuple[str, str] | None:
    """Return (image_url, photographer) or None."""
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": pexels_key},
            params={"query": query, "per_page": 3, "orientation": "landscape"},
            timeout=15,
        )
        resp.raise_for_status()
        photos = resp.json().get("photos", [])
        if not photos:
            return None
        photo = photos[0]
        url = photo["src"]["large2x"]
        photographer = photo.get("photographer", "Pexels")
        return url, photographer
    except Exception as exc:
        log(f"Pexels error: {exc}")
        return None


def upload_image_to_wp(image_url: str, alt_text: str,
                       wp_url: str, wp_user: str, wp_pass: str) -> tuple[int, str] | None:
    """Download image and upload to WP media. Return (media_id, media_url) or None."""
    try:
        img_resp = requests.get(image_url, timeout=30)
        img_resp.raise_for_status()
        img_bytes = img_resp.content

        # Determine filename & content-type
        filename = image_url.split("/")[-1].split("?")[0] or "image.jpg"
        if not re.search(r"\.(jpg|jpeg|png|webp)$", filename, re.I):
            filename = "pexels-image.jpg"
        content_type = img_resp.headers.get("Content-Type", "image/jpeg")

        files = {
            "file": (filename, io.BytesIO(img_bytes), content_type),
        }
        base = wp_url.rstrip("/") + "/wp-json/wp/v2/media"
        auth = (wp_user, wp_pass)
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        resp = requests.post(base, auth=auth, files=files, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        media_id = data["id"]
        media_url = data.get("source_url", image_url)

        # Update alt text
        requests.post(
            f"{base}/{media_id}",
            auth=auth,
            json={"alt_text": alt_text},
            timeout=15,
        )
        return media_id, media_url
    except Exception as exc:
        log(f"Image upload error: {exc}")
        return None


def insert_inline_image(content_html: str, img_url: str, alt_text: str) -> str:
    """Insert image after the first <p> tag in content."""
    img_tag = f'<img src="{img_url}" alt="{html.escape(alt_text)}" style="max-width:100%;height:auto;margin:1rem 0;" />'
    # Find first closing </p> and insert after
    match = re.search(r"</p>", content_html, re.IGNORECASE)
    if match:
        pos = match.end()
        return content_html[:pos] + "\n" + img_tag + "\n" + content_html[pos:]
    return img_tag + "\n" + content_html


# ─────────────────────────────────────────────
# Full SEO pipeline for a single post
# ─────────────────────────────────────────────

def process_single_post(post: dict, wp_url: str, wp_user: str, wp_pass: str,
                        claude_api_key: str, model: str, pexels_key: str,
                        min_score: int, max_iterations: int,
                        progress_cb=None) -> dict:
    """
    Run the full SEO pipeline on one post.
    Returns a result dict with keys: post_id, title, type, final_score, published, iterations, error.
    """
    post_id = post["id"]
    post_type = post.get("_type", "post")
    endpoint = f"{post_type}s/{post_id}"
    original_title = post.get("title", {}).get("rendered", "")
    original_content = post.get("content", {}).get("rendered", "")
    original_slug = post.get("slug", "")

    result = {
        "post_id": post_id,
        "title": original_title,
        "original_title": original_title,
        "type": post_type,
        "final_score": 0,
        "published": False,
        "iterations": 0,
        "error": None,
        "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "focus_keyword": "",
    }

    log(f"Processing {post_type} #{post_id}: {original_title[:60]}")

    try:
        current_title = original_title
        current_content = original_content
        current_slug = original_slug
        focus_keyword = ""
        featured_image_set = post.get("featured_media", 0) > 0

        for iteration in range(1, max_iterations + 1):
            result["iterations"] = iteration
            log(f"  Iteration {iteration}/{max_iterations} — running Claude SEO optimisation")
            if progress_cb:
                progress_cb((iteration - 1) / max_iterations * 0.6)

            # Claude optimisation
            seo_data = run_claude_seo(
                current_title, current_content, current_slug,
                claude_api_key, model,
            )

            focus_keyword = seo_data.get("focus_keyword", "")
            new_title = seo_data.get("optimized_title", current_title)
            meta_desc = seo_data.get("meta_description", "")
            new_content = seo_data.get("optimized_content_html", current_content)
            new_slug = seo_data.get("suggested_slug", current_slug)

            result["focus_keyword"] = focus_keyword
            log(f"  Focus keyword: {focus_keyword}")

            # Pexels image
            if pexels_key:
                log(f"  Fetching image from Pexels for '{focus_keyword}'")
                img_result = fetch_pexels_image(focus_keyword, pexels_key)
                if img_result:
                    img_url, photographer = img_result
                    alt_text = f"{focus_keyword} - photo by {photographer}"
                    upload_result = upload_image_to_wp(img_url, alt_text, wp_url, wp_user, wp_pass)
                    if upload_result:
                        media_id, media_url = upload_result
                        # Set featured image
                        try:
                            wp_request("POST", endpoint, wp_url, wp_user, wp_pass,
                                       data={"featured_media": media_id})
                            featured_image_set = True
                            log(f"  Featured image set (media ID {media_id})")
                        except RuntimeError as exc:
                            log(f"  Warning: could not set featured image: {exc}")
                        # Insert inline image
                        new_content = insert_inline_image(new_content, media_url, alt_text)
                        log(f"  Inline image inserted")

            if progress_cb:
                progress_cb(iteration / max_iterations * 0.8)

            # Update post in WordPress
            update_data = {
                "title": new_title,
                "content": new_content,
                "slug": new_slug,
                "meta": {
                    "_yoast_wpseo_focuskw": focus_keyword,
                    "_yoast_wpseo_title": new_title,
                    "_yoast_wpseo_metadesc": meta_desc,
                },
            }
            try:
                wp_request("POST", endpoint, wp_url, wp_user, wp_pass, data=update_data)
                log(f"  Post updated in WordPress")
            except RuntimeError as exc:
                log(f"  Warning: post update error: {exc}")

            current_title = new_title
            current_content = new_content
            current_slug = new_slug

            # Score
            score, _ = calculate_seo_score(
                current_title, current_content, meta_desc,
                focus_keyword, current_slug, featured_image_set,
            )
            result["final_score"] = score
            result["title"] = current_title
            log(f"  SEO score after iteration {iteration}: {score}/100")

            if score >= min_score:
                log(f"  Score {score} >= {min_score} — publishing!")
                try:
                    wp_request("POST", endpoint, wp_url, wp_user, wp_pass,
                               data={"status": "publish"})
                    result["published"] = True
                    log(f"  Published successfully!")
                except RuntimeError as exc:
                    log(f"  Publish error: {exc}")
                break
            else:
                log(f"  Score {score} < {min_score} — will iterate again")

        if progress_cb:
            progress_cb(1.0)

    except Exception as exc:
        result["error"] = str(exc)
        log(f"  ERROR: {exc}")

    return result


# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🔌 WordPress Connection")
    wp_url = st.text_input("WP Site URL", placeholder="https://example.com")
    wp_user = st.text_input("WP Username")
    wp_pass = st.text_input(
        "WP Application Password",
        type="password",
        help="Generate in WP Admin > Users > Profile > Application Passwords",
    )
    if st.button("Test Connection"):
        if wp_url and wp_user and wp_pass:
            ok, msg = test_wp_connection(wp_url, wp_user, wp_pass)
            if ok:
                st.success(msg)
            else:
                st.error(msg)
        else:
            st.warning("Fill in all WP fields first.")

    st.markdown("---")
    st.markdown("## 🔑 API Keys")
    claude_api_key = st.text_input("Claude API Key", type="password")
    pexels_api_key = st.text_input("Pexels API Key", type="password")
    model = st.selectbox(
        "Claude Model",
        ["claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
        index=0,
    )

    st.markdown("---")
    st.markdown("## ⚙️ Agent Settings")
    min_seo_score = st.slider("Min SEO Score to Publish", 70, 95, 85)
    auto_check_interval = st.slider("Auto-check Interval (minutes)", 1, 60, 5)
    include_pages = st.checkbox("Include Pages", value=True)
    include_posts = st.checkbox("Include Posts", value=True)
    max_iterations = st.slider("Max Iterations per Post", 1, 5, 3)

# ─────────────────────────────────────────────
# Helpers shared across tabs
# ─────────────────────────────────────────────

def _creds_ok() -> bool:
    return bool(wp_url and wp_user and wp_pass and claude_api_key)


def _refresh_drafts():
    if not (wp_url and wp_user and wp_pass):
        st.warning("Configure WP credentials in the sidebar.")
        return
    try:
        st.session_state.drafts_cache = get_drafts(
            wp_url, wp_user, wp_pass, include_posts, include_pages
        )
        log(f"Fetched {len(st.session_state.drafts_cache)} draft(s)")
    except Exception as exc:
        st.error(f"Error fetching drafts: {exc}")


# ─────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🤖 Auto SEO Agent", "✏️ Manual SEO"])

# ════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ════════════════════════════════════════════
with tab1:
    st.markdown("# WordPress SEO Agent Dashboard")

    # Metric cards
    processed = st.session_state.processed_posts
    today_str = date.today().strftime("%Y-%m-%d")
    published_today = sum(
        1 for p in processed
        if p.get("published") and p.get("processed_at", "").startswith(today_str)
    )
    scores = [p["final_score"] for p in processed if p.get("final_score", 0) > 0]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    agent_status = "🟢 Running" if st.session_state.agent_running else "🔴 Stopped"
    total_drafts = len(st.session_state.drafts_cache)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f'<div class="metric-card"><div style="color:#8B949E;font-size:.85rem;">Total Drafts Found</div>'
            f'<div style="font-size:2rem;font-weight:700;color:#C9D1D9;">{total_drafts}</div></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div class="metric-card"><div style="color:#8B949E;font-size:.85rem;">Published Today</div>'
            f'<div style="font-size:2rem;font-weight:700;color:#10B981;">{published_today}</div></div>',
            unsafe_allow_html=True,
        )
    with col3:
        score_col = "#10B981" if avg_score >= 85 else ("#F59E0B" if avg_score >= 70 else "#EF4444")
        st.markdown(
            f'<div class="metric-card"><div style="color:#8B949E;font-size:.85rem;">Average SEO Score</div>'
            f'<div style="font-size:2rem;font-weight:700;color:{score_col};">{avg_score}</div></div>',
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f'<div class="metric-card"><div style="color:#8B949E;font-size:.85rem;">Agent Status</div>'
            f'<div style="font-size:1.3rem;font-weight:700;color:#C9D1D9;">{agent_status}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    col_left, col_right = st.columns([3, 1])
    with col_left:
        st.markdown("### Recently Processed Posts")
    with col_right:
        if st.button("🔄 Refresh Stats", key="dash_refresh"):
            _refresh_drafts()
            st.rerun()

    if processed:
        import pandas as pd
        df_data = []
        for p in reversed(processed[-50:]):
            score = p.get("final_score", 0)
            score_str = f"{score}/100"
            df_data.append({
                "Title": p.get("title", "")[:60],
                "Type": p.get("type", "post").capitalize(),
                "SEO Score": score_str,
                "Status": "Published ✅" if p.get("published") else ("Error ❌" if p.get("error") else "Optimised 🔧"),
                "Processed At": p.get("processed_at", ""),
            })
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No posts processed yet. Use the Auto SEO Agent or Manual SEO tabs to get started.")

    # Current drafts list
    if st.session_state.drafts_cache:
        st.markdown("### Current Drafts")
        draft_rows = []
        for d in st.session_state.drafts_cache:
            draft_rows.append({
                "ID": d["id"],
                "Title": (d.get("title", {}).get("rendered", "") or "")[:70],
                "Type": d.get("_type", "post").capitalize(),
                "Slug": d.get("slug", ""),
            })
        import pandas as pd
        st.dataframe(pd.DataFrame(draft_rows), use_container_width=True, hide_index=True)

# ════════════════════════════════════════════
# TAB 2 — AUTO SEO AGENT
# ════════════════════════════════════════════
with tab2:
    st.markdown("# 🤖 Auto SEO Agent")

    # Start/stop toggle
    agent_col1, agent_col2 = st.columns([2, 5])
    with agent_col1:
        if st.session_state.agent_running:
            if st.button("⏹ Stop Agent", key="stop_agent"):
                st.session_state.agent_running = False
                log("Agent stopped by user.")
                st.rerun()
        else:
            if st.button("▶ Start Agent", key="start_agent"):
                if not _creds_ok():
                    st.error("Please fill in all credentials in the sidebar before starting.")
                else:
                    st.session_state.agent_running = True
                    log("Agent started.")
                    st.rerun()

    with agent_col2:
        if st.session_state.agent_running:
            st.success("🟢 Agent is RUNNING — click 'Run One Cycle Now' to process drafts.")
        else:
            st.info("🔴 Agent is STOPPED. Click '▶ Start Agent' to enable.")

    st.markdown("---")

    cycle_col1, cycle_col2 = st.columns([2, 5])
    with cycle_col1:
        run_cycle = st.button("⚡ Run One Cycle Now", key="run_cycle",
                              disabled=not st.session_state.agent_running)
    with cycle_col2:
        if st.session_state.last_cycle_time:
            st.caption(f"Last cycle: {st.session_state.last_cycle_time}")

    if run_cycle:
        if not _creds_ok():
            st.error("Please configure credentials in the sidebar.")
        else:
            log("=== Starting new cycle ===")
            _refresh_drafts()
            drafts = st.session_state.drafts_cache

            if not drafts:
                log("No drafts found. Cycle complete.")
                st.info("No draft posts or pages found.")
            else:
                log(f"Found {len(drafts)} draft(s) to process")
                progress_placeholder = st.empty()
                status_placeholder = st.empty()
                overall_bar = progress_placeholder.progress(0)

                for idx, draft in enumerate(drafts):
                    draft_title = (draft.get("title", {}).get("rendered", "") or f"Post #{draft['id']}")[:60]
                    status_placeholder.markdown(f"**Processing:** {draft_title}")

                    post_progress_bar = st.progress(0)

                    def _prog(val, _bar=post_progress_bar):
                        _bar.progress(min(val, 1.0))

                    result = process_single_post(
                        draft, wp_url, wp_user, wp_pass,
                        claude_api_key, model, pexels_api_key,
                        min_seo_score, max_iterations,
                        progress_cb=_prog,
                    )
                    st.session_state.processed_posts.append(result)
                    overall_bar.progress((idx + 1) / len(drafts))

                st.session_state.last_cycle_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                status_placeholder.markdown("**Cycle complete!**")
                log("=== Cycle complete ===")

    # Activity log
    st.markdown("### Activity Log")
    log_html = "<br>".join(st.session_state.agent_log[-100:]) if st.session_state.agent_log else "No activity yet."
    st.markdown(f'<div class="log-box">{log_html}</div>', unsafe_allow_html=True)

    if st.button("🗑 Clear Log", key="clear_log"):
        st.session_state.agent_log = []
        st.rerun()

# ════════════════════════════════════════════
# TAB 3 — MANUAL SEO
# ════════════════════════════════════════════
with tab3:
    st.markdown("# ✏️ Manual SEO Optimisation")

    refresh_manual = st.button("🔄 Refresh Draft List", key="manual_refresh")
    if refresh_manual:
        _refresh_drafts()

    drafts = st.session_state.drafts_cache
    if not drafts:
        st.info("No drafts loaded. Click 'Refresh Draft List' or configure credentials.")
    else:
        draft_options = {
            f"[{d.get('_type','post').upper()}] {(d.get('title',{}).get('rendered','') or 'Untitled')[:60]} (ID:{d['id']})": d
            for d in drafts
        }
        selected_label = st.selectbox("Select a draft post/page", list(draft_options.keys()))
        selected_post = draft_options[selected_label]

        load_col, _ = st.columns([2, 5])
        with load_col:
            load_post = st.button("📂 Load Post", key="load_post")

        if load_post:
            st.session_state.manual_post_data = selected_post
            st.session_state.manual_seo_result = None

        if st.session_state.manual_post_data:
            post = st.session_state.manual_post_data
            title = post.get("title", {}).get("rendered", "") or ""
            content_html = post.get("content", {}).get("rendered", "") or ""
            slug = post.get("slug", "")
            featured_media = post.get("featured_media", 0)

            # Decode HTML entities
            content_html_clean = html.unescape(content_html)

            soup = BeautifulSoup(content_html_clean, "lxml")
            plain_text = soup.get_text(separator=" ")
            words = re.findall(r"\b\w+\b", plain_text)
            word_count = len(words)
            content_preview = plain_text[:200].strip() + ("..." if len(plain_text) > 200 else "")

            # Initial score (no meta, no keyword yet)
            initial_score, initial_criteria = calculate_seo_score(
                title, content_html_clean, "", "", slug, featured_media > 0
            )

            st.markdown("---")
            info_col1, info_col2 = st.columns(2)
            with info_col1:
                st.markdown(f"**Current Title:** {title}")
                st.markdown(f"**Slug:** `{slug}`")
                st.markdown(f"**Word Count:** {word_count}")
                st.markdown(f"**Content Preview:**")
                st.caption(content_preview)

            with info_col2:
                st.markdown("**Current SEO Score:**")
                st.markdown(colored_score_html(initial_score), unsafe_allow_html=True)
                st.markdown("**Score Breakdown:**")
                breakdown_data = [
                    {"Criterion": c["criterion"], "Score": f"{c['score']}/{c['max']}", "Detail": c["detail"]}
                    for c in initial_criteria
                ]
                import pandas as pd
                st.dataframe(pd.DataFrame(breakdown_data), use_container_width=True, hide_index=True)

            st.markdown("---")

            run_seo_btn = st.button("🚀 Run SEO Optimisation", key="run_manual_seo",
                                    disabled=not _creds_ok())
            if not _creds_ok():
                st.caption("⚠️ Configure all credentials in the sidebar to enable.")

            if run_seo_btn:
                with st.status("Running SEO optimisation...", expanded=True) as status_widget:
                    st.write("📡 Calling Claude for SEO analysis...")
                    try:
                        seo_data = run_claude_seo(
                            title, content_html_clean, slug,
                            claude_api_key, model,
                        )
                        focus_keyword = seo_data.get("focus_keyword", "")
                        new_title = seo_data.get("optimized_title", title)
                        meta_desc = seo_data.get("meta_description", "")
                        new_content = seo_data.get("optimized_content_html", content_html_clean)
                        new_slug = seo_data.get("suggested_slug", slug)
                        reasoning = seo_data.get("reasoning", "")

                        st.write(f"✅ Claude responded. Focus keyword: **{focus_keyword}**")
                        st.write(f"💡 Reasoning: {reasoning[:200]}")

                        featured_image_set = featured_media > 0

                        if pexels_api_key:
                            st.write("🖼 Fetching image from Pexels...")
                            img_result = fetch_pexels_image(focus_keyword, pexels_api_key)
                            if img_result:
                                img_url, photographer = img_result
                                alt_text = f"{focus_keyword} - photo by {photographer}"
                                st.write(f"⬆️ Uploading image to WordPress...")
                                upload_result = upload_image_to_wp(
                                    img_url, alt_text, wp_url, wp_user, wp_pass
                                )
                                if upload_result:
                                    media_id, media_url = upload_result
                                    post_type = post.get("_type", "post")
                                    endpoint = f"{post_type}s/{post['id']}"
                                    try:
                                        wp_request("POST", endpoint, wp_url, wp_user, wp_pass,
                                                   data={"featured_media": media_id})
                                        featured_image_set = True
                                        st.write("✅ Featured image set!")
                                    except RuntimeError as exc:
                                        st.write(f"⚠️ Could not set featured image: {exc}")
                                    new_content = insert_inline_image(new_content, media_url, alt_text)
                                    st.write("✅ Inline image inserted")
                            else:
                                st.write("⚠️ No Pexels image found for this keyword.")
                        else:
                            st.write("ℹ️ No Pexels API key — skipping images.")

                        st.write("💾 Updating post in WordPress...")
                        post_type = post.get("_type", "post")
                        endpoint = f"{post_type}s/{post['id']}"
                        update_data = {
                            "title": new_title,
                            "content": new_content,
                            "slug": new_slug,
                            "meta": {
                                "_yoast_wpseo_focuskw": focus_keyword,
                                "_yoast_wpseo_title": new_title,
                                "_yoast_wpseo_metadesc": meta_desc,
                            },
                        }
                        try:
                            wp_request("POST", endpoint, wp_url, wp_user, wp_pass, data=update_data)
                            st.write("✅ Post updated in WordPress!")
                        except RuntimeError as exc:
                            st.write(f"⚠️ Update error: {exc}")

                        new_score, new_criteria = calculate_seo_score(
                            new_title, new_content, meta_desc,
                            focus_keyword, new_slug, featured_image_set,
                        )

                        seo_result = {
                            "focus_keyword": focus_keyword,
                            "new_title": new_title,
                            "meta_desc": meta_desc,
                            "new_content": new_content,
                            "new_slug": new_slug,
                            "new_score": new_score,
                            "new_criteria": new_criteria,
                            "old_title": title,
                            "old_score": initial_score,
                            "featured_image_set": featured_image_set,
                            "reasoning": reasoning,
                        }
                        st.session_state.manual_seo_result = seo_result
                        status_widget.update(label="SEO Optimisation Complete!", state="complete")

                    except json.JSONDecodeError as exc:
                        st.error(f"Claude returned invalid JSON: {exc}")
                        status_widget.update(label="Optimisation failed", state="error")
                    except RuntimeError as exc:
                        st.error(f"Error: {exc}")
                        status_widget.update(label="Optimisation failed", state="error")
                    except Exception as exc:
                        st.error(f"Unexpected error: {exc}")
                        status_widget.update(label="Optimisation failed", state="error")

            # Show results if available
            if st.session_state.manual_seo_result:
                res = st.session_state.manual_seo_result
                st.markdown("---")
                st.markdown("## Before / After Comparison")

                bc1, bc2 = st.columns(2)
                with bc1:
                    st.markdown("### Before")
                    st.markdown(f"**Title:** {res['old_title']}")
                    st.markdown(f"**SEO Score:** ", unsafe_allow_html=False)
                    st.markdown(colored_score_html(res["old_score"]), unsafe_allow_html=True)

                with bc2:
                    st.markdown("### After")
                    st.markdown(f"**Title:** {res['new_title']}")
                    st.markdown(f"**SEO Score:** ", unsafe_allow_html=False)
                    st.markdown(colored_score_html(res["new_score"]), unsafe_allow_html=True)

                st.markdown(f"**Focus Keyword:** `{res['focus_keyword']}`")
                st.markdown(f"**Meta Description:** {res['meta_desc']}")
                st.markdown(f"**New Slug:** `{res['new_slug']}`")
                if res.get("reasoning"):
                    with st.expander("Claude's reasoning"):
                        st.write(res["reasoning"])

                st.markdown("### New SEO Score Breakdown")
                import pandas as pd
                breakdown_new = [
                    {"Criterion": c["criterion"], "Score": f"{c['score']}/{c['max']}", "Detail": c["detail"]}
                    for c in res["new_criteria"]
                ]
                st.dataframe(pd.DataFrame(breakdown_new), use_container_width=True, hide_index=True)

                # Publish button
                new_score = res["new_score"]
                publish_enabled = new_score >= min_seo_score
                if not publish_enabled:
                    st.warning(
                        f"SEO score {new_score} is below the minimum {min_seo_score}. "
                        f"Improve content before publishing."
                    )

                pub_col, _ = st.columns([2, 5])
                with pub_col:
                    if st.button("🚀 Publish Now", key="manual_publish", disabled=not publish_enabled):
                        post_type = st.session_state.manual_post_data.get("_type", "post")
                        post_id = st.session_state.manual_post_data["id"]
                        endpoint = f"{post_type}s/{post_id}"
                        try:
                            wp_request("POST", endpoint, wp_url, wp_user, wp_pass,
                                       data={"status": "publish"})
                            st.success("🎉 Post published successfully!")
                            log(f"Manually published {post_type} #{post_id}")
                            # Record in processed
                            st.session_state.processed_posts.append({
                                "post_id": post_id,
                                "title": res["new_title"],
                                "original_title": res["old_title"],
                                "type": post_type,
                                "final_score": new_score,
                                "published": True,
                                "iterations": 1,
                                "error": None,
                                "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "focus_keyword": res["focus_keyword"],
                            })
                        except RuntimeError as exc:
                            st.error(f"Publish failed: {exc}")
