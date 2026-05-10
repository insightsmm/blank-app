import streamlit as st
import anthropic
import requests
import tempfile
import os
import json
import re
import base64
import numpy as np
from PIL import Image, ImageDraw, ImageFont


# ── Page setup & branding ────────────────────────────────────────────────
st.set_page_config(page_title="DailyShorts", page_icon="▶", layout="wide",
                   initial_sidebar_state="collapsed")

LOGO_SVG = """
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 320 64' height='52'>
  <defs>
    <linearGradient id='g' x1='0' x2='1'>
      <stop offset='0' stop-color='#3B82F6'/>
      <stop offset='1' stop-color='#8B5CF6'/>
    </linearGradient>
  </defs>
  <rect x='0' y='4' width='56' height='56' rx='16' fill='url(#g)'/>
  <polygon points='22,20 22,44 44,32' fill='white'/>
  <text x='74' y='44' font-family='-apple-system, Inter, system-ui, sans-serif'
        font-size='30' font-weight='800' fill='#E6EDF3' letter-spacing='-0.5'>
    Daily<tspan fill='#3B82F6'>Shorts</tspan>
  </text>
</svg>
"""

CUSTOM_CSS = """
<style>
  #MainMenu, footer, header {visibility: hidden;}
  .block-container {padding-top: 2rem; max-width: 880px;}
  .stButton > button {
    background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%);
    color: white; border: 0; border-radius: 12px;
    padding: 0.75rem 1.5rem; font-weight: 600; font-size: 1rem;
    box-shadow: 0 4px 14px rgba(59,130,246,0.35);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }
  .stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(59,130,246,0.5);
  }
  .stButton > button:disabled {
    background: #1F2937; color: #6B7280; box-shadow: none;
  }
  .stTextInput input, .stTextArea textarea {
    background: #161B22 !important; color: #E6EDF3 !important;
    border: 1px solid #21262D !important; border-radius: 12px !important;
  }
  .stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #3B82F6 !important; box-shadow: 0 0 0 3px rgba(59,130,246,0.2) !important;
  }
  .stSlider [data-baseweb="slider"] > div > div > div {background: #3B82F6;}
  .hero-sub { color: #8B949E; font-size: 1.05rem; margin-top: -0.5rem; }
  .card {
    background: #161B22; border: 1px solid #21262D; border-radius: 16px;
    padding: 1.5rem; margin-top: 1.5rem;
  }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown(LOGO_SVG, unsafe_allow_html=True)
st.markdown("<div class='hero-sub'>Turn any topic into a 9:16 short with AI script, voiceover, and b-roll.</div>",
            unsafe_allow_html=True)


# ── Pipeline functions ──────────────────────────────────────────────────
def synthesize_speech(text, voice_id, api_key):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    payload = {"text": text, "model_id": "eleven_multilingual_v2",
               "voice_settings": {"stability": 0.4, "similarity_boost": 0.75}}
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    return base64.b64decode(data["audio_base64"]), data.get("alignment", {})


def fetch_pexels_video(query, api_key):
    headers = {"Authorization": api_key}
    params = {"query": query, "per_page": 5, "orientation": "portrait"}
    r = requests.get("https://api.pexels.com/videos/search",
                     headers=headers, params=params, timeout=15)
    r.raise_for_status()
    for video in r.json().get("videos", []):
        for vf in video.get("video_files", []):
            if vf.get("width", 0) < vf.get("height", 1):
                resp = requests.get(vf["link"], timeout=30, stream=True)
                resp.raise_for_status()
                tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
                for chunk in resp.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                tmp.close()
                return tmp.name
    return None


def generate_script(topic, num_scenes, api_key):
    client = anthropic.Anthropic(api_key=api_key)
    prompt = ("You are a short-form video scriptwriter.\n"
              + f"Write a {num_scenes}-scene script about: {topic}\n\n"
              + "Return ONLY a JSON array with scene, narration, b_roll_query fields.")
    message = client.messages.create(model="claude-opus-4-5", max_tokens=1024,
                                     messages=[{"role": "user", "content": prompt}])
    raw = message.content[0].text.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def render_word_image(word):
    font = ImageFont.truetype(FONT_PATH, 90)
    tmp = Image.new("RGBA", (10, 10))
    bbox = ImageDraw.Draw(tmp).textbbox((0, 0), word, font=font, stroke_width=6)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = 30
    img = Image.new("RGBA", (text_w + pad * 2, text_h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((pad - bbox[0], pad - bbox[1]), word, font=font,
           fill=(255, 235, 59), stroke_width=6, stroke_fill=(0, 0, 0))
    return np.array(img)


def words_from_alignment(alignment):
    chars = alignment.get("characters", [])
    char_start = alignment.get("character_start_times_seconds", [])
    char_end = alignment.get("character_end_times_seconds", [])
    if not chars or not char_start:
        return []
    out = []
    cur, cs, ce = "", None, None
    for ch, s, e in zip(chars, char_start, char_end):
        if ch == " ":
            if cur:
                out.append((cur, cs, ce))
                cur, cs = "", None
        else:
            if cs is None:
                cs = s
            cur += ch
            ce = e
    if cur:
        out.append((cur, cs, ce))
    return out


def build_video(scenes, audio_paths, alignments):
    from moviepy.editor import (VideoFileClip, AudioFileClip, ImageClip,
                                CompositeVideoClip, concatenate_videoclips, ColorClip)
    W, H = 1080, 1920
    clips = []
    for scene, audio_path, alignment in zip(scenes, audio_paths, alignments):
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        broll_path = scene.get("_broll_path")
        if broll_path and os.path.exists(broll_path):
            bg = (VideoFileClip(broll_path, audio=False)
                  .loop(duration=duration).resize((W, H)).set_duration(duration))
        else:
            bg = ColorClip((W, H), color=(11, 14, 20), duration=duration)
        word_clips = []
        for word, ws, we in words_from_alignment(alignment):
            wdur = max(float(we) - float(ws), 0.1)
            arr = render_word_image(word)
            ic = (ImageClip(arr, transparent=True)
                  .set_start(float(ws)).set_duration(wdur)
                  .set_position(("center", H * 0.72)))
            word_clips.append(ic)
        scene_clip = (CompositeVideoClip([bg] + word_clips, size=(W, H))
                      .set_audio(audio_clip).set_duration(duration))
        clips.append(scene_clip)
    final = concatenate_videoclips(clips, method="compose")
    out_path = tempfile.mktemp(suffix=".mp4")
    final.write_videofile(out_path, fps=30, codec="libx264",
                          audio_codec="aac", threads=2, logger=None)
    return out_path


# ── UI ──────────────────────────────────────────────────────────────────
st.markdown("<div class='card'>", unsafe_allow_html=True)
topic = st.text_input("What's today's video about?",
                      placeholder="e.g. weird facts about octopuses")
num_scenes = st.slider("Number of scenes", 2, 8, 4)
go = st.button("Generate Short", type="primary", disabled=not topic.strip(),
               use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

if go:
    anthropic_key = st.secrets["ANTHROPIC_API_KEY"]
    elevenlabs_key = st.secrets["ELEVENLABS_API_KEY"]
    voice_id = st.secrets["ELEVENLABS_VOICE_ID"]
    pexels_key = st.secrets["PEXELS_API_KEY"]
    with st.status("Working...", expanded=True) as status:
        st.write("✍️  Writing the script with Claude...")
        scenes = generate_script(topic, num_scenes, anthropic_key)
        st.write(f"   {len(scenes)} scenes ready")
        audio_paths, alignments = [], []
        for scene in scenes:
            idx = scene["scene"]
            st.write(f"🎙️  Scene {idx}: voiceover...")
            audio_bytes, alignment = synthesize_speech(scene["narration"], voice_id, elevenlabs_key)
            tmp_audio = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tmp_audio.write(audio_bytes)
            tmp_audio.close()
            audio_paths.append(tmp_audio.name)
            alignments.append(alignment)
            st.write(f"🎬  Scene {idx}: b-roll...")
            scene["_broll_path"] = fetch_pexels_video(scene["b_roll_query"], pexels_key)
        st.write("🎞️  Assembling final video...")
        video_path = build_video(scenes, audio_paths, alignments)
        status.update(label="✅ Done", state="complete")

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.video(video_path)
    with open(video_path, "rb") as f:
        st.download_button("Download MP4", f, file_name="dailyshorts.mp4",
                           mime="video/mp4", use_container_width=True)
    with st.expander("View script"):
        for scene in scenes:
            st.markdown(f"**Scene {scene['scene']}** — _{scene['b_roll_query']}_")
            st.write(scene["narration"])
    st.markdown("</div>", unsafe_allow_html=True)

    for p in audio_paths:
        try: os.unlink(p)
        except Exception: pass
