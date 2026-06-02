from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import requests
import os
import io
import time
import base64
import urllib.parse
import tempfile
import speech_recognition as sr
from PIL import Image
from dotenv import load_dotenv
from gradio_client import Client, handle_file
import json
from concurrent.futures import ThreadPoolExecutor

# Load .env from parent directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

HF_TOKEN = os.getenv("HF_TOKEN", "")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")

app = FastAPI(title="AI Creative Studio API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────
STYLE_PRESETS = {
    "none": "",
    "photorealistic": (
        ", ultra photorealistic, 8K UHD resolution, highly detailed, sharp focus, "
        "professional DSLR photography, cinematic lighting, HDR, masterpiece, "
        "best quality, intricate details, vivid colors, perfect composition, award winning photography"
    ),
    "anime": (
        ", digital illustration, anime style, highly detailed, vivid colors, "
        "concept art, sharp focus, masterfully illustrated, 4k resolution, smooth shading"
    ),
    "cyberpunk": (
        ", cyberpunk style, futuristic city, neon lights, glowing accents, cinematic lighting, "
        "cybernetic details, hyper-detailed, raytracing, sharp focus, 8k resolution"
    ),
    "3d": (
        ", highly detailed 3d render, unreal engine 5 render, ray traced reflections, "
        "octane render style, cinematic lighting, sharp focus, photorealistic textures, volumetric lighting"
    ),
}

ASPECT_RATIOS = {
    "1:1":  (1024, 1024),
    "16:9": (1024, 576),
    "9:16": (576,  1024),
    "4:3":  (1024, 768),
    "3:4":  (768,  1024),
}

PROMPT_TEMPLATES = {
    "🏙️ Architecture & Cities": [
        "A futuristic cyberpunk metropolis with towering neon-lit skyscrapers, flying vehicles, and rain-slicked streets reflecting vibrant holographic advertisements, evening sky, 8k resolution, cinematic lighting.",
        "An ancient Gothic cathedral hidden inside a giant underground cavern, illuminated by sunbeams filtering through a hole in the ceiling, detailed stone carvings, ethereal atmosphere, highly detailed.",
        "A cozy cottage in a Scandinavian pine forest, wooden architecture, smoking chimney, warm interior light, winter snow landscape, golden hour glow, cinematic photography.",
        "A floating island city with Victorian-era steampunk architecture, windmills, airships docked at wooden piers, waterfalls falling into the sky, clouds passing below, highly detailed, fantasy art.",
        "A minimalist modernist concrete mansion built on the edge of a rugged ocean cliff, infinity pool reflecting the starry night sky, warm interior lighting, architectural digest style, sharp focus.",
        "A bustling ancient Roman market square, columns and marble arches, merchants selling colorful silks and spices, sun-drenched day, historical illustration, ultra detailed.",
        "A treehouse city built high up in ancient redwood trees, suspension bridges connecting tree platforms, glowing lanterns at dusk, magical, intricate details, fantasy illustration.",
        "A futuristic solarpunk city where buildings are covered in lush vertical gardens and solar panels, clean white curves, flowing water channels, people walking in parks, bright sunny day.",
    ],
    "🌿 Nature & Landscapes": [
        "A breathtaking majestic waterfall cascading into a crystal clear turquoise lagoon, surrounded by lush tropical jungle flora, colorful birds, cinematic lighting, photorealistic 8K.",
        "An enchanted misty forest at sunrise, sunbeams piercing through the ancient oak trees, glowing mushrooms on the forest floor, magical, ethereal, fantasy landscape.",
        "A vast purple lavender field stretching towards the horizon under a spectacular pink and orange sunset sky, a rustic stone farmhouse in the distance, highly detailed, oil painting style.",
        "A dramatic stormy ocean scene, massive waves crashing against dark volcanic rocks, dark moody storm clouds, lightning flash in the distance, high dynamic range, cinematic photography.",
        "An oasis in a desert at night, palm trees reflecting on a calm water pool, massive glowing Milky Way galaxy filling the clear night sky, dunes in background, 8k resolution.",
        "A tranquil Japanese Zen garden in autumn, colorful red maple leaves floating on a pond, stone bridges, raked gravel patterns, wooden tea house, morning mist, peaceful scenery.",
        "A glowing bioluminescent cave with underground rivers, neon blue and green light reflecting on rock formations, stalactites, magical, fantasy art, octane render.",
        "A breathtaking alpine mountain range with snow-capped peaks reflecting in a mirror-like glacial lake, wildflowers in the foreground, bright sunny day, perfect composition.",
    ],
    "🧑‍🚀 Characters & Portraits": [
        "A detailed portrait of a rugged space explorer in an astronaut suit, helmet visor reflecting a distant colorful nebula, dramatic lighting, highly detailed, digital painting.",
        "A beautiful woodland elf warrior, detailed silver armor, green cloak, holding a glowing magical bow, sharp focus, fantasy digital art, cinematic lighting.",
        "An elderly wizard with a long white beard, wearing star-patterned velvet robes, reading an ancient glowing spellbook in a library filled with books, candlelight, detailed illustration.",
        "A high-fashion portrait of a cyberpunk woman, neon cybernetic face implants, glowing hair, futuristic visor, dark background, leather jacket, dramatic side-lighting.",
        "A cheerful young female scientist in a high-tech lab, holding a glowing holographic atom model, futuristic gadgets in background, bright warm lighting, clean render.",
        "An ancient warrior chief with traditional face paint, looking determinedly into the distance, wearing intricate leather and fur armor, realistic details, cinematic portrait.",
        "A whimsical cartoon character, a friendly tiny robot with expressive glowing eyes, holding a small flower, pixar style, warm lighting, 3D render.",
        "A mysterious rogue in a dark hood, eyes glowing faintly in the shadows, holding a pair of ornate daggers, mist-covered medieval street background, moody fantasy illustration.",
    ],
    "🐉 Fantasy & Mythology": [
        "A colossal golden dragon perched on top of a mountain of gold coins and sparkling gems inside a massive cave, breathing a small puff of flame, fantasy art, highly detailed.",
        "The lost city of Atlantis under the deep ocean, massive domes, coral-covered columns, mermaids swimming around, glowing sea creatures, magical atmosphere.",
        "A majestic phoenix rising from glowing ashes and fire, wings made of flames and starlight, dark dramatic background, epic composition, fantasy digital painting.",
        "A hidden portal in an ancient stone wall, swirling blue vortex of magical energy, glowing runes carved in the stone, enchanted forest background, fantasy concept art.",
        "A celestial castle floating in space, built out of crystal and starlight, nebulas and galaxies passing by in the cosmic background, epic scale, fantasy art.",
        "An ancient stone circle at midnight under a blood moon, glowing magical runes on the stones, druids in cloaks gathering, mystical atmosphere.",
        "A majestic unicorn standing in a clearing of a bioluminescent forest, glowing horn casting a soft light, fireflies, magical, dreamlike fantasy illustration.",
        "A giant sea kraken wrapping its massive tentacles around a medieval wooden pirate ship, stormy ocean, dramatic lightning, epic fantasy battles.",
    ],
    "🚀 Sci-Fi & Futurism": [
        "A futuristic spaceship engine room, glowing fusion reactor core, pipes and high-tech panels, engineer in protective gear, sci-fi concept art, volumetric lighting.",
        "An astronaut standing on the surface of Mars, looking at a massive colony dome in the distance, Earth visible as a small blue dot in the black sky, realistic space art.",
        "A cybernetic white futuristic city on water, sleek curved buildings, flying drones, speedboats, sunny day, clean modern sci-fi style, highly detailed.",
        "A futuristic hover-car race through a canyon on a desert planet, dust trails, sleek aerodynamic vehicles, spectator drones, dynamic action shot, 8k resolution.",
        "A humanoid robot playing a grand piano on a stage in an empty theater, single spotlight highlighting the metallic reflections, dramatic contrast, beautiful art.",
        "A massive space station orbiting a ringed gas giant planet, solar panels reflecting sunlight, small scout ships entering the hangar bay, epic sci-fi illustration.",
        "A virtual reality database matrix, glowing lines of green code, abstract digital landscape, futuristic neon structures, cyberpunk network visualization.",
        "An underwater sci-fi research lab, glass walls showing giant whales and sharks swimming outside, high-tech control panels inside, cool blue lighting.",
    ],
    "🎨 Art Styles": [
        "A quiet Parisian street cafe in the style of Vincent van Gogh's Starry Night, thick swirling brushstrokes, vibrant cobalt blues and warm yellows, impressionist oil painting.",
        "A surreal melting clock landscape in the style of Salvador Dali, barren desert, weird distorted figures, dreamlike surrealism art style.",
        "A majestic cherry blossom mountain landscape in the style of traditional Japanese Ukiyo-e woodblock print, bold ink outlines, flat color washes.",
        "A portrait of a woman in the style of Gustav Klimt's Art Nouveau, gold leaf patterns, intricate decorative mosaic details, rich textures.",
        "A modern abstract geometric painting in the style of Piet Mondrian, primary colors (red, blue, yellow) with thick black grid lines on white canvas.",
        "A futuristic warrior in the style of classic cyber-punk retro 80s synthwave, neon magenta and cyan grid, sunset grid lines, VHS scanlines.",
        "A majestic castle on a hill in watercolor style, soft pastel color washes, ink splatters, dreamlike artistic illustration.",
        "A busy city street scene in the style of pop art, Ben-Day dots, comic book style, bold black outlines, speech bubbles, vibrant flat colors.",
    ],
}

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def _pil_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _generate_pollinations(prompt, width, height, seed, style_suffix="", negative_prompt=""):
    final = prompt + style_suffix
    if negative_prompt:
        final += f", [negative: {negative_prompt}]"
    url = (
        f"https://image.pollinations.ai/prompt/{urllib.parse.quote(final)}"
        f"?width={width}&height={height}&seed={seed}&nologo=true&model=flux"
    )
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200 and len(r.content) > 1000:
                return Image.open(io.BytesIO(r.content))
        except Exception:
            pass
        if attempt < 2:
            time.sleep(2.0)
    return None



def _generate_hf(prompt, width, height, seed, style_suffix="", negative_prompt=""):
    if not HF_TOKEN:
        raise HTTPException(400, "HF_TOKEN not set in .env")
    final = prompt + style_suffix
    if negative_prompt:
        final += f", [negative: {negative_prompt}]"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": final, "parameters": {"width": width, "height": height, "seed": seed}}
    try:
        r = requests.post(
            "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell",
            headers=headers, json=payload, timeout=60,
        )
        if r.status_code == 200:
            return Image.open(io.BytesIO(r.content))
        raise HTTPException(r.status_code, r.text[:200])
    except requests.exceptions.ConnectionError:
        raise HTTPException(503, "Cannot reach Hugging Face — check network/VPN")


# ─────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────
class ImageRequest(BaseModel):
    prompt: str
    negative_prompt: str = ""
    style: str = "none"
    aspect_ratio: str = "1:1"
    batch_count: int = Field(1, ge=1, le=4)
    seed: int = 0
    provider: str = "pollinations"  # "pollinations" | "huggingface"


class TTSRequest(BaseModel):
    text: str
    mode: str = "google"          # "google" | "pollinations"
    language: str = "en"
    voice: str = "nova"
    api_key: str = ""


class TextRequest(BaseModel):
    prompt: str
    genre: str = "general"
    tone: str = "cinematic"
    word_count: int = 150




# ─────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "AI Creative Studio API is running", "docs": "/docs"}


@app.post("/api/generate-image")
async def generate_image(req: ImageRequest):
    style_suffix = STYLE_PRESETS.get(req.style, "")
    width, height = ASPECT_RATIOS.get(req.aspect_ratio, (1024, 1024))
    base_seed = req.seed if req.seed > 0 else int(time.time() * 1000) % 1_000_000

    results = []
    for i in range(req.batch_count):
        current_seed = base_seed + i
        try:
            if req.provider == "pollinations":
                img = _generate_pollinations(req.prompt, width, height, current_seed, style_suffix, req.negative_prompt)
            else:
                img = _generate_hf(req.prompt, width, height, current_seed, style_suffix, req.negative_prompt)

            if img:
                results.append({"image": _pil_to_b64(img), "seed": current_seed})
            else:
                results.append({"error": "Generation returned no image", "seed": current_seed})
        except HTTPException as e:
            results.append({"error": e.detail, "seed": current_seed})

        if i < req.batch_count - 1:
            time.sleep(1.0)

    return {"images": results}


@app.get("/api/enhance-prompt")
async def enhance_prompt(prompt: str = Query(..., min_length=1)):
    system = (
        "You are a professional stable diffusion prompt engineer. "
        "Expand the user prompt to be descriptive, detailed, beautiful, "
        "adding style, lighting, and camera details. "
        "Return ONLY the enhanced prompt. Keep it under 60 words."
    )
    try:
        url = (
            f"https://text.pollinations.ai/{urllib.parse.quote(prompt)}"
            f"?system={urllib.parse.quote(system)}"
        )
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            return {"enhanced": r.text.strip()}
    except Exception:
        pass
    return {"enhanced": prompt}


@app.post("/api/generate-text")
async def generate_text(req: TextRequest):
    system = (
        f"You are a professional creative scriptwriter and story assistant. "
        f"Generate a creative piece in the '{req.genre}' genre with a '{req.tone}' tone. "
        f"Keep the total word count strictly under {req.word_count} words. "
        f"Do not write introductory or concluding meta remarks, output only the story content."
    )
    try:
        url = (
            f"https://text.pollinations.ai/{urllib.parse.quote(req.prompt)}"
            f"?system={urllib.parse.quote(system)}"
        )
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            return {"text": r.text.strip()}
        raise HTTPException(r.status_code, r.text[:200])
    except requests.exceptions.ConnectionError:
        raise HTTPException(503, "Cannot reach Pollinations Text service")
    except Exception as e:
        raise HTTPException(500, f"Error generating text: {e}")



@app.post("/api/caption-image")
async def caption_image(file: UploadFile = File(...)):
    """
    Caption an image using the hysts/image-captioning-with-blip Space on HF:
    This space runs Salesforce BLIP which is fast, free, keyless, and not blocked on Jio.
    """
    image_bytes = await file.read()
    tmp_path = None
    try:
        suffix = os.path.splitext(file.filename or "image.jpg")[1]
        if not suffix:
            suffix = ".jpg"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        
        client = Client("hysts/image-captioning-with-blip")
        result = client.predict(
            image=handle_file(tmp_path),
            api_name="/caption"
        )
        if result:
            return {"caption": str(result).strip(), "source": "BLIP Vision"}
        raise Exception("Gradio client returned empty caption")
    except Exception as e:
        raise HTTPException(503, f"Vision captioning is temporarily unavailable: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass




@app.post("/api/tts")
async def tts(req: TTSRequest):
    if req.mode == "google":
        # Optional translation
        translated = req.text
        if req.language != "en":
            try:
                tr_url = (
                    f"https://translate.googleapis.com/translate_a/single"
                    f"?client=gtx&sl=auto&tl={req.language}&dt=t&q={urllib.parse.quote(req.text)}"
                )
                r = requests.get(tr_url, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    translated = "".join(s[0] for s in data[0] if s[0])
            except Exception:
                pass

        tts_url = (
            f"https://translate.google.com/translate_tts"
            f"?ie=UTF-8&q={urllib.parse.quote(translated)}&tl={req.language}&client=tw-ob"
        )
        try:
            r = requests.get(tts_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            if r.status_code == 200:
                return {
                    "audio": base64.b64encode(r.content).decode(),
                    "translated_text": translated,
                }
            raise HTTPException(r.status_code, "Google TTS failed")
        except requests.exceptions.ConnectionError:
            raise HTTPException(503, "Cannot reach Google TTS")

    elif req.mode == "pollinations":
        if not req.api_key:
            raise HTTPException(400, "Pollinations API key is required")
        try:
            url = f"https://gen.pollinations.ai/audio/{urllib.parse.quote(req.text)}?key={req.api_key}&voice={req.voice}"
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                return {"audio": base64.b64encode(r.content).decode(), "translated_text": req.text}
            raise HTTPException(r.status_code, r.text[:200])
        except requests.exceptions.ConnectionError:
            raise HTTPException(503, "Cannot reach Pollinations Audio")

    raise HTTPException(400, "Invalid mode — use 'google' or 'pollinations'")


@app.post("/api/transcribe")
async def transcribe(file: UploadFile = File(...)):
    recognizer = sr.Recognizer()
    audio_bytes = await file.read()
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        with sr.AudioFile(tmp_path) as source:
            audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data)
        return {"transcription": text}
    except sr.UnknownValueError:
        raise HTTPException(422, "Could not understand audio — ensure the recording is clear")
    except sr.RequestError as e:
        raise HTTPException(503, f"Speech Recognition service error: {e}")
    except Exception as e:
        raise HTTPException(500, f"Error processing audio: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/api/talking-avatar")
async def talking_avatar(
    image: UploadFile = File(...),
    audio: UploadFile = File(...),
    preprocess: str = Query("crop"),
    still_mode: bool = Query(True),
    use_enhancer: bool = Query(False),
    custom_endpoint: str = Query("")
):
    image_bytes = await image.read()
    audio_bytes = await audio.read()

    img_tmp_path = None
    aud_tmp_path = None

    try:
        # Save source image to temp file
        img_suffix = os.path.splitext(image.filename or "image.jpg")[1] or ".jpg"
        with tempfile.NamedTemporaryFile(suffix=img_suffix, delete=False) as img_tmp:
            img_tmp.write(image_bytes)
            img_tmp_path = img_tmp.name

        # Save driving audio to temp file
        aud_suffix = os.path.splitext(audio.filename or "audio.wav")[1] or ".wav"
        with tempfile.NamedTemporaryFile(suffix=aud_suffix, delete=False) as aud_tmp:
            aud_tmp.write(audio_bytes)
            aud_tmp_path = aud_tmp.name

        # Select target client
        endpoint = custom_endpoint.strip() if custom_endpoint.strip() else "John6666/SadTalker"
        client = Client(endpoint)

        # Call the SadTalker space
        result = client.predict(
            source_image=handle_file(img_tmp_path),
            driven_audio=handle_file(aud_tmp_path),
            preprocess=preprocess,
            still_mode=still_mode,
            use_enhancer=use_enhancer,
            batch_size=1,
            size="256",
            pose_style=0,
            facerender="facevid2vid",
            exp_scale=1.0,
            use_ref_video=False,
            ref_video=None,
            ref_info="pose",
            use_idle_mode=False,
            length_of_audio=5.0,
            use_blink=True,
            api_name="/test"
        )

        video_path = None
        if isinstance(result, dict) and "video" in result:
            video_path = result["video"]
        elif isinstance(result, (list, tuple)) and len(result) > 0:
            video_path = result[0]
        else:
            video_path = str(result)

        if not video_path or not os.path.exists(video_path):
            raise Exception("SadTalker engine failed to return a valid video path.")

        with open(video_path, "rb") as video_file:
            video_b64 = base64.b64encode(video_file.read()).decode()

        return {"video": video_b64}

    except Exception as e:
        raise HTTPException(500, f"Error generating talking avatar: {e}")

    finally:
        for p in [img_tmp_path, aud_tmp_path]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass



@app.get("/api/prompt-templates")
async def get_prompt_templates():
    return PROMPT_TEMPLATES


@app.get("/api/style-presets")
async def get_style_presets():
    return list(STYLE_PRESETS.keys())


@app.get("/api/aspect-ratios")
async def get_aspect_ratios():
    return list(ASPECT_RATIOS.keys())




