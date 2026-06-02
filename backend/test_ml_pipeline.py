import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "AI Creative Studio API is running"

def test_enhance_prompt():
    response = client.get("/api/enhance-prompt?prompt=futuristic cat")
    assert response.status_code == 200
    assert "enhanced" in response.json()

def test_style_presets():
    response = client.get("/api/style-presets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert "photorealistic" in response.json()

def test_aspect_ratios():
    response = client.get("/api/aspect-ratios")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert "1:1" in response.json()

def test_generate_text():
    payload = {
        "prompt": "A magical dragon in a forest",
        "genre": "Fantasy",
        "tone": "Mysterious",
        "word_count": 50
    }
    response = client.post("/api/generate-text", json=payload)
    assert response.status_code == 200
    assert "text" in response.json()
    assert len(response.json()["text"]) > 0

def test_tts():
    payload = {
        "text": "Hello world",
        "mode": "google",
        "language": "en"
    }
    response = client.post("/api/tts", json=payload)
    assert response.status_code == 200
    assert "audio" in response.json()
    assert "translated_text" in response.json()

def test_generate_image_pollinations():
    payload = {
        "prompt": "minimalist red circle",
        "style": "none",
        "aspect_ratio": "1:1",
        "batch_count": 1,
        "seed": 42,
        "provider": "pollinations"
    }
    response = client.post("/api/generate-image", json=payload)
    assert response.status_code == 200
    assert "images" in response.json()
    assert len(response.json()["images"]) > 0
    assert "image" in response.json()["images"][0]



