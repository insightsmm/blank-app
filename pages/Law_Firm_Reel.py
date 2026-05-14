import os
import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(page_title="Law Firm Reel", page_icon="⚖️", layout="wide",
                   initial_sidebar_state="collapsed")

REEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "law_firm_reel.html")

st.markdown(
    """
    <style>
      #MainMenu, footer, header { visibility: hidden; }
      .block-container { padding-top: 1rem; max-width: 980px; }
      h1 { color: #ffd166; font-weight: 900; letter-spacing: -0.5px; }
      .sub { color: #9aa3b2; margin-top: -0.5rem; }
      .script-card {
        background: #161B22; border: 1px solid #21262D; border-radius: 14px;
        padding: 1rem 1.25rem; margin-top: 1rem; color: #E6EDF3;
      }
      .script-card h3 { color: #ffd166; margin-top: 0.5rem; }
      .meta-chip {
        display: inline-block; background: #ef476f; color: #fff;
        padding: 4px 10px; border-radius: 999px; font-size: 12px;
        font-weight: 800; margin-right: 6px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("# Law Firm Cartoon Reel ⚖️")
st.markdown(
    "<div class='sub'>Insight Social Media Management · Tampa Bay attorneys · 9:16 · ~42s</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<span class='meta-chip'>HOOK</span><span class='meta-chip'>AGITATE</span>"
    "<span class='meta-chip'>GAP</span><span class='meta-chip'>OFFER</span>"
    "<span class='meta-chip'>PROOF</span><span class='meta-chip'>CTA</span>",
    unsafe_allow_html=True,
)

with open(REEL_PATH, "r", encoding="utf-8") as f:
    reel_html = f.read()

components.html(reel_html, height=900, scrolling=False)

with open(REEL_PATH, "rb") as f:
    st.download_button(
        "Download standalone HTML reel",
        f,
        file_name="law_firm_reel.html",
        mime="text/html",
        use_container_width=True,
    )

st.markdown("<div class='script-card'>", unsafe_allow_html=True)
st.markdown("### Full script")
st.markdown(
    """
**[0:00–0:04] HOOK**
Your law firm has a billboard on I-275… but you're invisible on Instagram. And that's costing you cases.
*On-screen:* INVISIBLE ONLINE = INVISIBLE TO CLIENTS

**[0:04–0:09] AGITATE**
Every day, someone in Tampa Bay Googles "family lawyer near me," opens Instagram, and picks the attorney whose face they recognize. That used to be the lawyer with the biggest ad budget. Now? It's the one who shows up consistently with content that proves they know their stuff.

**[0:10–0:18] GAP**
Brilliant in the courtroom. Silent on social. A logo for a profile picture. Three posts from 2022. A bio that just says "Attorney at Law." That's not a brand — that's a business card pretending to be a presence.

**[0:19–0:28] OFFER**
I'm Frantz with Insight Social Media Management. I help law firms in Tampa Bay turn their expertise into authority — and their authority into booked consultations. We handle the content, the strategy, the posting, the DMs. You handle the cases.

**[0:29–0:35] PROOF**
We don't do generic "law firm content." We build a footprint that sounds like you, ranks for your city, and pulls in the exact clients you want to sign.

**[0:36–0:42] CTA**
If you're an attorney in Tampa Bay and you're tired of being the best-kept secret in your practice area — comment **AUTHORITY** and I'll send you our law firm content audit. Free. No pitch. Just clarity.
"""
)
st.markdown("</div>", unsafe_allow_html=True)
