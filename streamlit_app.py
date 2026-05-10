import streamlit as st
import anthropic
import requests
import json
import re
import io
from datetime import date
from urllib.parse import urlparse


# ── Page setup & branding ────────────────────────────────────────────────
st.set_page_config(page_title="AutoBlog", page_icon="📝", layout="wide",
                   initial_sidebar_state="collapsed")

LOGO_SVG = """
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 360 64' height='52'>
  <defs>
    <linearGradient id='g' x1='0' x2='1'>
      <stop offset='0' stop-color='#3B82F6'/>
      <stop offset='1' stop-color='#10B981'/>
    </linearGradient>
  </defs>
  <rect x='0' y='4' width='56' height='56' rx='16' fill='url(#g)'/>
  <path d='M18 22 H38 M18 32 H38 M18 42 H32' stroke='white' stroke-width='4' stroke-linecap='round'/>
  <text x='74' y='44' font-family='-apple-system, Inter, system-ui, sans-serif'
        font-size='30' font-weight='800' fill='#E6EDF3' letter-spacing='-0.5'>
    Auto<tspan fill='#10B981'>Blog</tspan>
  </text>
</svg>
"""

CUSTOM_CSS = """
<style>
  #MainMenu, footer, header {visibility: hidden;}
  .block-container {padding-top: 2rem; max-width: 980px;}
  .stButton > button {
    background: linear-gradient(135deg, #3B82F6 0%, #10B981 100%);
    color: white; border: 0; border-radius: 12px;
    padding: 0.75rem 1.5rem; font-weight: 600; font-size: 1rem;
    box-shadow: 0 4px 14px rgba(59,130,246,0.35);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }
  .stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(16,185,129,0.5);
  }
  .stButton > button:disabled {
    background: #1F2937; color: #6B7280; box-shadow: none;
  }
  .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
    background: #161B22 !important; color: #E6EDF3 !important;
    border: 1px solid #21262D !important; border-radius: 12px !important;
  }
  .stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #10B981 !important; box-shadow: 0 0 0 3px rgba(16,185,129,0.2) !important;
  }
  .hero-sub { color: #8B949E; font-size: 1.05rem; margin-top: -0.5rem; }
  .card {
    background: #161B22; border: 1px solid #21262D; border-radius: 16px;
    padding: 1.5rem; margin-top: 1.5rem;
  }
  .pill {
    display: inline-block; padding: 4px 10px; margin: 2px 4px 2px 0;
    background: #0D1117; border: 1px solid #21262D; border-radius: 999px;
    color: #8B949E; font-size: 0.85rem;
  }
  .score {
    font-size: 2.5rem; font-weight: 800; line-height: 1;
    background: linear-gradient(135deg, #3B82F6, #10B981);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown(LOGO_SVG, unsafe_allow_html=True)
st.markdown("<div class='hero-sub'>Daily SEO-optimized blog posts, auto-published to your site.</div>",
            unsafe_allow_html=True)


# ── Generation ──────────────────────────────────────────────────────────
INDUSTRIES = [
    "SaaS / Software", "E-commerce", "Health & Wellness", "Finance & Fintech",
    "Real Estate", "Marketing & Agencies", "Education", "Travel & Hospitality",
    "Food & Beverage", "Legal Services", "Fitness & Sports", "Beauty & Skincare",
    "Home Services", "B2B Services", "Crypto & Web3", "AI & Machine Learning",
]

TONES = ["Professional", "Conversational", "Authoritative expert", "Friendly & casual",
         "Data-driven", "Storytelling"]


def _strip_code_fence(s: str) -> str:
    s = s.strip()
    s = re.sub(r"^```[a-z]*\n?", "", s)
    s = re.sub(r"\n?```$", "", s)
    return s.strip()


def suggest_topics(industry, website_context, api_key, n=5):
    client = anthropic.Anthropic(api_key=api_key)
    prompt = (
        f"Suggest {n} fresh, SEO-driven blog topics for a {industry} business.\n"
        f"Context about the site: {website_context or '(none)'}\n\n"
        "Each topic must target a real search intent, ideally a long-tail keyword "
        "with reasonable difficulty. Mix 'how-to', 'listicle', 'vs/comparison', "
        "and 'beginner guide' formats.\n\n"
        "Return ONLY a JSON array of objects with fields: "
        "title, target_keyword, search_intent (informational|commercial|transactional|navigational), "
        "format (how-to|listicle|comparison|guide|case-study)."
    )
    msg = client.messages.create(
        model="claude-opus-4-5", max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    return json.loads(_strip_code_fence(msg.content[0].text))


def generate_blog_post(topic, target_keyword, industry, tone, word_count,
                       website_url, website_context, api_key):
    client = anthropic.Anthropic(api_key=api_key)
    system = (
        "You are a senior SEO content strategist who writes blog posts that rank "
        "on the first page of Google. You follow Google's E-E-A-T guidelines, "
        "use natural keyword placement (no stuffing), and write for humans first. "
        "You produce clean, semantic HTML."
    )
    user = f"""Write a complete, publication-ready blog post.

Topic: {topic}
Primary keyword: {target_keyword}
Industry: {industry}
Tone: {tone}
Target word count: ~{word_count}
Site: {website_url or '(not provided)'}
Site context: {website_context or '(none)'}

Requirements:
- SEO title: 50–60 chars, include the primary keyword near the front.
- Meta description: 140–158 chars, include keyword, end with a soft CTA.
- URL slug: lowercase, hyphenated, ≤60 chars, keyword-bearing.
- One <h1> at the top, then logical <h2> sections, optional <h3> sub-sections.
- 800–{max(900, word_count + 200)} words. Short paragraphs (≤3 sentences). Scannable.
- Include 1 bulleted or numbered list and at least 1 short table when natural.
- Place the primary keyword in: title, H1, first 100 words, one H2, meta description, and slug.
- Include 4–6 LSI/semantic keywords naturally throughout.
- Include an FAQ section with 4 questions answered concisely (great for People Also Ask).
- Include a 2–3 sentence conclusion with a clear next step.
- Image suggestion: one hero image with descriptive alt text including the keyword.
- Internal link suggestions: 2 (anchor text + target topic).
- External link suggestions: 1–2 to authoritative sources (anchor + URL).

Return ONLY a single JSON object with these fields:
{{
  "seo_title": str,
  "meta_description": str,
  "slug": str,
  "primary_keyword": str,
  "secondary_keywords": [str, ...],
  "html": str,             // full post body as HTML, starting with <h1> and including the FAQ section as <h2>FAQ</h2> with <h3> questions
  "faq": [{{"question": str, "answer": str}}, ...],
  "hero_image": {{"alt": str, "search_query": str}},
  "internal_links": [{{"anchor": str, "topic": str}}, ...],
  "external_links": [{{"anchor": str, "url": str}}, ...],
  "tags": [str, ...],
  "categories": [str, ...]
}}"""
    msg = client.messages.create(
        model="claude-opus-4-5", max_tokens=8000,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return json.loads(_strip_code_fence(msg.content[0].text))


# ── SEO scoring (heuristic, on-page) ────────────────────────────────────
def seo_score(post):
    checks = []
    title = post.get("seo_title", "")
    meta = post.get("meta_description", "")
    slug = post.get("slug", "")
    html = post.get("html", "")
    kw = post.get("primary_keyword", "").lower()
    text = re.sub(r"<[^>]+>", " ", html).lower()
    first_100 = " ".join(text.split()[:100])

    def add(name, ok, hint=""):
        checks.append({"name": name, "ok": bool(ok), "hint": hint})

    add("Title length 50–60 chars", 50 <= len(title) <= 60, f"now {len(title)}")
    add("Meta description 140–158 chars", 140 <= len(meta) <= 158, f"now {len(meta)}")
    add("Keyword in title", kw and kw in title.lower())
    add("Keyword in meta", kw and kw in meta.lower())
    add("Keyword in slug", kw and kw.replace(" ", "-") in slug.lower())
    add("Keyword in first 100 words", kw and kw in first_100)
    add("Has H1", "<h1" in html.lower())
    add("Has ≥3 H2 sections", html.lower().count("<h2") >= 3)
    add("Has list (ul/ol)", "<ul" in html.lower() or "<ol" in html.lower())
    add("Has FAQ section", any(k in html.lower() for k in ["<h2>faq", "frequently asked"]))
    word_count = len(text.split())
    add("Word count ≥ 800", word_count >= 800, f"now {word_count}")
    density = text.count(kw) / max(word_count, 1) * 100 if kw else 0
    add("Keyword density 0.5–2.5%", 0.5 <= density <= 2.5, f"{density:.2f}%")

    passed = sum(1 for c in checks if c["ok"])
    return round(passed / len(checks) * 100), checks


# ── Schema.org JSON-LD ─────────────────────────────────────────────────
def build_jsonld(post, website_url):
    parsed = urlparse(website_url) if website_url else None
    site_name = parsed.netloc if parsed and parsed.netloc else "Your Site"
    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": post.get("seo_title", ""),
        "description": post.get("meta_description", ""),
        "keywords": ", ".join([post.get("primary_keyword", "")] + post.get("secondary_keywords", [])),
        "datePublished": date.today().isoformat(),
        "author": {"@type": "Organization", "name": site_name},
        "publisher": {"@type": "Organization", "name": site_name},
    }
    faq_items = post.get("faq") or []
    if faq_items:
        faq = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q["question"],
                 "acceptedAnswer": {"@type": "Answer", "text": q["answer"]}}
                for q in faq_items
            ],
        }
        return [article, faq]
    return [article]


def html_with_schema(post, website_url):
    schema = build_jsonld(post, website_url)
    schema_tag = (
        "<script type=\"application/ld+json\">\n"
        + json.dumps(schema, indent=2)
        + "\n</script>"
    )
    return post["html"] + "\n\n" + schema_tag


# ── WordPress publishing ────────────────────────────────────────────────
def wp_get_or_create_terms(base, auth, taxonomy, names):
    if not names:
        return []
    ids = []
    endpoint = f"{base}/wp-json/wp/v2/{taxonomy}"
    for name in names:
        r = requests.get(endpoint, params={"search": name}, auth=auth, timeout=20)
        r.raise_for_status()
        match = next((t for t in r.json() if t["name"].lower() == name.lower()), None)
        if match:
            ids.append(match["id"])
            continue
        r = requests.post(endpoint, json={"name": name}, auth=auth, timeout=20)
        if r.status_code in (200, 201):
            ids.append(r.json()["id"])
    return ids


def publish_to_wordpress(post, site_url, username, app_password, status="draft",
                         publish_date=None):
    base = site_url.rstrip("/")
    auth = (username, app_password)
    full_html = html_with_schema(post, site_url)
    payload = {
        "title": post["seo_title"],
        "slug": post["slug"],
        "content": full_html,
        "excerpt": post["meta_description"],
        "status": status,
        "meta": {"description": post["meta_description"]},
    }
    if publish_date:
        payload["date"] = f"{publish_date}T09:00:00"
        if status == "publish":
            payload["status"] = "future" if publish_date > date.today().isoformat() else "publish"
    try:
        cat_ids = wp_get_or_create_terms(base, auth, "categories", post.get("categories") or [])
        tag_ids = wp_get_or_create_terms(base, auth, "tags", post.get("tags") or [])
        if cat_ids:
            payload["categories"] = cat_ids
        if tag_ids:
            payload["tags"] = tag_ids
    except requests.HTTPError as e:
        # taxonomy creation isn't fatal — proceed without if it fails
        st.warning(f"Couldn't sync tags/categories: {e}")
    r = requests.post(f"{base}/wp-json/wp/v2/posts", json=payload, auth=auth, timeout=30)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"WordPress error {r.status_code}: {r.text[:300]}")
    return r.json()


def test_wp_connection(site_url, username, app_password):
    base = site_url.rstrip("/")
    r = requests.get(f"{base}/wp-json/wp/v2/users/me",
                     auth=(username, app_password), timeout=15)
    if r.status_code == 200:
        return True, r.json().get("name", "ok")
    return False, f"{r.status_code}: {r.text[:200]}"


# ── State ───────────────────────────────────────────────────────────────
ss = st.session_state
ss.setdefault("post", None)
ss.setdefault("topic_suggestions", [])
ss.setdefault("selected_topic", "")


# ── UI ──────────────────────────────────────────────────────────────────
tab_generate, tab_publish, tab_settings = st.tabs(["✍️ Generate", "🚀 Publish", "🔌 Site connection"])

with tab_settings:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Connect your WordPress site")
    st.caption("Posts are published via the WordPress REST API using an "
               "[application password](https://wordpress.org/documentation/article/application-passwords/). "
               "Create one under Users → Profile → Application Passwords.")
    site_url = st.text_input("Site URL", value=ss.get("site_url", ""),
                             placeholder="https://yourblog.com", key="site_url")
    col1, col2 = st.columns(2)
    with col1:
        wp_user = st.text_input("WordPress username", value=ss.get("wp_user", ""), key="wp_user")
    with col2:
        wp_pass = st.text_input("Application password", value=ss.get("wp_pass", ""),
                                type="password", key="wp_pass")
    website_context = st.text_area(
        "About your site (1–2 sentences — used for topic ideas & voice)",
        value=ss.get("website_context", ""),
        placeholder="e.g. A boutique fitness studio in Austin focused on strength training for women over 40.",
        key="website_context",
    )
    if st.button("Test connection", disabled=not (site_url and wp_user and wp_pass)):
        ok, info = test_wp_connection(site_url, wp_user, wp_pass)
        if ok:
            st.success(f"Connected as {info}")
        else:
            st.error(f"Connection failed — {info}")
    st.markdown("</div>", unsafe_allow_html=True)


with tab_generate:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    industry = st.selectbox("Industry", INDUSTRIES, key="industry")
    colA, colB = st.columns([3, 1])
    with colA:
        topic = st.text_input(
            "Today's topic",
            value=ss.get("selected_topic", ""),
            placeholder="e.g. how to choose the right CRM for a small agency",
            key="topic_input",
        )
    with colB:
        st.write("")
        st.write("")
        if st.button("✨ Suggest topics", use_container_width=True):
            try:
                key = st.secrets["ANTHROPIC_API_KEY"]
                with st.spinner("Researching topic ideas..."):
                    ss.topic_suggestions = suggest_topics(
                        industry, ss.get("website_context", ""), key
                    )
            except Exception as e:
                st.error(f"Couldn't generate suggestions: {e}")

    if ss.topic_suggestions:
        st.write("**Suggestions** (click to use):")
        for i, sug in enumerate(ss.topic_suggestions):
            cols = st.columns([6, 1])
            with cols[0]:
                st.markdown(
                    f"**{sug['title']}**  \n"
                    f"<span class='pill'>kw: {sug['target_keyword']}</span>"
                    f"<span class='pill'>{sug['search_intent']}</span>"
                    f"<span class='pill'>{sug['format']}</span>",
                    unsafe_allow_html=True,
                )
            with cols[1]:
                if st.button("Use", key=f"use_{i}"):
                    ss.selected_topic = sug["title"]
                    ss["topic_input"] = sug["title"]
                    st.rerun()

    col1, col2, col3 = st.columns(3)
    with col1:
        target_kw = st.text_input("Primary keyword (optional)",
                                  placeholder="auto-fills from topic")
    with col2:
        tone = st.selectbox("Tone", TONES, key="tone")
    with col3:
        word_count = st.slider("Target words", 600, 2500, 1200, step=100)

    go = st.button("Generate blog post", type="primary",
                   disabled=not (topic and topic.strip()),
                   use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if go:
        try:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
        except (KeyError, FileNotFoundError):
            st.error("Missing ANTHROPIC_API_KEY in Streamlit secrets.")
            st.stop()
        kw = target_kw.strip() or topic.strip()
        with st.status("Writing your post...", expanded=True) as status:
            st.write("🔍  Planning structure & keywords...")
            post = generate_blog_post(
                topic.strip(), kw, industry, tone, word_count,
                ss.get("site_url", ""), ss.get("website_context", ""),
                api_key,
            )
            ss.post = post
            st.write("📊  Scoring on-page SEO...")
            status.update(label="✅ Draft ready", state="complete")

if ss.post:
    post = ss.post
    score, checks = seo_score(post)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    cols = st.columns([1, 3])
    with cols[0]:
        st.markdown(f"<div class='score'>{score}</div>"
                    f"<div style='color:#8B949E'>SEO score</div>",
                    unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f"### {post['seo_title']}")
        st.caption(post["meta_description"])
        st.markdown(
            "".join([f"<span class='pill'>{kw}</span>"
                     for kw in [post.get("primary_keyword", "")]
                     + post.get("secondary_keywords", [])]),
            unsafe_allow_html=True,
        )

    with st.expander("SEO checklist", expanded=False):
        for c in checks:
            icon = "✅" if c["ok"] else "⚠️"
            hint = f" — _{c['hint']}_" if c.get("hint") else ""
            st.markdown(f"{icon} {c['name']}{hint}")

    with st.expander("Preview", expanded=True):
        st.markdown(post["html"], unsafe_allow_html=True)

    with st.expander("Search snippet preview"):
        st.markdown(
            f"""
<div style="font-family: arial, sans-serif; max-width: 600px;">
  <div style="color:#8AB4F8; font-size:14px;">{ss.get('site_url','example.com')}/{post['slug']}</div>
  <div style="color:#8AB4F8; font-size:20px; line-height:1.3;">{post['seo_title']}</div>
  <div style="color:#BDC1C6; font-size:14px; line-height:1.4;">{post['meta_description']}</div>
</div>""",
            unsafe_allow_html=True,
        )

    with st.expander("Schema.org JSON-LD"):
        st.code(json.dumps(build_jsonld(post, ss.get("site_url", "")), indent=2),
                language="json")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.download_button(
            "Download HTML",
            data=html_with_schema(post, ss.get("site_url", "")),
            file_name=f"{post['slug']}.html", mime="text/html",
            use_container_width=True,
        )
    with col_b:
        md = (
            f"# {post['seo_title']}\n\n"
            f"_{post['meta_description']}_\n\n"
            + re.sub(r"<[^>]+>", "", post["html"])
        )
        st.download_button(
            "Download Markdown", data=md,
            file_name=f"{post['slug']}.md", mime="text/markdown",
            use_container_width=True,
        )
    with col_c:
        st.download_button(
            "Download JSON", data=json.dumps(post, indent=2),
            file_name=f"{post['slug']}.json", mime="application/json",
            use_container_width=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


with tab_publish:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    if not ss.post:
        st.info("Generate a post first in the **Generate** tab.")
    elif not (ss.get("site_url") and ss.get("wp_user") and ss.get("wp_pass")):
        st.warning("Connect your WordPress site in the **Site connection** tab.")
    else:
        st.subheader("Publish to WordPress")
        st.write(f"**{ss.post['seo_title']}**")
        st.caption(f"→ {ss.site_url.rstrip('/')}/{ss.post['slug']}")
        col1, col2 = st.columns(2)
        with col1:
            pub_status = st.radio("Status", ["draft", "publish", "schedule"],
                                  horizontal=True)
        with col2:
            if pub_status == "schedule":
                pub_date = st.date_input("Publish date", value=date.today())
            else:
                pub_date = None
        if st.button("🚀 Send to WordPress", type="primary", use_container_width=True):
            try:
                with st.spinner("Publishing..."):
                    result = publish_to_wordpress(
                        ss.post, ss.site_url, ss.wp_user, ss.wp_pass,
                        status="publish" if pub_status == "schedule" else pub_status,
                        publish_date=pub_date.isoformat() if pub_date else None,
                    )
                link = result.get("link") or f"{ss.site_url.rstrip('/')}/?p={result.get('id')}"
                st.success(f"Published! [{link}]({link})")
            except Exception as e:
                st.error(f"Publish failed: {e}")

        st.divider()
        st.subheader("Daily auto-publishing")
        st.caption(
            "To publish a fresh post every day automatically, schedule the helper "
            "script `daily_publish.py` (included in this repo) on any cron service "
            "(GitHub Actions, Vercel cron, your own server). It calls the same "
            "generation + WordPress publish flow used here, with your industry and "
            "site context as inputs."
        )
        st.code(
            "# Example GitHub Actions cron (.github/workflows/daily-blog.yml)\n"
            "on:\n"
            "  schedule:\n"
            "    - cron: '0 13 * * *'  # 9am ET daily\n"
            "jobs:\n"
            "  publish:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/checkout@v4\n"
            "      - uses: actions/setup-python@v5\n"
            "        with: { python-version: '3.11' }\n"
            "      - run: pip install -r requirements.txt\n"
            "      - run: python daily_publish.py\n"
            "        env:\n"
            "          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}\n"
            "          WP_SITE_URL: ${{ secrets.WP_SITE_URL }}\n"
            "          WP_USERNAME: ${{ secrets.WP_USERNAME }}\n"
            "          WP_APP_PASSWORD: ${{ secrets.WP_APP_PASSWORD }}\n"
            "          INDUSTRY: 'SaaS / Software'\n"
            "          SITE_CONTEXT: 'A project-management tool for remote agencies.'\n",
            language="yaml",
        )
    st.markdown("</div>", unsafe_allow_html=True)
