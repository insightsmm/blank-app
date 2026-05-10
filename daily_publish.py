"""Headless daily blog publisher.

Designed to run on a schedule (cron, GitHub Actions, etc.). Reads config from
environment variables, picks a fresh topic in the configured industry,
generates a fully SEO-optimized post (with TPO / 3Cs / Clarity Mirror frameworks
applied, real internal links pulled from the live WordPress site, and Pexels
images injected), and publishes it directly to a connected WordPress site via
the REST API.

Required env:
  ANTHROPIC_API_KEY   Claude API key
  WP_SITE_URL         e.g. https://yourblog.com
  WP_USERNAME         WordPress username
  WP_APP_PASSWORD     WordPress application password
  INDUSTRY            e.g. "Coaching & Consulting"

Optional env:
  SITE_CONTEXT        1–2 sentence description of the site's audience/niche
  TONE                Professional | Conversational | ... (default: Professional)
  WORD_COUNT          target words (default: 1700)
  STATUS              draft | publish (default: publish)
  PEXELS_API_KEY      enables relevant hero + inline images
  FRAMEWORKS          override the default TPO / 3Cs / Clarity Mirror text
"""
import os
import sys

from streamlit_app import (
    DEFAULT_FRAMEWORKS,
    suggest_topics,
    generate_blog_post,
    inject_images,
    publish_to_wordpress,
    refine_blog_post,
    seo_score,
    wp_fetch_recent_posts,
)


def env(name, default=None, required=False):
    val = os.environ.get(name, default)
    if required and not val:
        print(f"Missing required env var: {name}", file=sys.stderr)
        sys.exit(1)
    return val


def main():
    api_key = env("ANTHROPIC_API_KEY", required=True)
    site_url = env("WP_SITE_URL", required=True)
    wp_user = env("WP_USERNAME", required=True)
    wp_pass = env("WP_APP_PASSWORD", required=True)
    industry = env("INDUSTRY", required=True)
    site_context = env("SITE_CONTEXT", "")
    tone = env("TONE", "Professional")
    word_count = int(env("WORD_COUNT", "1700"))
    status = env("STATUS", "publish")
    pexels_key = env("PEXELS_API_KEY", "")
    frameworks = env("FRAMEWORKS", DEFAULT_FRAMEWORKS)

    print(f"[autoblog] Picking topic for {industry}...")
    topics = suggest_topics(industry, site_context, api_key, n=5)
    pick = topics[0]
    print(f"[autoblog] Topic: {pick['title']} (kw: {pick['target_keyword']})")

    print("[autoblog] Pulling internal-link pool from WordPress...")
    link_pool = wp_fetch_recent_posts(site_url, wp_user, wp_pass, n=50)
    print(f"[autoblog]   {len(link_pool)} existing posts available")

    print("[autoblog] Generating post...")
    post = generate_blog_post(
        pick["title"], pick["target_keyword"], industry, tone, word_count,
        site_url, site_context, frameworks, link_pool, api_key,
    )

    if pexels_key:
        print("[autoblog] Injecting Pexels images...")
        post = inject_images(post, pexels_key)

    score, checks = seo_score(post, frameworks)
    print(f"[autoblog] Initial SEO score: {score}/100")
    refines = 0
    while score < 100 and refines < 2:
        failing = [c for c in checks if not c["ok"]]
        print(f"[autoblog] Refining {len(failing)} issues...")
        post = refine_blog_post(post, failing, frameworks, link_pool, api_key)
        if pexels_key and post.get("html", "").lower().count("<img") < 2:
            post = inject_images(post, pexels_key)
        score, checks = seo_score(post, frameworks)
        print(f"[autoblog] Score after refine: {score}/100")
        refines += 1

    print(f"[autoblog] Publishing to {site_url} as {status}...")
    result = publish_to_wordpress(post, site_url, wp_user, wp_pass, status=status)
    print(f"[autoblog] Done: {result.get('link')} (score {score}/100)")


if __name__ == "__main__":
    main()
