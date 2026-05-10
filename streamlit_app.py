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


def synthesize_speech(text, voice_id, api_key):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.4, "similarity_boost": 0.75},
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    audio_bytes = base64.b64decode(data["audio_base64"])
    alignment = data.get("alignment", {})
    return audio_bytes, alignment


def fetch_pexels_video(query, api_key):
    headers = {"Authorization": api_key}
    params = {"query": query, "per_page": 5, "orientation": "portrait"}
    r = requests.get("https://api.pexels.com/videos/search",
                     headers=headers, params=params, timeout=15)
    r.raise_for_status()
    videos = r.json().get("videos", [])
    for video in videos:
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
    prompt = (
        "You are a short-form video scriptwriter.\n"
        + f"Write a {num_scenes}-scene script about: {topic}\n\n"
        + "Return ONLY a JSON array with scene, narration, b_roll_query fields."
    )
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def render_word_image(word):
    font = ImageFont.truetype(FONT_PATH, 90)
    tmp = Image.new("RGBA", (10, 10))
    bbox = ImageDraw.Draw(tmp).textbbox((0, 0), word, font=font, stroke_width=6)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
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
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, ImageClip,
        CompositeVideoClip, concatenate_videoclips, ColorClip,
    )
    W, H = 1080, 1920
    clips = []
    for scene, audio_path, alignment in zip(scenes, audio_paths, alignments):
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        broll_path = scene.get("_broll_path")
        if broll_path and os.path.exists(broll_path):
            bg = (VideoFileClip(broll_path, audio=False)
                  .loop(duration=duration)
                  .resize((W, H))
                  .set_duration(duration))
        else:
            bg = ColorClip((W, H), color=(10, 10, 10), duration=duration)
        word_clips = []
        for word, ws, we in words_from_alignment(alignment):
            wdur = max(float(we) - float(ws), 0.1)
            arr = render_word_image(word)
            ic = (ImageClip(arr, transparent=True)
                  .set_start(float(ws))
                  .set_duration(wdur)
                  .set_position(("center", H * 0.72)))
            word_clips.append(ic)
        scene_clip = (CompositeVideoClip([bg] + word_clips, size=(W, H))
                      .set_audio(audio_clip)
                      .set_duration(duration))
        clips.append(scene_clip)
    final = concatenate_videoclips(clips, method="compose")
    out_path = tempfile.mktemp(suffix=".mp4")
    final.write_videofile(out_path, fps=30, codec="libx264",
                          audio_codec="aac", threads=2, logger=None)
    return out_path


st.set_page_config(page_title="Daily Video Generator", page_icon="🎬", layout="centered")
st.title("Daily Animated Video Generator")
st.caption("Topic -> Script -> Voiceover -> B-roll -> 9:16 Short")

topic = st.text_input("Video topic", placeholder="e.g. stoic morning routines")
num_scenes = st.slider("Number of scenes", 2, 8, 4)

if st.button("Generate Video", type="primary", disabled=not topic.strip()):
    anthropic_key = st.secrets["ANTHROPIC_API_KEY"]
    elevenlabs_key = st.secrets["ELEVENLABS_API_KEY"]
    voice_id = st.secrets["ELEVENLABS_VOICE_ID"]
    pexels_key = st.secrets["PEXELS_API_KEY"]
    with st.status("Working...", expanded=True) as status:
        st.write("Writing the script with Claude...")
        scenes = generate_script(topic, num_scenes, anthropic_key)
        st.write("Script ready: " + str(len(scenes)) + " scenes")
        audio_paths, alignments = [], []
        for scene in scenes:
            idx = scene["scene"]
            st.write("Scene " + str(idx) + ": synthesising voiceover...")
            audio_bytes, alignment = synthesize_speech(scene["narration"], voice_id, elevenlabs_key)
            tmp_audio = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tmp_audio.write(audio_bytes)
            tmp_audio.close()
            audio_paths.append(tmp_audio.name)
            alignments.append(alignment)
            st.write("Scene " + str(idx) + ": fetching b-roll...")
            broll_path = fetch_pexels_video(scene["b_roll_query"], pexels_key)
            scene["_broll_path"] = broll_path
        st.write("Assembling video with moviepy...")
        video_path = build_video(scenes, audio_paths, alignments)
        status.update(label="Done!", state="complete")
    with st.expander("Script", expanded=False):
        for scene in scenes:
            st.write("Scene " + str(scene["scene"]) + ": " + scene["narration"])
    with open(video_path, "rb") as f:
        st.download_button("Download Video", f, file_name="daily_video.mp4", mime="video/mp4")
    for p in audio_paths:
        try:
            os.unlink(p)
        except Exception:
            pass
