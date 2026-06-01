import requests
import os
import streamlit as st
from PIL import Image
import io
import urllib.parse
import time
import base64
import tempfile
import speech_recognition as sr
import zipfile


# Load tokens from .env if it exists
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if "=" in line:
                key, val = line.strip().split("=", 1)
                os.environ[key] = val.strip()

HF_TOKEN = os.getenv("HF_TOKEN", "")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")

# ----------------------------------------------------
# QUALITY ENHANCER DICTIONARY & ASPECT RATIOS
# ----------------------------------------------------
STYLE_PRESETS = {
    "None": "",
    "Ultra-Photorealistic (Recommended) ✨": (
        ", ultra photorealistic, 8K UHD resolution, highly detailed, sharp focus, "
        "professional DSLR photography, cinematic lighting, HDR, masterpiece, "
        "best quality, intricate details, vivid colors, perfect composition, award winning photography"
    ),
    "Digital Art & Anime 🎨": (
        ", digital illustration, anime style, highly detailed, vivid colors, "
        "concept art, sharp focus, masterfully illustrated, 4k resolution, smooth shading"
    ),
    "Cyberpunk & Sci-Fi 🌆": (
        ", cyberpunk style, futuristic city, neon lights, glowing accents, cinematic lighting, "
        "cybernetic details, hyper-detailed, raytracing, sharp focus, 8k resolution"
    ),
    "3D Render & Unreal Engine 5 👾": (
        ", highly detailed 3d render, unreal engine 5 render, ray traced reflections, "
        "octane render style, cinematic lighting, sharp focus, photorealistic textures, volumetric lighting"
    )
}

ASPECT_RATIOS = {
    "1:1 Square (1024x1024)": (1024, 1024),
    "16:9 Widescreen (1024x576)": (1024, 576),
    "9:16 Portrait (576x1024)": (576, 1024),
    "4:3 Standard (1024x768)": (1024, 768),
    "3:4 Tall (768x1024)": (768, 1024)
}

# ----------------------------------------------------
# IMAGE GENERATION FUNCTIONS
# ----------------------------------------------------
def generate_image_huggingface(prompt, width, height, seed, style_suffix="", negative_prompt=""):
    if not HF_TOKEN or HF_TOKEN == "hf_your_token_here":
        st.error("🔑 Hugging Face token is missing! Please add it to your `.env` file.")
        return None
        
    final_prompt = prompt + style_suffix
    if negative_prompt:
        final_prompt += f", [negative: {negative_prompt}]"
        
    API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    payload = {
        "inputs": final_prompt,
        "parameters": {
            "width": width,
            "height": height,
            "seed": seed
        }
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            st.error(f"API Error ({response.status_code}): {response.text}")
            return None
        return Image.open(io.BytesIO(response.content))
    except requests.exceptions.ConnectionError:
        st.error("🌐 Connection Error: Could not connect to Hugging Face. Jio network might be blocking it. Try using the Pollinations AI option instead!")
        return None
    except Exception as e:
        st.error(f"⚠️ Hugging Face Error: {e}")
        return None

def generate_image_pollinations(prompt, width, height, seed, style_suffix="", negative_prompt=""):
    try:
        final_prompt = prompt + style_suffix
        if negative_prompt:
            final_prompt += f", [negative: {negative_prompt}]"
            
        encoded_prompt = urllib.parse.quote(final_prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed}&nologo=true&model=flux"
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            return None
        return Image.open(io.BytesIO(response.content))
    except Exception:
        return None

def generate_batch(provider, prompt, count, width, height, seed, style_suffix, negative_prompt):
    base_seed = seed if seed > 0 else int(time.time() * 1000) % 1000000

    images = []
    for index in range(count):
        current_seed = base_seed + index
        if "Pollinations" in provider:
            img = generate_image_pollinations(
                prompt=prompt,
                width=width,
                height=height,
                seed=current_seed,
                style_suffix=style_suffix,
                negative_prompt=negative_prompt
            )
        else:
            img = generate_image_huggingface(
                prompt=prompt,
                width=width,
                height=height,
                seed=current_seed,
                style_suffix=style_suffix,
                negative_prompt=negative_prompt
            )
        if img:
            images.append((img, current_seed))
        # Small delay between requests to avoid Pollinations rate-limiting
        if index < count - 1:
            time.sleep(1.0)
    return images


def enhance_prompt(prompt):
    try:
        system_prompt = "You are a professional stable diffusion prompt engineer. Expand the user prompt to be descriptive, detailed, beautiful, adding style, lighting, and camera details. Return ONLY the enhanced prompt. Keep it under 60 words."
        encoded_prompt = urllib.parse.quote(prompt)
        encoded_system = urllib.parse.quote(system_prompt)
        url = f"https://text.pollinations.ai/{encoded_prompt}?system={encoded_system}"
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            return response.text.strip()
        return prompt
    except Exception:
        return prompt

def caption_image(image_bytes):
    if not HF_TOKEN or HF_TOKEN == "hf_your_token_here" or not HF_TOKEN.strip():
        return "🔑 Hugging Face token is missing! Please add it to your `.env` file to use Captioning."
    
    API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    try:
        response = requests.post(API_URL, headers=headers, data=image_bytes, timeout=30)
        if response.status_code == 200:
            res = response.json()
            if isinstance(res, list) and len(res) > 0 and "generated_text" in res[0]:
                return res[0]["generated_text"]
            return "Error: Could not parse response."
        elif response.status_code == 503:
            return "⏳ Model is loading on Hugging Face. Please try again in a few seconds."
        else:
            return f"API Error ({response.status_code}): {response.text}"
    except requests.exceptions.ConnectionError:
        return "🌐 Connection Error: Could not connect to Hugging Face. Jio network might be blocking it. Please use a VPN or Cloudflare WARP."
    except Exception as e:
        return f"⚠️ Error: {e}"

# ----------------------------------------------------
# TRANSLATION & AUDIO FUNCTIONS
# ----------------------------------------------------
def translate_text(text, target_lang):
    if target_lang == "en":
        return text
    try:
        encoded_text = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={encoded_text}"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            translated = "".join([s[0] for s in data[0] if s[0]])
            return translated
        return text
    except Exception:
        return text

def generate_audio_google(text, lang="en"):
    try:
        encoded_text = urllib.parse.quote(text)
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded_text}&tl={lang}&client=tw-ob"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            st.error(f"Error ({response.status_code}) generating audio from Google TTS.")
            return None
        return response.content
    except Exception as e:
        st.error(f"⚠️ Google TTS Error: {e}")
        return None

def generate_audio_pollinations(text, api_key, voice="nova"):
    try:
        encoded_text = urllib.parse.quote(text)
        url = f"https://gen.pollinations.ai/audio/{encoded_text}?key={api_key}&voice={voice}"
        response = requests.get(url, timeout=30)
        if response.status_code == 401:
            st.error("🔑 Invalid Pollinations API Key! Please check your key in the sidebar.")
            return None
        elif response.status_code != 200:
            st.error(f"API Error ({response.status_code}): {response.text}")
            return None
        return response.content
    except Exception as e:
        st.error(f"⚠️ Pollinations Audio Error: {e}")
        return None

def transcribe_audio_file(uploaded_file):
    r = sr.Recognizer()
    try:
        # Create a temp file path inside workspace
        temp_dir = os.path.join("C:/Users/asach/.gemini/antigravity", "scratch")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, "temp_transcription.wav")
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getvalue())
            
        with sr.AudioFile(temp_path) as source:
            audio_data = r.record(source)
            
        # Clean up immediately
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        text = r.recognize_google(audio_data)
        return text
    except sr.UnknownValueError:
        return "❌ Speech Recognition could not understand the audio. Please make sure the recording is clear."
    except sr.RequestError as e:
        return f"❌ Service error from Google Speech Recognition: {e}"
    except Exception as e:
        return f"❌ Error reading/processing the audio: {e}"

# ----------------------------------------------------
# STREAMLIT UI CONFIGURATION
# ----------------------------------------------------
st.set_page_config(page_title="AI Creative Studio", page_icon="🎨", layout="centered")

# Initialize Session State
if "gallery" not in st.session_state:
    st.session_state["gallery"] = []
if "img_prompt_input" not in st.session_state:
    st.session_state["img_prompt_input"] = ""
if "vision_caption" not in st.session_state:
    st.session_state["vision_caption"] = ""


# Prompt templates categorized library (50+ prompts)
PROMPT_TEMPLATES = {
    "🏙️ Architecture & Cities": [
        "A futuristic cyberpunk metropolis with towering neon-lit skyscrapers, flying vehicles, and rain-slicked streets reflecting vibrant holographic advertisements, evening sky, 8k resolution, cinematic lighting.",
        "An ancient Gothic cathedral hidden inside a giant underground cavern, illuminated by sunbeams filtering through a hole in the ceiling, detailed stone carvings, ethereal atmosphere, highly detailed.",
        "A cozy cottage in a Scandinavian pine forest, wooden architecture, smoking chimney, warm interior light, winter snow landscape, golden hour glow, cinematic photography.",
        "A floating island city with Victorian-era steampunk architecture, windmills, airships docked at wooden piers, waterfalls falling into the sky, clouds passing below, highly detailed, fantasy art.",
        "A minimalist modernist concrete mansion built on the edge of a rugged ocean cliff, infinity pool reflecting the starry night sky, warm interior lighting, architectural digest style, sharp focus.",
        "A bustling ancient Roman market square, columns and marble arches, merchants selling colorful silks and spices, sun-drenched day, historical illustration, ultra detailed.",
        "A treehouse city built high up in ancient redwood trees, suspension bridges connecting tree platforms, glowing lanterns at dusk, magical, intricate details, fantasy illustration.",
        "A futuristic solarpunk city where buildings are covered in lush vertical gardens and solar panels, clean white curves, flowing water channels, people walking in parks, bright sunny day, optimistic future."
    ],
    "🌿 Nature & Landscapes": [
        "A breathtaking majestic waterfall cascading into a crystal clear turquoise lagoon, surrounded by lush tropical jungle flora, colorful birds, cinematic lighting, photorealistic 8K.",
        "An enchanted misty forest at sunrise, sunbeams piercing through the ancient oak trees, glowing mushrooms on the forest floor, magical, ethereal, fantasy landscape.",
        "A vast purple lavender field stretching towards the horizon under a spectacular pink and orange sunset sky, a rustic stone farmhouse in the distance, highly detailed, oil painting style.",
        "A dramatic stormy ocean scene, massive waves crashing against dark volcanic rocks, dark moody storm clouds, lightning flash in the distance, high dynamic range, cinematic photography.",
        "An oasis in a desert at night, palm trees reflecting on a calm water pool, massive glowing Milky Way galaxy filling the clear night sky, dunes in background, 8k resolution.",
        "A tranquil Japanese Zen garden in autumn, colorful red maple leaves floating on a pond, stone bridges, raked gravel patterns, wooden tea house, morning mist, peaceful scenery.",
        "A glowing bioluminescent cave with underground rivers, neon blue and green light reflecting on rock formations, stalactites, magical, fantasy art, octane render.",
        "A breathtaking alpine mountain range with snow-capped peaks reflecting in a mirror-like glacial lake, wildflowers in the foreground, bright sunny day, perfect composition."
    ],
    "🧑‍🚀 Characters & Portraits": [
        "A detailed portrait of a rugged space explorer in an astronaut suit, helmet visor reflecting a distant colorful nebula, dramatic lighting, highly detailed, digital painting.",
        "A beautiful woodland elf warrior, detailed silver armor, green cloak, holding a glowing magical bow, sharp focus, fantasy digital art, cinematic lighting.",
        "An elderly wizard with a long white beard, wearing star-patterned velvet robes, reading an ancient glowing spellbook in a library filled with books, candlelight, detailed illustration.",
        "A high-fashion portrait of a cyberpunk woman, neon cybernetic face implants, glowing hair, futuristic visor, dark background, leather jacket, dramatic side-lighting.",
        "A cheerful young female scientist in a high-tech lab, holding a glowing holographic atom model, futuristic gadgets in background, bright warm lighting, clean render.",
        "An ancient warrior chief with traditional face paint, looking determinedly into the distance, wearing intricate leather and fur armor, realistic details, cinematic portrait.",
        "A whimsical cartoon character, a friendly tiny robot with expressive glowing eyes, holding a small flower, pixar style, warm lighting, 3D render.",
        "A mysterious rogue in a dark hood, eyes glowing faintly in the shadows, holding a pair of ornate daggers, mist-covered medieval street background, moody fantasy illustration."
    ],
    "🐉 Fantasy & Mythology": [
        "A colossal golden dragon perched on top of a mountain of gold coins and sparkling gems inside a massive cave, breathing a small puff of flame, fantasy art, highly detailed.",
        "The lost city of Atlantis under the deep ocean, massive domes, coral-covered columns, mermaids swimming around, glowing sea creatures, magical atmosphere.",
        "A majestic phoenix rising from glowing ashes and fire, wings made of flames and starlight, dark dramatic background, epic composition, fantasy digital painting.",
        "A hidden portal in an ancient stone wall, swirling blue vortex of magical energy, glowing runes carved in the stone, enchanted forest background, fantasy concept art.",
        "A celestial castle floating in space, built out of crystal and starlight, nebulas and galaxies passing by in the cosmic background, epic scale, fantasy art.",
        "An ancient stone circle (like Stonehenge) at midnight under a blood moon, glowing magical runes on the stones, druids in cloaks gathering, mystical atmosphere.",
        "A majestic unicorn standing in a clearing of a bioluminescent forest, glowing horn casting a soft light, fireflies, magical, dreamlike fantasy illustration.",
        "A giant sea kraken wrapping its massive tentacles around a medieval wooden pirate ship, stormy ocean, dramatic lightning, epic fantasy battles."
    ],
    "🚀 Sci-Fi & Futurism": [
        "A futuristic spaceship engine room, glowing fusion reactor core, pipes and high-tech panels, engineer in protective gear, sci-fi concept art, volumetric lighting.",
        "An astronaut standing on the surface of Mars, looking at a massive colony dome in the distance, Earth visible as a small blue dot in the black sky, realistic space art.",
        "A cybernetic white futuristic city on water, sleek curved buildings, flying drones, speedboats, sunny day, clean modern sci-fi style, highly detailed.",
        "A futuristic hover-car race through a canyon on a desert planet, dust trails, sleek aerodynamic vehicles, spectator drones, dynamic action shot, 8k resolution.",
        "A humanoid robot playing a grand piano on a stage in an empty theater, single spotlight highlighting the metallic reflections, dramatic contrast, beautiful art.",
        "A massive space station orbiting a ringed gas giant planet, solar panels reflecting sunlight, small scout ships entering the hangar bay, epic sci-fi illustration.",
        "A virtual reality database matrix, glowing lines of green code, abstract digital landscape, futuristic neon structures, cyberpunk network visualization.",
        "An underwater sci-fi research lab, glass walls showing giant whales and sharks swimming outside, high-tech control panels inside, cool blue lighting."
    ],
    "🎨 Art Styles": [
        "A quiet Parisian street cafe in the style of Vincent van Gogh's Starry Night, thick swirling brushstrokes, vibrant cobalt blues and warm yellows, impressionist oil painting.",
        "A surreal melting clock landscape in the style of Salvador Dali, barren desert, weird distorted figures, dreamlike surrealism art style.",
        "A majestic cherry blossom mountain landscape in the style of traditional Japanese Ukiyo-e woodblock print, bold ink outlines, flat color washes.",
        "A portrait of a woman in the style of Gustav Klimt's Art Nouveau, gold leaf patterns, intricate decorative mosaic details, rich textures.",
        "A modern abstract geometric painting in the style of Piet Mondrian, primary colors (red, blue, yellow) with thick black grid lines on white canvas.",
        "A futuristic warrior in the style of classic cyber-punk retro 80s synthwave, neon magenta and cyan grid, sunset grid lines, VHS scanlines.",
        "A majestic castle on a hill in watercolor style, soft pastel color washes, ink splatters, dreamlike artistic illustration.",
        "A busy city street scene in the style of pop art, Ben-Day dots, comic book style, bold black outlines, speech bubbles, vibrant flat colors."
    ]
}

st.title("🎬 AI Creative Studio")
st.write("Generate beautiful images and speech using AI. Simple, fast, and interactive!")

# Sidebar for Settings & API Keys
st.sidebar.title("⚙️ API Configuration")
st.sidebar.write("Configure keys for advanced models:")

user_pollinations_key = st.sidebar.text_input(
    "Pollinations API Key:",
    value=POLLINATIONS_API_KEY,
    type="password",
    help="Get a FREE key with trial credits by logging into https://enter.pollinations.ai"
)

st.sidebar.markdown(
    "💡 **No Key/No Coins?** Use the keyless options under Image (Pollinations) and Audio (Google TTS) tabs. They are 100% free!"
)

# Tab Selection: Five Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📸 Text-to-Image",
    "🔊 Text-to-Audio / Speech",
    "🖼️ Image Vision & Captioning",
    "📚 Prompt Library",
    "🗂️ My Session Gallery"
])

# ----------------------------------------------------
# TAB 1: TEXT TO IMAGE
# ----------------------------------------------------
with tab1:
    st.header("Generate Images")
    
    img_provider = st.radio(
        "Select Image Generator Provider:",
        ["Pollinations AI (Free, No Token, Jio Compatible 🚀)", "Hugging Face API (Requires HF Token, FLUX.1-schnell)"]
    )
    
    col_p1, col_p2 = st.columns([5, 1])
    with col_p1:
        img_prompt = st.text_input("Enter Image Prompt:", key="img_prompt_input")
    with col_p2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("✨ Enhance", use_container_width=True, key="btn_enhance_prompt"):
            if img_prompt.strip():
                with st.spinner("Enhancing prompt..."):
                    enhanced_text = enhance_prompt(img_prompt)
                    st.session_state["img_prompt_input"] = enhanced_text
                    st.rerun()
            else:
                st.warning("Please type a prompt first!")
                
    neg_prompt = st.text_input("Negative Prompt (Elements to exclude):", key="neg_prompt_input", placeholder="e.g. blurry, low quality, watermark, text")
    
    # Styling and Grid controls
    col1, col2 = st.columns(2)
    with col1:
        img_preset = st.selectbox(
            "Style Preset:",
            list(STYLE_PRESETS.keys()),
            index=1,
            help="Automatically appends specialized quality tokens for stunning results."
        )
    with col2:
        aspect_ratio_label = st.selectbox(
            "Aspect Ratio:",
            list(ASPECT_RATIOS.keys()),
            index=0
        )
        
    # Grid batch generation and advanced config
    col_batch, col_advanced = st.columns(2)
    with col_batch:
        batch_count = st.slider("Batch Count (Images to generate at once):", min_value=1, max_value=4, value=1)
        
    with col_advanced:
        with st.expander("🛠️ Advanced Settings"):
            custom_seed = st.number_input("Custom Seed (Use 0 for random):", min_value=0, value=0)
            
    if st.button("Generate Image(s)", use_container_width=True):
        if not img_prompt.strip():
            st.warning("Please enter a prompt.")
        else:
            with st.spinner("Generating your image(s)... Please wait..."):
                style_suffix = STYLE_PRESETS[img_preset]
                width, height = ASPECT_RATIOS[aspect_ratio_label]
                
                images = generate_batch(
                    provider=img_provider,
                    prompt=img_prompt,
                    count=batch_count,
                    width=width,
                    height=height,
                    seed=custom_seed,
                    style_suffix=style_suffix,
                    negative_prompt=neg_prompt
                )
                
                if images:
                    st.success(f"Successfully generated {len(images)} image(s)!")
                    
                    cols_count = min(len(images), 2)
                    cols = st.columns(cols_count)
                    
                    for idx, (img, current_seed) in enumerate(images):
                        # Save to Session Gallery
                        st.session_state["gallery"].append({
                            "image": img,
                            "prompt": img_prompt,
                            "seed": current_seed,
                            "timestamp": time.strftime("%I:%M %p")
                        })
                        
                        col_idx = idx % cols_count
                        with cols[col_idx]:
                            st.image(img, caption=f"Image {idx+1} (Seed: {current_seed})", use_container_width=True)
                            
                            # Individual Download
                            buf = io.BytesIO()
                            img.save(buf, format="PNG")
                            st.download_button(
                                label="📥 Download",
                                data=buf.getvalue(),
                                file_name=f"generated_{idx+1}_{current_seed}.png",
                                mime="image/png",
                                key=f"dl_btn_{idx}_{current_seed}"
                            )
                else:
                    st.error("❌ Generation failed. Please check your prompt or network connection.")

# ----------------------------------------------------
# TAB 2: TEXT TO AUDIO / SPEECH
# ----------------------------------------------------
with tab2:
    audio_subtab1, audio_subtab2 = st.tabs(["🎙️ Speech Synthesis & Mixing", "📝 Speech-to-Text Transcription"])
    
    # ----------------------------------------------------
    # SUBTAB 1: SYNTHESIS & MIXING
    # ----------------------------------------------------
    with audio_subtab1:
        st.header("Speech Synthesis & Studio Mixer")
        st.write("Convert written text into speech and overlay procedural background tracks.")
        
        audio_mode = st.radio(
            "Choose Audio Mode:",
            ["Google TTS (100% Free, Keyless, Jio Compatible 🚀)", "Pollinations AI (Requires Pollinations API Key)"],
            key="synthesis_mode_radio"
        )
        
        audio_text = st.text_area(
            "Enter text to speak:",
            value="Hello! Welcome to the AI Creative Studio. Customize the speed, choose a background track, and play or download your mixed audio.",
            height=100,
            key="synthesis_text_area"
        )
        
        # Select Target Language / Voice Preset
        col_voice, col_playback = st.columns(2)
        with col_voice:
            if "Google TTS" in audio_mode:
                lang_option = st.selectbox(
                    "Select Target Language:",
                    [
                        ("English", "en"),
                        ("Tamil (தமிழ்)", "ta"),
                        ("Hindi (हिन्दी)", "hi"),
                        ("Spanish (Español)", "es"),
                        ("French (Français)", "fr"),
                        ("German (Deutsch)", "de")
                    ],
                    index=0,
                    format_func=lambda x: x[0]
                )
                target_lang = lang_option[1]
            else:
                voice_option = st.selectbox(
                    "Select Voice Preset:",
                    ["nova", "alloy", "echo", "fable", "onyx", "shimmer"],
                    index=0
                )
                
        with col_playback:
            playback_speed = st.slider("Playback Speed:", min_value=0.5, max_value=2.0, value=1.0, step=0.1, format="%.1fx")
            
        # Audio loop selection & volume
        col_loop, col_volume = st.columns(2)
        with col_loop:
            bg_loop_name = st.selectbox(
                "Background Soundtrack Preset:",
                ["None (A cappella)", "Calm Zen Pad ✨", "Deep Tech Pulse 🥁", "Cosmic Drone 🚀"],
                index=0
            )
        with col_volume:
            bg_volume = st.slider("Music Loop Volume:", min_value=0, max_value=50, value=15, step=5, format="%d%%")
            
        if st.button("Render Audio Mix", use_container_width=True):
            if not audio_text.strip():
                st.warning("Please enter some text.")
            else:
                with st.spinner("Processing speech audio... Please wait..."):
                    if "Google TTS" in audio_mode:
                        translated_text = translate_text(audio_text, target_lang)
                        if target_lang != "en":
                            st.info(f"📝 **Translated Text ({lang_option[0]}):** {translated_text}")
                        audio_bytes = generate_audio_google(translated_text, lang=target_lang)
                    else:
                        audio_bytes = generate_audio_pollinations(audio_text, user_pollinations_key, voice_option)
                        
                    if audio_bytes:
                        st.success("Speech rendered successfully! Load mixer below:")
                        
                        # Encode speech MP3 bytes to base64
                        b64_speech = base64.b64encode(audio_bytes).decode()
                        
                        # Custom premium HTML5/JS Web Audio API Mixer Player
                        mixer_html = f"""
                        <div style="background: #111827; border-radius: 12px; padding: 20px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #f3f4f6; border: 1px solid #1f2937; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);">
                          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <span style="font-weight: 600; font-size: 14px; color: #10b981; letter-spacing: 0.5px;">🎧 ACTIVE MIXER CONSOLE</span>
                            <span id="player-status" style="font-size: 12px; padding: 3px 8px; border-radius: 9999px; background: #374151; color: #9ca3af;">READY</span>
                          </div>
                          
                          <!-- Visualizer Canvas -->
                          <canvas id="visualizer" style="width: 100%; height: 60px; background: #030712; border-radius: 6px; border: 1px solid #1f2937; margin-bottom: 20px;"></canvas>
                          
                          <!-- Mixer Controls -->
                          <div style="display: flex; gap: 10px;">
                            <button id="btn-play" onclick="playMixed()" style="flex: 1; padding: 12px 20px; border-radius: 8px; background: linear-gradient(135deg, #10b981, #059669); border: none; color: #fff; font-weight: bold; cursor: pointer; transition: transform 0.1s;">▶ PLAY MIX</button>
                            <button id="btn-stop" onclick="stopMixed()" style="padding: 12px 20px; border-radius: 8px; background: #ef4444; border: none; color: #fff; font-weight: bold; cursor: pointer;">⏹ STOP</button>
                            <button id="btn-download" onclick="downloadMixed()" style="padding: 12px 20px; border-radius: 8px; background: #4b5563; border: none; color: #fff; font-weight: bold; cursor: pointer;">📥 EXPORT WAV</button>
                          </div>
                          <a id="download-link" style="display:none"></a>
                        </div>
                        
                        <script>
                          const speechBase64 = "{b64_speech}";
                          const bgLoopType = "{bg_loop_name}";
                          const bgVolPercent = {bg_volume};
                          const playbackRateSpeed = {playback_speed};
                          
                          let audioCtx = null;
                          let activeNodes = [];
                          let animationId = null;
                          let decodedBuffer = null;
                          
                          // Convert base64 to ArrayBuffer
                          function base64ToArrayBuffer(base64) {{
                            const binaryString = window.atob(base64);
                            const len = binaryString.length;
                            const bytes = new Uint8Array(len);
                            for (let i = 0; i < len; i++) {{
                              bytes[i] = binaryString.charCodeAt(i);
                            }}
                            return bytes.buffer;
                          }}
                          
                          // Synthesize background pad in Offline or Online Context
                          function addProceduralBackground(ctx, duration, volume) {{
                            if (bgLoopType.includes("None")) return [];
                            
                            const oscNodes = [];
                            const gainNode = ctx.createGain();
                            gainNode.gain.setValueAtTime(volume, 0);
                            gainNode.connect(ctx.destination);
                            
                            if (bgLoopType.includes("Calm Zen")) {{
                              // C3, E3, G3, B3 warm chords
                              const freqs = [130.81, 164.81, 196.00, 246.94];
                              freqs.forEach(f => {{
                                const osc = ctx.createOscillator();
                                osc.type = 'sine';
                                osc.frequency.setValueAtTime(f, 0);
                                osc.connect(gainNode);
                                oscNodes.push(osc);
                              }});
                            }} else if (bgLoopType.includes("Deep Tech")) {{
                              // Slow triangle pulse on low E (82.41 Hz)
                              const osc = ctx.createOscillator();
                              osc.type = 'triangle';
                              osc.frequency.setValueAtTime(82.41, 0);
                              
                              // Create periodic pulsing
                              const pulseGain = ctx.createGain();
                              pulseGain.gain.setValueAtTime(volume, 0);
                              
                              // LFO to modulate volume
                              const lfo = ctx.createOscillator();
                              lfo.type = 'sine';
                              lfo.frequency.setValueAtTime(1.5, 0); // 1.5 Hz pulse rate
                              const lfoGain = ctx.createGain();
                              lfoGain.gain.setValueAtTime(volume * 0.8, 0);
                              
                              lfo.connect(lfoGain);
                              lfoGain.connect(pulseGain.gain);
                              osc.connect(pulseGain);
                              pulseGain.connect(ctx.destination);
                              
                              oscNodes.push(osc, lfo);
                            }} else if (bgLoopType.includes("Cosmic Drone")) {{
                              // Filtered Sawtooth pad
                              const osc1 = ctx.createOscillator();
                              const osc2 = ctx.createOscillator();
                              osc1.type = 'sine';
                              osc2.type = 'sawtooth';
                              
                              osc1.frequency.setValueAtTime(65.41, 0); // Low C2
                              osc2.frequency.setValueAtTime(65.7, 0);  // Slightly detuned C2
                              
                              const lowpass = ctx.createBiquadFilter();
                              lowpass.type = 'lowpass';
                              lowpass.Q.setValueAtTime(5, 0);
                              lowpass.frequency.setValueAtTime(200, 0);
                              
                              // Sweep filter over time
                              lowpass.frequency.exponentialRampToValueAtTime(800, duration / 2);
                              lowpass.frequency.exponentialRampToValueAtTime(200, duration);
                              
                              osc1.connect(lowpass);
                              osc2.connect(lowpass);
                              lowpass.connect(gainNode);
                              oscNodes.push(osc1, osc2);
                            }}
                            
                            return oscNodes;
                          }}
                          
                          async function initAudio() {{
                            if (!audioCtx) {{
                              audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                              const arrBuf = base64ToArrayBuffer(speechBase64);
                              decodedBuffer = await audioCtx.decodeAudioData(arrBuf);
                            }}
                          }}
                          
                          async function playMixed() {{
                            stopMixed();
                            document.getElementById('player-status').innerText = 'LOADING';
                            
                            try {{
                              await initAudio();
                              
                              const sourceNode = audioCtx.createBufferSource();
                              sourceNode.buffer = decodedBuffer;
                              sourceNode.playbackRate.value = playbackRateSpeed;
                              
                              // Setup Analyser for Visualizer
                              const analyser = audioCtx.createAnalyser();
                              analyser.fftSize = 64;
                              sourceNode.connect(analyser);
                              analyser.connect(audioCtx.destination);
                              
                              // Start visualizer animation
                              visualize(analyser);
                              
                              // Background loops
                              const duration = decodedBuffer.duration / playbackRateSpeed;
                              const volume = bgVolPercent / 100.0;
                              const synths = addProceduralBackground(audioCtx, duration, volume);
                              
                              activeNodes = [sourceNode, ...synths];
                              
                              sourceNode.start(0);
                              synths.forEach(s => s.start(0));
                              
                              document.getElementById('player-status').innerText = 'PLAYING';
                              document.getElementById('player-status').style.background = '#065f46';
                              document.getElementById('player-status').style.color = '#a7f3d0';
                              
                              sourceNode.onended = () => {{
                                stopMixed();
                              }};
                            }} catch(err) {{
                              console.error(err);
                              document.getElementById('player-status').innerText = 'ERROR';
                            }}
                          }}
                          
                          function stopMixed() {{
                            if (activeNodes.length > 0) {{
                              activeNodes.forEach(n => {{
                                try {{ n.stop(0); }} catch(e) {{}}
                              }});
                              activeNodes = [];
                            }}
                            if (animationId) {{
                              cancelAnimationFrame(animationId);
                              animationId = null;
                            }}
                            
                            // Clear canvas
                            const canvas = document.getElementById('visualizer');
                            const canvasCtx = canvas.getContext('2d');
                            canvasCtx.clearRect(0, 0, canvas.width, canvas.height);
                            
                            document.getElementById('player-status').innerText = 'READY';
                            document.getElementById('player-status').style.background = '#374151';
                            document.getElementById('player-status').style.color = '#9ca3af';
                          }}
                          
                          function visualize(analyser) {{
                            const canvas = document.getElementById('visualizer');
                            const canvasCtx = canvas.getContext('2d');
                            const bufferLength = analyser.frequencyBinCount;
                            const dataArray = new Uint8Array(bufferLength);
                            
                            canvas.width = canvas.clientWidth;
                            canvas.height = canvas.clientHeight;
                            
                            function draw() {{
                              animationId = requestAnimationFrame(draw);
                              analyser.getByteFrequencyData(dataArray);
                              
                              canvasCtx.fillStyle = '#030712';
                              canvasCtx.fillRect(0, 0, canvas.width, canvas.height);
                              
                              const barWidth = (canvas.width / bufferLength) * 1.5;
                              let barHeight;
                              let x = 0;
                              
                              for(let i = 0; i < bufferLength; i++) {{
                                barHeight = dataArray[i] / 2;
                                
                                // Gradient color
                                const g = canvasCtx.createLinearGradient(0, canvas.height, 0, 0);
                                g.addColorStop(0, '#047857');
                                g.addColorStop(1, '#10b981');
                                
                                canvasCtx.fillStyle = g;
                                canvasCtx.fillRect(x, canvas.height - barHeight, barWidth - 1, barHeight);
                                x += barWidth;
                              }}
                            }}
                            
                            draw();
                          }}
                          
                          // Encode mixed buffer to WAV and trigger download
                          async function downloadMixed() {{
                            await initAudio();
                            document.getElementById('player-status').innerText = 'EXPORTING';
                            
                            const duration = decodedBuffer.duration / playbackRateSpeed;
                            
                            const offlineCtx = new OfflineAudioContext(
                              2, 
                              decodedBuffer.sampleRate * duration, 
                              decodedBuffer.sampleRate
                            );
                            
                            const speechNode = offlineCtx.createBufferSource();
                            speechNode.buffer = decodedBuffer;
                            speechNode.playbackRate.value = playbackRateSpeed;
                            speechNode.connect(offlineCtx.destination);
                            
                            const volume = bgVolPercent / 100.0;
                            const synths = addProceduralBackground(offlineCtx, duration, volume);
                            
                            speechNode.start(0);
                            synths.forEach(s => s.start(0));
                            
                            const renderedBuffer = await offlineCtx.startRendering();
                            const wavBlob = bufferToWav(renderedBuffer);
                            
                            const url = URL.createObjectURL(wavBlob);
                            const dlLink = document.getElementById('download-link');
                            dlLink.href = url;
                            dlLink.download = 'ai_speech_mix.wav';
                            dlLink.click();
                            
                            document.getElementById('player-status').innerText = 'EXPORTED';
                            setTimeout(() => {{
                              document.getElementById('player-status').innerText = 'READY';
                            }}, 2000);
                          }}
                          
                          // WAV encoding algorithm
                          function bufferToWav(buffer) {{
                            let numOfChan = buffer.numberOfChannels,
                                length = buffer.length * numOfChan * 2 + 44,
                                bufferArr = new ArrayBuffer(length),
                                view = new DataView(bufferArr),
                                channels = [], i, sample,
                                offset = 0,
                                pos = 0;

                            setUint32(0x46464952);                         // "RIFF"
                            setUint32(length - 8);                         // file length - 8
                            setUint32(0x45564157);                         // "WAVE"
                            setUint32(0x20746d66);                         // "fmt " chunk
                            setUint32(16);                                 // chunk length
                            setUint16(1);                                  // sample format (raw PCM)
                            setUint16(numOfChan);                          // channel count
                            setUint32(buffer.sampleRate);                  // sample rate
                            setUint32(buffer.sampleRate * 2 * numOfChan);  // byte rate
                            setUint16(numOfChan * 2);                      // block align
                            setUint16(16);                                 // bits per sample
                            setUint32(0x61746164);                         // "data" - chunk
                            setUint32(length - pos - 4);                   // chunk length

                            for(i=0; i<buffer.numberOfChannels; i++)
                              channels.push(buffer.getChannelData(i));

                            while(pos < length) {{
                              for(i=0; i<numOfChan; i++) {{
                                sample = Math.max(-1, Math.min(1, channels[i][offset]));
                                sample = (sample < 0 ? sample * 0x8000 : sample * 0x7FFF);
                                view.setInt16(pos, sample, true);
                                pos += 2;
                              }}
                              offset++;
                            }}

                            return new Blob([bufferArr], {{type: "audio/wav"}});

                            function setUint16(data) {{
                              view.setUint16(pos, data, true);
                              pos += 2;
                            }}
                            function setUint32(data) {{
                              view.setUint32(pos, data, true);
                              pos += 4;
                            }}
                          }}
                        </script>
                        """
                        # Render component in Streamlit page container
                        st.components.v1.html(mixer_html, height=220)

    # ----------------------------------------------------
    # SUBTAB 2: SPEECH TO TEXT TRANSCRIPTION
    # ----------------------------------------------------
    with audio_subtab2:
        st.header("Speech-to-Text Transcription")
        st.write("Upload a WAV voice recording to transcribe it into text. (Supports keyless translation offline fallback).")
        
        uploaded_audio = st.file_uploader(
            "Choose a WAV recording file (Max 10MB):",
            type=["wav"],
            help="Please upload standard 16-bit PCM WAV audio files."
        )
        
        if st.button("Transcribe Audio File", use_container_width=True):
            if uploaded_audio is None:
                st.warning("Please upload a WAV file first.")
            else:
                with st.spinner("Analyzing and transcribing audio content... Please wait..."):
                    transcription_output = transcribe_audio_file(uploaded_audio)
                    
                    if "❌" in transcription_output:
                        st.error(transcription_output)
                    else:
                        st.success("Audio transcribed successfully!")
                        st.text_area("Transcription:", value=transcription_output, height=150)
                        
                        # Quick options
                        st.download_button(
                            label="📥 Download Transcript (.txt)",
                            data=transcription_output,
                            file_name="transcript.txt",
                            mime="text/plain"
                        )

# ----------------------------------------------------
# TAB 3: IMAGE VISION & CAPTIONING
# ----------------------------------------------------
with tab3:
    st.header("🖼️ Image Vision & Captioning")
    st.write("Upload any image and let our AI Vision model describe its contents. You can copy the generated description or directly set it as your next image generation prompt!")

    uploaded_vision_img = st.file_uploader(
        "Choose an image file (PNG, JPG, JPEG):",
        type=["png", "jpg", "jpeg"],
        key="vision_image_uploader"
    )

    if uploaded_vision_img is not None:
        st.image(uploaded_vision_img, caption="Uploaded Image", use_container_width=True)
        
        if st.button("🔍 Generate AI Caption", use_container_width=True):
            with st.spinner("Analyzing image content... Please wait..."):
                img_bytes = uploaded_vision_img.getvalue()
                caption = caption_image(img_bytes)
                
                if "🔑" in caption or "🌐" in caption or "⚠️" in caption:
                    st.error(caption)
                else:
                    st.session_state["vision_caption"] = caption.capitalize()
                    st.success("Analysis complete!")

        # Display caption and action button if present in state
        if st.session_state["vision_caption"]:
            st.info(f"📝 **AI Caption:** {st.session_state['vision_caption']}")
            if st.button("✨ Set as Image Prompt", use_container_width=True):
                st.session_state["img_prompt_input"] = st.session_state["vision_caption"]
                st.success("🚀 Prompt set! Go to the 'Text-to-Image' tab to generate.")
    else:
        st.session_state["vision_caption"] = ""


# ----------------------------------------------------
# TAB 4: PROMPT LIBRARY
# ----------------------------------------------------
with tab4:
    st.header("📚 Prompt Library")
    st.write("Browse curated, high-quality, and pre-tested prompt templates. Click 'Use Prompt' to load any template into the Image Generator tab.")

    selected_category = st.selectbox(
        "Select Category:",
        list(PROMPT_TEMPLATES.keys())
    )

    prompts_in_category = PROMPT_TEMPLATES[selected_category]

    for idx, prompt_text in enumerate(prompts_in_category):
        with st.container():
            st.markdown(
                f"""
                <div style="background: #1e293b; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 5px solid #10b981;">
                    <p style="color: #f1f5f9; margin: 0; font-size: 14px; font-style: italic;">"{prompt_text}"</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Use unique key for each button
            if st.button("📋 Use Prompt", key=f"btn_use_p_{selected_category}_{idx}"):
                st.session_state["img_prompt_input"] = prompt_text
                st.success("🚀 Template copied to prompt! Navigate to the 'Text-to-Image' tab to generate.")
            st.write("")

# ----------------------------------------------------
# TAB 5: SESSION GALLERY
# ----------------------------------------------------
with tab5:
    st.header("🗂️ My Session Gallery")
    st.write("View and manage all images generated during your active session.")

    if not st.session_state["gallery"]:
        st.info("No images generated in this session yet. Go to 'Text-to-Image' to generate beautiful artwork!")
    else:
        # Gallery Action Buttons
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            # Download All as ZIP
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w") as zip_file:
                for idx, item in enumerate(st.session_state["gallery"]):
                    img = item["image"]
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format="PNG")
                    zip_file.writestr(f"gallery_{idx+1}_{item['seed']}.png", img_bytes.getvalue())
            
            st.download_button(
                label="📥 Export All as ZIP",
                data=zip_buf.getvalue(),
                file_name="ai_creative_studio_gallery.zip",
                mime="application/zip",
                use_container_width=True
            )
        with col_g2:
            if st.button("🗑️ Clear Gallery", use_container_width=True):
                st.session_state["gallery"] = []
                st.success("Gallery cleared!")
                st.rerun()

        st.write("---")

        # Gallery grid
        gallery_images = st.session_state["gallery"]
        grid_cols = st.columns(2)
        
        for idx, item in enumerate(gallery_images):
            col_idx = idx % 2
            with grid_cols[col_idx]:
                st.image(item["image"], caption=f"Prompt: {item['prompt'][:50]}... (Seed: {item['seed']})", use_container_width=True)
                
                # Individual download button
                img_buf = io.BytesIO()
                item["image"].save(img_buf, format="PNG")
                
                st.download_button(
                    label=f"📥 Download Image {idx+1}",
                    data=img_buf.getvalue(),
                    file_name=f"gallery_{idx+1}_{item['seed']}.png",
                    mime="image/png",
                    key=f"dl_gallery_btn_{idx}_{item['seed']}"
                )
                st.write("")

