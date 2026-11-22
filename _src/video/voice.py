"""Озвучка видеоинструкции голосом из библиотеки ElevenLabs (по имени, по умолчанию «Фил»/Phil).
Сохраняет _src/video/voice.mp3 и alignment.json (тайминги букв для субтитров)."""
import base64, json, os, sys, urllib.request
KEY = os.environ.get("ELEVENLABS_API_KEY", "").strip()
NAME = os.environ.get("VOICE_NAME", "fil,фил,phil")
D = os.path.dirname(os.path.abspath(__file__))
if not KEY:
    print("Нет секрета ELEVENLABS_API_KEY"); sys.exit(0)
def req(url, data=None):
    r = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
                               headers={"xi-api-key": KEY, "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=180))
voices = req("https://api.elevenlabs.io/v1/voices").get("voices", [])
names = [n.strip().lower() for n in NAME.split(",")]
pick = next((v for v in voices if any(v["name"].lower().startswith(n) or n in v["name"].lower().split() for n in names)), None)
if not pick:
    print("Голос не найден. Есть:", ", ".join(v["name"] for v in voices)); sys.exit(1)
print("Голос:", pick["name"])
SFX = os.environ.get("SUFFIX", "")
text = open(os.path.join(D, f"script{SFX}.txt"), encoding="utf-8").read().strip()
r = req(f"https://api.elevenlabs.io/v1/text-to-speech/{pick['voice_id']}/with-timestamps?output_format=mp3_44100_128",
        {"text": text, "model_id": "eleven_multilingual_v2",
         "voice_settings": {"stability": 0.6, "similarity_boost": 0.8, "style": 0.1, "use_speaker_boost": True}})
open(os.path.join(D, f"voice{SFX}.mp3"), "wb").write(base64.b64decode(r["audio_base64"]))
json.dump({"voice": pick["name"], "alignment": r.get("alignment")}, open(os.path.join(D, f"alignment{SFX}.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("Готово:", len(r["audio_base64"]) * 3 // 4, "байт")
