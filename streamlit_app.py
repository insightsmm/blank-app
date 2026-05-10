import streamlit as st
import anthropic
import requests
import json
import re
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


# ── Defaults ───────────────────────────────────────────────────────────
INDUSTRIES = [
    "SaaS / Software", "E-commerce", "Health & Wellness", "Finance & Fintech",
    "Real Estate", "Marketing & Agencies", "Education", "Travel & Hospitality",
    "Food & Beverage", "Legal Services", "Fitness & Sports", "Beauty & Skincare",
    "Home Services", "B2B Services", "Crypto & Web3", "AI & Machine Learning",
    "Coaching & Consulting",
]

TONES = ["Professional", "Conversational", "Authoritative expert", "Friendly & casual",
         "Data-driven", "Storytelling"]

DEFAULT_FRAMEWORKS = """\
TPO Method (Target / Problem / Outcome)
- Target: who the post is for and the context they're in.
- Problem: the specific friction or pain they're stuck on.
- Outcome: what success looks like once they apply the post.

3Cs (Clarity / Conciseness / Consistency)
- Clarity: one idea per paragraph, plain language.
- Conciseness: every sentence earns its place.
- Consistency: voice, terms, and formatting don't drift.

Clarity Mirror Method
- Mirror the reader's current thought/feeling before introducing the insight.
- Restate their internal monologue so they feel seen.
- Then bridge to the new perspective or actionable step.
"""


def _strip_code_fence(s: str) -> str:
    s = s.strip()
    s = re.sub(r"^```[a-z]*\n?", "", s)
    s = re.sub(r"\n?```$", "", s)
    return s.strip()


# ── Image sourcing (Pexels) ────────────────────────────────────────────
def fetch_pexels_image(query, api_key, orientation="landscape"):
    """Return (url, photographer, photographer_url) or (None, None, None)."""
    if not api_key or not query:
        return None, None, None
    try:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": api_key},
            params={"query": query, "per_page": 1, "orientation": orientation,
                    "size": "large"},
            timeout=15,
        )
        if r.status_code != 200:
            return None, None, None
        photos = r.json().get("photos", [])
        if not photos:
            return None, None, None
        p = photos[0]
        url = (p.get("src") or {}).get("large2x") or (p.get("src") or {}).get("large")
        return url, p.get("photographer"), p.get("photographer_url")
    except requests.RequestException:
        return None, None, None


def _img_figure(url, alt, credit_name=None, credit_url=None):
    cap = ""
    if credit_name:
        if credit_url:
            cap = (f'<figcaption style="font-size:0.85em;color:#666;">'
                   f'Photo by <a href="{credit_url}" target="_blank" '
                   f'rel="noopener nofollow">{credit_name}</a> on Pexels'
                   f'</figcaption>')
        else:
            cap = (f'<figcaption style="font-size:0.85em;color:#666;">'
                   f'Photo by {credit_name} on Pexels</figcaption>')
    return (f'<figure>\n  <img src="{url}" alt="{alt}" loading="lazy" '
            f'style="width:100%;height:auto;border-radius:8px;">\n  {cap}\n</figure>')


def inject_images(post, pexels_key):
    """Resolve image queries to real Pexels URLs and inject <figure> tags
    into post['html'] (hero after H1, plus one image after the first H2)."""
    html = post.get("html", "") or ""
    images = post.get("images") or []
    if not images:
        # Fall back to hero_image suggestion only
        hi = post.get("hero_image") or {}
        if hi.get("search_query"):
            images = [{"position": "hero", "alt": hi.get("alt", ""),
                       "search_query": hi["search_query"]}]
    placed = []

    def place(spec, html_in):
        url, name, prof_url = fetch_pexels_image(spec.get("search_query", ""), pexels_key)
        if not url:
            return html_in, None
        fig = _img_figure(url, spec.get("alt", ""), name, prof_url)
        position = spec.get("position", "hero")
        if position == "hero":
            # insert after the closing </h1>
            m = re.search(r"</h1>", html_in, flags=re.IGNORECASE)
            if m:
                html_in = html_in[: m.end()] + "\n" + fig + "\n" + html_in[m.end():]
            else:
                html_in = fig + "\n" + html_in
        else:
            # insert after the first </h2>
            m = re.search(r"</h2>", html_in, flags=re.IGNORECASE)
            if m:
                html_in = html_in[: m.end()] + "\n" + fig + "\n" + html_in[m.end():]
            else:
                html_in += "\n" + fig
        return html_in, {"url": url, "alt": spec.get("alt", ""),
                         "credit": name, "credit_url": prof_url,
                         "position": position}

    # Place at most one hero + one inline
    hero = next((i for i in images if i.get("position", "hero") == "hero"), None)
    inline = next((i for i in images if i.get("position") and
                   i["position"] != "hero"), None)
    if hero:
        html, info = place(hero, html)
        if info:
            placed.append(info)
    if inline:
        html, info = place(inline, html)
        if info:
            placed.append(info)

    post["html"] = html
    post["resolved_images"] = placed
    return post


# ── WordPress helpers ──────────────────────────────────────────────────
def wp_fetch_recent_posts(site_url, username, app_password, n=50):
    """Pull recent published posts to use as the internal-link pool."""
    base = site_url.rstrip("/")
    auth = (username, app_password)
    out = []
    try:
        r = requests.get(
            f"{base}/wp-json/wp/v2/posts",
            params={"per_page": min(n, 100), "status": "publish",
                    "_fields": "id,title,link,excerpt"},
            auth=auth, timeout=20,
        )
        if r.status_code != 200:
            return out
        for p in r.json():
            title = re.sub(r"<[^>]+>", "", (p.get("title") or {}).get("rendered", "")).strip()
            link = p.get("link") or ""
            excerpt = re.sub(r"<[^>]+>", "",
                             (p.get("excerpt") or {}).get("rendered", "")).strip()
            if title and link:
                out.append({"title": title, "url": link, "excerpt": excerpt[:160]})
    except requests.RequestException:
        pass
    return out


def wp_get_or_create_terms(base, auth, taxonomy, names):
    if not names:
        return []
    ids = []
    endpoint = f"{base}/wp-json/wp/v2/{taxonomy}"
    for name in names:
        r = requests.get(endpoint, params={"search": name}, auth=auth, timeout=20)
        if r.status_code != 200:
            continue
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


# ── Generation ─────────────────────────────────────────────────────────
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


def _build_internal_link_block(pool, max_show=25):
    if not pool:
        return ("(No existing posts available — internal_links may be empty. "
                "Do NOT invent internal URLs.)")
    lines = []
    for p in pool[:max_show]:
        line = f"- {p['title']} — {p['url']}"
        if p.get("excerpt"):
            line += f"  ({p['excerpt']})"
        lines.append(line)
    return "\n".join(lines)


def generate_blog_post(topic, target_keyword, industry, tone, word_count,
                       website_url, website_context, frameworks,
                       internal_link_pool, api_key):
    client = anthropic.Anthropic(api_key=api_key)
    system = (
        "You are a senior SEO content strategist who writes blog posts that hit "
        "100/100 on on-page SEO scoring (Yoast/RankMath standards). You follow "
        "Google's E-E-A-T guidelines, write for humans first, and use natural "
        "keyword placement (zero stuffing). Output is clean, semantic HTML."
    )
    link_block = _build_internal_link_block(internal_link_pool)
    user = f"""Write a complete, publication-ready blog post.

Topic: {topic}
Primary keyword: {target_keyword}
Industry: {industry}
Tone: {tone}
Target word count: {max(1500, word_count)}
Site: {website_url or '(not provided)'}
Site context: {website_context or '(none)'}

REQUIRED FRAMEWORKS — every post MUST visibly apply ALL of these:
{frameworks.strip()}

Apply them in the post body using clearly labeled blocks/sub-sections, e.g.
<h3>Applying the TPO Method</h3>, <h3>Through the 3Cs Lens</h3>,
<h3>Clarity Mirror</h3>. Don't just name them — show how the framework
shapes the reader's thinking on this specific topic.

INTERNAL LINK POOL (the ONLY valid internal URLs — pick 3–4 most relevant
and weave them into the body with natural anchor text. If a perfect match
isn't here, pick the closest. Do NOT fabricate internal URLs.):
{link_block}

ON-PAGE SEO REQUIREMENTS — every single one is mandatory:
1.  SEO title 50–60 chars, primary keyword in the first 4 words.
2.  Meta description 140–158 chars, includes the keyword, ends with a soft CTA.
3.  URL slug ≤ 60 chars, lowercase, hyphenated, contains the keyword.
4.  Exactly one <h1> at the top, contains the primary keyword.
5.  At least 4 <h2> sections; at least 3 <h3> sub-sections total.
6.  1500–2000 words. Short paragraphs (≤3 sentences). Highly scannable.
7.  Primary keyword density 1.0–2.0%. Do not stuff.
8.  At least 6 LSI/semantic keywords used naturally throughout.
9.  Primary keyword appears in: title, H1, first 100 words, ≥2 H2s,
    conclusion, slug, and meta description.
10. At least 1 numbered list, 1 bulleted list, and 1 short comparison table.
11. 3–4 in-body internal links chosen ONLY from the pool above, with
    descriptive (not "click here") anchor text. Inline as <a href="…">.
12. 2 external links to authoritative sources (.gov, .edu, major
    publications, primary research). Inline as <a href="…" target="_blank" rel="noopener">.
13. FAQ section as <h2>FAQ</h2> with 4 <h3> question sub-headings, each
    answered in 2–3 sentences (optimized for People Also Ask).
14. Provide TWO image specs in the `images` field: one "hero" and one
    "inline" (placed after the first H2). For each, give an alt text that
    contains the primary keyword AND a concrete, photogenic search_query
    (Pexels-friendly: real-world subjects, e.g. "team strategy meeting
    whiteboard" — not abstract concepts). Do NOT include <img> tags in the
    HTML; the app will inject them.
15. Conclusion ≥3 sentences with a clear, specific next-step CTA.
16. Add a Table of Contents at the top: <nav class="toc"> with anchor links
    to each H2 (use slugified ids on the H2s).

Return ONLY a single JSON object with these fields (no prose, no fences):
{{
  "seo_title": str,
  "meta_description": str,
  "slug": str,
  "primary_keyword": str,
  "secondary_keywords": [str, ...],          // ≥6 items
  "html": str,                               // full body HTML starting with <h1>, includes TOC, FAQ, internal & external <a> tags inline
  "faq": [{{"question": str, "answer": str}}, ...],  // 4 items
  "hero_image": {{"alt": str, "search_query": str}},
  "images": [                                // exactly 2 items (hero + inline)
    {{"position": "hero",   "alt": str, "search_query": str}},
    {{"position": "inline", "alt": str, "search_query": str}}
  ],
  "internal_links_used": [{{"anchor": str, "url": str}}, ...],  // 3–4 items, URLs must come from the pool
  "external_links": [{{"anchor": str, "url": str}}, ...],       // 2 items
  "tags": [str, ...],
  "categories": [str, ...]
}}"""
    msg = client.messages.create(
        model="claude-opus-4-5", max_tokens=12000,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return json.loads(_strip_code_fence(msg.content[0].text))


def refine_blog_post(post, failing_checks, frameworks, internal_link_pool, api_key):
    """Ask Claude to fix the specific failing SEO checks without rewriting from scratch."""
    if not failing_checks:
        return post
    client = anthropic.Anthropic(api_key=api_key)
    issues = "\n".join(
        f"- {c['name']}" + (f" (currently: {c['hint']})" if c.get("hint") else "")
        for c in failing_checks
    )
    link_block = _build_internal_link_block(internal_link_pool)
    user = f"""Here is a JSON blog-post object. Fix ONLY the failing on-page SEO
checks listed below by editing the relevant fields. Preserve everything else
(voice, framework sections, structure). Keep all required frameworks visibly
applied. Internal links must still come from the pool.

Failing checks:
{issues}

Internal link pool:
{link_block}

Required frameworks (must remain visibly applied):
{frameworks.strip()}

Current post JSON:
{json.dumps(post)}

Return ONLY the corrected JSON object with the same shape."""
    msg = client.messages.create(
        model="claude-opus-4-5", max_tokens=12000,
        messages=[{"role": "user", "content": user}],
    )
    try:
        return json.loads(_strip_code_fence(msg.content[0].text))
    except json.JSONDecodeError:
        return post


# ── SEO scoring (rigorous — targets 100/100) ───────────────────────────
def seo_score(post, frameworks_text=""):
    checks = []
    title = post.get("seo_title", "")
    meta = post.get("meta_description", "")
    slug = post.get("slug", "")
    html = post.get("html", "") or ""
    html_l = html.lower()
    kw = (post.get("primary_keyword") or "").lower().strip()
    text = re.sub(r"<[^>]+>", " ", html).lower()
    words = text.split()
    word_count = len(words)
    first_100 = " ".join(words[:100])

    def add(name, ok, hint=""):
        checks.append({"name": name, "ok": bool(ok), "hint": hint})

    add("Title 50–60 chars", 50 <= len(title) <= 60, f"now {len(title)}")
    add("Meta 140–158 chars", 140 <= len(meta) <= 158, f"now {len(meta)}")
    add("Keyword in title", kw and kw in title.lower())
    add("Keyword in first 4 words of title",
        kw and kw in " ".join(title.lower().split()[:4]))
    add("Keyword in meta", kw and kw in meta.lower())
    add("Slug ≤ 60 chars & has keyword",
        len(slug) <= 60 and kw and kw.replace(" ", "-") in slug.lower())
    add("Keyword in first 100 words", kw and kw in first_100)
    add("Single H1 with keyword",
        html_l.count("<h1") == 1 and kw and re.search(
            r"<h1[^>]*>([\s\S]*?)</h1>", html_l).group(1).find(kw) != -1
        if "<h1" in html_l else False)
    add("≥4 H2 sections", html_l.count("<h2") >= 4,
        f"now {html_l.count('<h2')}")
    add("≥3 H3 sections", html_l.count("<h3") >= 3,
        f"now {html_l.count('<h3')}")
    add("Has numbered list", "<ol" in html_l)
    add("Has bulleted list", "<ul" in html_l)
    add("Has table", "<table" in html_l)
    add("Has FAQ section", "<h2" in html_l and "faq" in html_l)
    add("Word count 1500–2200", 1500 <= word_count <= 2200,
        f"now {word_count}")
    density = (text.count(kw) / max(word_count, 1) * 100) if kw else 0
    add("Keyword density 1.0–2.0%", 1.0 <= density <= 2.0,
        f"{density:.2f}%")
    add("≥6 secondary keywords",
        len(post.get("secondary_keywords") or []) >= 6,
        f"now {len(post.get('secondary_keywords') or [])}")
    internal_used = post.get("internal_links_used") or []
    add("≥3 internal links", len(internal_used) >= 3,
        f"now {len(internal_used)}")
    add("Internal links present in HTML",
        all(li.get("url", "") and li["url"] in html for li in internal_used)
        if internal_used else False)
    ext = post.get("external_links") or []
    add("≥2 external links", len(ext) >= 2, f"now {len(ext)}")
    add("Has Table of Contents",
        "toc" in html_l or html_l.count("<nav") >= 1)
    add("Hero image alt has keyword",
        kw and kw in (post.get("hero_image") or {}).get("alt", "").lower())
    img_count = html_l.count("<img")
    add("≥2 images with alt text",
        img_count >= 2 and len(re.findall(r'<img[^>]+alt="[^"]+"', html, re.I)) >= 2,
        f"now {img_count}")
    # Required frameworks must each appear in headings or labels
    framework_names = []
    for line in frameworks_text.splitlines():
        line = line.strip()
        if line and not line.startswith("-") and "(" in line:
            framework_names.append(line.split("(")[0].strip().lower())
        elif line and not line.startswith("-") and len(line) < 60:
            framework_names.append(line.lower())
    framework_names = [n for n in framework_names if n]
    if framework_names:
        for name in framework_names:
            add(f"Applies '{name}'", name in html_l)

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
        "keywords": ", ".join(
            [post.get("primary_keyword", "")] + post.get("secondary_keywords", [])
        ),
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


# ── State ──────────────────────────────────────────────────────────────
ss = st.session_state
ss.setdefault("post", None)
ss.setdefault("topic_suggestions", [])
ss.setdefault("selected_topic", "")
ss.setdefault("frameworks", DEFAULT_FRAMEWORKS)
ss.setdefault("last_publish_link", "")


def _generate_with_self_heal(topic, target_kw, industry, tone, word_count,
                             site_url, site_context, frameworks, link_pool,
                             api_key, pexels_key, status_box):
    status_box.write("📥  Pulling internal-link pool from your site...")
    status_box.write(f"   Found {len(link_pool)} existing posts to link to")
    status_box.write("✍️   Drafting the post (frameworks + SEO requirements applied)...")
    post = generate_blog_post(
        topic, target_kw, industry, tone, word_count,
        site_url, site_context, frameworks, link_pool, api_key,
    )
    if pexels_key:
        status_box.write("🖼️   Fetching relevant images from Pexels...")
        post = inject_images(post, pexels_key)
        status_box.write(f"   Embedded {len(post.get('resolved_images', []))} images")
    score, checks = seo_score(post, frameworks)
    status_box.write(f"📊  Initial SEO score: {score}/100")
    refines = 0
    while score < 100 and refines < 2:
        failing = [c for c in checks if not c["ok"]]
        status_box.write(f"🔧  Refining {len(failing)} issues (pass {refines + 1})...")
        post = refine_blog_post(post, failing, frameworks, link_pool, api_key)
        # Re-inject images if the refine pass dropped them
        if pexels_key and post.get("html", "").lower().count("<img") < 2:
            post = inject_images(post, pexels_key)
        score, checks = seo_score(post, frameworks)
        status_box.write(f"📊  Score after refine: {score}/100")
        refines += 1
    return post, score, checks


# ── UI ─────────────────────────────────────────────────────────────────
tab_generate, tab_publish, tab_settings = st.tabs(
    ["✍️ Generate", "🚀 Publish", "🔌 Site connection"]
)

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
            pool = wp_fetch_recent_posts(site_url, wp_user, wp_pass, n=50)
            st.caption(f"Internal-link pool: {len(pool)} published posts available.")
        else:
            st.error(f"Connection failed — {info}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Required frameworks")
    st.caption("Every post will visibly apply these. Edit to match your "
               "proprietary methodology.")
    ss.frameworks = st.text_area("Frameworks", value=ss.frameworks, height=320)
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
        word_count = st.slider("Target words", 1200, 2500, 1700, step=100)

    wp_connected = bool(ss.get("site_url") and ss.get("wp_user") and ss.get("wp_pass"))
    pub_choice = st.radio(
        "When ready",
        ["Generate only", "Generate & publish to WordPress",
         "Generate & save as draft on WordPress"],
        horizontal=False,
        index=1 if wp_connected else 0,
        disabled=not wp_connected,
        help=None if wp_connected else
        "Connect your WordPress site in the **Site connection** tab to enable auto-publish.",
    )

    go = st.button(
        "🚀 Generate" + (" & publish" if "publish" in pub_choice.lower() else
                          " & save draft" if "draft" in pub_choice.lower() else ""),
        type="primary",
        disabled=not (topic and topic.strip()),
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if go:
        try:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
        except (KeyError, FileNotFoundError):
            st.error("Missing ANTHROPIC_API_KEY in Streamlit secrets.")
            st.stop()
        kw = target_kw.strip() or topic.strip()
        link_pool = []
        if wp_connected:
            link_pool = wp_fetch_recent_posts(
                ss.site_url, ss.wp_user, ss.wp_pass, n=50,
            )
        pexels_key = ""
        try:
            pexels_key = st.secrets.get("PEXELS_API_KEY", "")
        except Exception:
            pass
        with st.status("Working on your post...", expanded=True) as status_box:
            post, score, checks = _generate_with_self_heal(
                topic.strip(), kw, industry, tone, word_count,
                ss.get("site_url", ""), ss.get("website_context", ""),
                ss.frameworks, link_pool, api_key, pexels_key, status_box,
            )
            ss.post = post
            ss.last_score = score
            ss.last_checks = checks

            if pub_choice != "Generate only" and wp_connected:
                wp_status = "publish" if "publish" in pub_choice.lower() else "draft"
                status_box.write(f"📤  Sending to WordPress as **{wp_status}**...")
                try:
                    result = publish_to_wordpress(
                        post, ss.site_url, ss.wp_user, ss.wp_pass, status=wp_status,
                    )
                    ss.last_publish_link = result.get("link", "")
                    status_box.write(f"✅  Live at {ss.last_publish_link}")
                except Exception as e:
                    status_box.write(f"⚠️  Publish failed: {e}")
            status_box.update(label=f"✅ Done · SEO {score}/100", state="complete")

if ss.post:
    post = ss.post
    score = ss.get("last_score", seo_score(post, ss.frameworks)[0])
    checks = ss.get("last_checks", seo_score(post, ss.frameworks)[1])

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
        if ss.get("last_publish_link"):
            st.success(f"Published: [{ss.last_publish_link}]({ss.last_publish_link})")

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
                ss.last_publish_link = link
                st.success(f"Published! [{link}]({link})")
            except Exception as e:
                st.error(f"Publish failed: {e}")

        st.divider()
        st.subheader("Daily auto-publishing")
        st.caption(
            "To publish a fresh post every day automatically, schedule the helper "
            "script `daily_publish.py` (included in this repo) on any cron service "
            "(GitHub Actions, Vercel cron, your own server). It calls the same "
            "generation + WordPress publish flow used here, with your industry, "
            "site context, and required frameworks as inputs."
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
            "          INDUSTRY: 'Coaching & Consulting'\n"
            "          SITE_CONTEXT: 'A coaching practice teaching the TPO method, 3Cs, and Clarity Mirror.'\n",
            language="yaml",
        )
    st.markdown("</div>", unsafe_allow_html=True)
