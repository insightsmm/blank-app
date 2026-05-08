import streamlit as st
import anthropic
import requests
import tempfile
import os
import json
import re
import base64


# ── ElevenLabs ──────────────────────────────────────────────────────────────
def synthesize_speech(text: str, voice_id: str, api_key: str):
        """Call ElevenLabs TTS with character-level alignment."""
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


# ── Pexels ───────────────────────────────────────────────────────────────────
def fetch_pexels_video(query: str, api_key: str):
        """Download a vertical (portrait) Pexels video and return local path."""
        headers = {"Authorization": api_key}
        params = {"query": query, "per_page": 5, "orientation": "portrait"}
        r = requests.get(
            "https://api.pexels.com/videos/search",
            headers=headers,
            params=params,
            timeout=15,
        )
        r.raise_for_status()
        videos = r.json().get("videos", [])
        for video in videos:
                    for vf in video.get("video_files", []):
                                    if vf.get("width", 0) < vf.get("height", 1):
                                                        video_url = vf["link"]
                                                        resp = requests.get(video_url, timeout=30, stream=True)
                                                        resp.raise_for_status()
                                                        tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
                                                        for chunk in resp.iter_content(chunk_size=8192):
                                                                                tmp.write(chunk)
                                                                            tmp.close()
                                                        return tmp.name
                                            return None


# ── Claude script writer ──────────────────────────────────────────────────────
def generate_script(topic: str, num_scenes: int, api_key: str):
        """Ask Claude for a scene-by-scene JSON script."""
        client = anthropic.Anthropic(api_key=api_key)
        prompt = (
            f"You are a short-form video scriptwriter.\n"
            f"Write a {num_scenes}-scene script for a 9:16 vertical video about: {topic}\n\n"
            "Return ONLY a JSON array. Each element must have:\n"
            '  "scene": integer starting at 1\n'
            '  "narration": string (15-25 words, punchy)\n'
            '  "b_roll_query": string (2-4 words for a Pexels video search)\n'
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


# ── moviepy assembly ──────────────────────────────────────────────────────────
def build_video(scenes, audio_paths, alignments):
        """Stitch b-roll + voiceover + pop captions into one MP4."""
        from moviepy.editor import (
            VideoFileClip,
            AudioFileClip,
            TextClip,
            CompositeVideoClip,
            concatenate_videoclips,
            ColorClip,
    )

    W, H = 1080, 1920
    clips = []

    for scene, audio_path, alignment in zip(scenes, audio_paths, alignments):
                audio_clip = AudioFileClip(audio_path)
                duration = audio_clip.duration

        broll_path = scene.get("_broll_path")
        if broll_path and os.path.exists(broll_path):
                        bg = (
                                            VideoFileClip(broll_path, audio=False)
                                            .loop(duration=duration)
                                            .resize((W, H))
                                            .set_duration(duration)
                        )
else:
                bg = ColorClip((W, H), color=(10, 10, 10), duration=duration)

        chars = alignment.get("characters", [])
        char_start = alignment.get("character_start_times_seconds", [])
        char_end = alignment.get("character_end_times_seconds", [])

        word_clips = []
        if chars and char_start:
                        words, starts, ends = [], [], []
                        cur_word, cur_start, cur_end = "", None, None
                        for ch, cs, ce in zip(chars, char_start, char_end):
                                            if ch == " ":
                                                                    if cur_word:
                                                                                                words.append(cur_word)
                                                                                                starts.append(cur_start)
                                                                                                ends.append(cur_end)
                                                                                                cur_word, cur_start, cur_end = "", None, None
                                            else:
                                                                    if cur_start is None:
                                                                                                cur_start = cs
                                                                                            cur_word += ch
                                                                    cur_end = ce
                                                            if cur_word:
                                            words.append(cur_word)
                                            starts.append(cur_start)
                                            ends.append(cur_end)

                        for word, ws, we in zip(words, starts, ends):
                                            wdur = max(float(we) - float(ws), 0.1)
                                            tc = (
                                                TextClip(
                                                    word,
                                                    fontsize=90,
                                                    font="DejaVu-Sans-Bold",
                                                    color="white",
                                                    stroke_color="black",
                                                    stroke_width=4,
                                                    method="caption",
                                                    size=(W - 80, None),
                                                )
                                                .set_start(float(ws))
                                                .set_duration(wdur)
                                                .set_position(("center", H * 0.72))
                                            )
                                            word_clips.append(tc)

                    scene_clip = (
                                    CompositeVideoClip([bg] + word_clips, size=(W, H))
                                    .set_audio(audio_clip)
                                    .set_duration(duration)
                    )
        clips.append(scene_clip)

    final = concatenate_videoclips(clips, method="compose")
    out_path = tempfile.mktemp(suffix=".mp4")
    final.write_videofile(
                out_path,
                fps=30,
                codec="libx264",
                audio_codec="aac",
                threads=2,
                logger=None,
    )
    return out_path


# ── Streamlit UI ──────────────────────────────────────────────────────────────
st.set_page_config(
        page_title="Daily Video Generator", page_icon="🎬", layout="centered"
)
st.title("🎬 Daily Animated Video Generator")
st.caption("Topic → Script → Voiceover → B-roll → 9:16 Short")

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
                st.write(f"  -> {len(scenes)} scenes generated")

        audio_paths, alignments = [], []
        for scene in scenes:
                        st.write(f"Scene {scene['scene']}: synthesising voiceover...")
                        audio_bytes, alignment = synthesize_speech(
                            scene["narration"], voice_id, elevenlabs_key
                        )
                        tmp_audio = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                        tmp_audio.write(audio_bytes)
                        tmp_audio.close()
                        audio_paths.append(tmp_audio.name)
                        alignments.append(alignment)

            st.write(
                                f"Scene {scene['scene']}: fetching b-roll for '{scene['b_roll_query']}'..."
            )
            broll_path = fetch_pexels_video(scene["b_roll_query"], pexels_key)
            scene["_broll_path"] = broll_path

        st.write("Assembling video with moviepy...")
        video_path = build_video(scenes, audio_paths, alignments)

        status.update(label="Done!", state="complete")

    with st.expander("Script", expanded=False):
                for scene in scenes:
                                st.markdown(f"**Scene {scene['scene']}** — *{scene['b_roll_query']}*")
                                st.write(scene["narration"])

            with open(video_path, "rb") as f:
                        st.download_button(
                                        "Download Video",
                                        f,
                                        file_name="daily_video.mp4",
                                        mime="video/mp4",
                        )

    for p in audio_paths:
                try:
                                os.unlink(p)
except Exception:
            pass
