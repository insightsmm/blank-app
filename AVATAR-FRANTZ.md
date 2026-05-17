# Avatar: Frantz

## Appearance
- Age: Early Middle Age
- Gender: Man
- Ethnicity: Black
- Hair: Closely cropped / shaved under hat
- Build: Athletic, medium frame
- Features: Rectangular metal-frame glasses with tinted lenses, mustache, bright warm smile, gold chain necklace, stylish and confident energy
- Style: Realistic
- Reference: photos provided by user (portrait selfie + podcast studio shot, same geometric black-and-gold background)

## Voice
- Tone: Warm, confident, magnetic
- Accent: Haitian / Caribbean
- Energy: Expressive and engaging — animated delivery with natural charisma
- Think: A storyteller who commands the room without raising his voice
- Cloning: Voice cloning from user-provided samples
  - `/root/.claude/uploads/bd92df68-ce07-45af-bcc8-95e8052b86c2/4f41643d-i_grew_up_in_haiti_animated1.MP3`
  - `/root/.claude/uploads/bd92df68-ce07-45af-bcc8-95e8052b86c2/57137f6b-grew_up_in_haiti.mp3`

## HeyGen
- Group ID: (pending — create via photo upload)
- Voice ID: (pending — create via voice cloning from samples above)
- Voice Name: Frantz
- Voice Designed: false
- Voice Seed: N/A
- Looks: (pending creation)
- Last Synced: (pending)

⚠️ look_ids are ephemeral — always resolve fresh from group_id at runtime via `heygen avatar looks list --group-id <id>` (or MCP `list_avatar_looks`). Never hardcode look_id as the primary avatar reference.

## Creation Notes
- Type B (photo-based) creation — use the portrait selfie (first photo) as the reference image
- Voice cloning from the two MP3 samples above
- CLI commands (once transport is available):
  1. Upload photo: `heygen asset create --file <photo_path>`
  2. Clone voice: `heygen voice clone --name "Frantz" --file <mp3_path>`
  3. Create avatar: `heygen avatar create -d '{"type":"photo","name":"Frantz","file":{"type":"asset_id","asset_id":"<id>"}}'`
  4. Update this file with Group ID, Voice ID, and Look IDs
