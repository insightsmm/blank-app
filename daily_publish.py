"""Headless daily blog publisher.

Designed to run on a schedule (cron, GitHub Actions, etc.). Reads config from
environment variables, picks a fresh topic in the configured industry,
generates a fully SEO-optimized post with Claude, and publishes it directly
to a connected WordPress site via the REST API.

Required env:
  ANTHROPIC_API_KEY   Claude API key
  WP_SITE_URL         e.g. https://yourblog.com
  WP_USERNAME         WordPress username
  WP_APP_PASSWORD     WordPress application password
  INDUSTRY            e.g. "SaaS / Software"

Optional env:
  SITE_CONTEXT        1–2 sentence description of the site's audience/niche
  TONE                Professional | Conversational | ... (default: Professional)
  WORD_COUNT          target words (default: 1200)
  STATUS              draft | publish (default: publish)
"""
import os
import sys

from streamlit_app import (
    suggest_topics,
    generate_blog_post,
    publish_to_wordpress,
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
    word_count = int(env("WORD_COUNT", "1200"))
    status = env("STATUS", "publish")

    print(f"[autoblog] Picking topic for {industry}...")
    topics = suggest_topics(industry, site_context, api_key, n=5)
    pick = topics[0]
    print(f"[autoblog] Topic: {pick['title']} (kw: {pick['target_keyword']})")

    print("[autoblog] Generating post...")
    post = generate_blog_post(
        pick["title"], pick["target_keyword"], industry, tone, word_count,
        site_url, site_context, api_key,
    )

    print(f"[autoblog] Publishing to {site_url} as {status}...")
    result = publish_to_wordpress(post, site_url, wp_user, wp_pass, status=status)
    print(f"[autoblog] Done: {result.get('link')}")


if __name__ == "__main__":
    main()
