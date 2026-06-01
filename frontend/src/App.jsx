import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ImageGenerator from './components/ImageGenerator';
import AudioSuite from './components/AudioSuite';
import VisionAI from './components/VisionAI';
import PromptLibrary from './components/PromptLibrary';
import Gallery from './components/Gallery';
import CreativeWriter from './components/CreativeWriter';
import BackgroundRemover from './components/BackgroundRemover';
import VoiceCanvas from './components/VoiceCanvas';

export default function App() {
  const [activeTab, setActiveTab] = useState('image');

  // Gallery persisted in localStorage
  const [gallery, setGallery] = useState(() => {
    try {
      const saved = localStorage.getItem('ai_gallery');
      return saved ? JSON.parse(saved) : [];
    } catch { return []; }
  });

  useEffect(() => {
    localStorage.setItem('ai_gallery', JSON.stringify(gallery));
  }, [gallery]);

  // Shared prompt: set by PromptLibrary / VisionAI → read by ImageGenerator
  const [sharedPrompt, setSharedPrompt] = useState('');

  const addToGallery = (item) => setGallery(prev => [item, ...prev]);

  const goToImageTab = (prompt) => {
    if (prompt) setSharedPrompt(prompt);
    setActiveTab('image');
  };

  const pages = {
    image:      <ImageGenerator addToGallery={addToGallery} sharedPrompt={sharedPrompt} setSharedPrompt={setSharedPrompt} />,
    audio:      <AudioSuite />,
    writer:     <CreativeWriter goToImageTab={goToImageTab} />,
    voicecanvas:<VoiceCanvas addToGallery={addToGallery} />,
    bgremover:  <BackgroundRemover gallery={gallery} addToGallery={addToGallery} />,
    vision:     <VisionAI goToImageTab={goToImageTab} />,
    library:    <PromptLibrary goToImageTab={goToImageTab} />,
    gallery:    <Gallery gallery={gallery} setGallery={setGallery} />,
  };

  return (
    <div className="app-layout">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} galleryCount={gallery.length} />
      <main className="main-content">
        {pages[activeTab]}
      </main>
    </div>
  );
}
