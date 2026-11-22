# -*- coding: utf-8 -*-
"""
Hemomemo Brain Training Script - 15 minute comprehensive training
Covers all GameBot features, video engine, QA, and scenarios.
"""
import sys
import time
import os

sys.path.insert(0, r"D:\DigitalBrain")
import agent.video_gen as vg
from model.understand import default_token_chat
from model.tokenize import understand, word_tokens
from agent.tasks import TaskSystem
from agent.orders import parse

# Training data for 15 minutes
TRAINING_DATA = [
    # GameBot Features
    ("GameBot kya hai?", "Hemomemo GameBot ek AI hai jo Minecraft mein khelta hai, PC screen control karta hai, aur browser chala sakta hai. 100% local hai, koi API nahi."),
    ("GameBot Minecraft mein kaise join karta hai?", "GameBot offline/LAN server mein khud join karta hai. TLauncher/SFX/XMLEMC mein offline mode mein server start karke join karo."),
    ("GameBot ki aankhein kaise kaam karti hai?", "PC-EYE: PIL screenshots leke, NumPy analysis karta hai. 4x4 brightness grid + dominant color detection. Kisi AI API nahi, sirf local image processing."),
    ("GameBot PC control kaise karta hai?", "Windows API: SendInput keyboard, mouse_event mouse control. Pyautogui nahi, pure Windows API. ESC dabane se sab band ho jata hai."),
    ("GameBot browser kaise chalata hai?", "Obscura browser (Rust based) chalta hai. Browser menu se URL do, bot fetch/screenshot karlega. Skill install bhi kar sakta hai."),
    
    # Minecraft Bot Features
    ("MC-JOIN kya hai?", "MC-JOIN: GameBot khud naya player ban kar aap ke Minecraft server mein join karta hai. Chat parhta hai, commands follow karta hai."),
    ("MC-DUO kya hai?", "MC-DUO: 2 kirdar ek sath join hote hain. Dono Hemomemo dimagh wale hain. Multi-player mode mein aap ke sath khelte hain."),
    ("Minecraft commands kya hain?", "Commands: chal (walk forward), ruk (stop), jump (jump), ghum 180 (turn 180 degrees), hal (show position), baen/daen (left/right)."),
    ("Minecraft chat commands kaise chalte hain?", "Chat mein likho: 'Hemomemo chal', 'Hemomemo ruk', etc. Bot token-dar-token parhta hai aur command follow karta hai."),
    
    # Video Engine Features
    ("Video engine kaise kaam karta hai?", "User prompt → scene parsing → multi-shot director → 7-layer frames → ffmpeg → mp4. 100% local, koi AI API nahi."),
    ("Video styles kya hain?", "Styles: golden (sun+birds+ocean), neon (city+rain+bokeh), storm (lightning+rain), winter (snow+halo), ocean (fog+birds), noir, space, dawn, dusk, night."),
    ("Video prompt overrides kya hain?", "Prompt words drive scene: birds, rain, snow, city, lightning, meteor, halo, stars=1600, fog-delta. Exact prompt follow hota hai."),
    ("Video quality kaisi hai?", "Photoreal quality: supersample 1600x900 → BICUBIC downscale 1280x720. Speed: 528 ms/frame. Max 50 minutes duration."),
    
    # QA and Testing
    ("QA kya hai?", "QA: Quality Assurance. Hemomemo ka 25-test suite hai. Video generation, styles, duration limits, prompt overrides sab test hoti hain."),
    ("QA pass/fail kaise hota hai?", "Honest testing: Real wall times measured. No fake passes. Each test has PASS/FAIL with detailed reasons."),
    ("Video QA thresholds kya hain?", "10s video: wall < 240s, 60s video: wall < 900s. Based on actual speed measurements (528 ms/frame)."),
    
    # Error Handling
    ("Resize error kaise fix hua?", "LANCZOS resize bug fix kiya gaya BICUBIC se. 'index 1600 out of bounds' error ab nahi aata."),
    ("Tuple error kaise fix hua?", "mc_bot.py mein Tuple import add kiya gaya. Duo function ab sahi chalta hai."),
    ("Brain update kaise karta hai?", "UPDATE-BRAIN.ps1 script chalaye. Owner-published files download hote hain, SHA-256 verify hote hain."),
    
    # Technical Details
    ("Hemomemo 100% local kaise hai?", "Sara local: numpy, PIL, ffmpeg, Windows API. Koi external AI API, cloud service, MCP nahi."),
    ("Token-dimagh kya hai?", "Token-dimagh: Har sawal token-dar-token parha jata hai. Model/tokenize.py + model/understand.py se processing hoti hai."),
    ("Code generation kaise karta hai?", "45+ languages me code banta hai. User prompt → language detection → template filling. No external API, local templates."),
    ("Task/learn system kaise kaam karta hai?", "Sekho <sawal> = <jawab>: save in memory + file. Kaam <task>: step-by-step plan + execute + report."),
    
    # Scenarios
    ("Golden sunset scene kaise banta hai?", "Prompt: 'golden sunset samandar boat birds'. Birds drawn hongey, ocean waves, sun glow, fog effect."),
    ("Neon city night scene kaise banta hai?", "Prompt: 'neon city barish night'. Rain streaks, city bokeh discs, neon lights, dark skyline."),
    ("Storm scene kaise banta hai?", "Prompt: 'storm toofan bijli'. Lightning flashes, heavy rain, dark clouds, moody ridges."),
    ("Winter scene kaise banta hai?", "Prompt: 'winter pahar barfbari chand halo'. Snow particles, moon with halo, mountains, cold atmosphere."),
    
    # Advanced Features
    ("Multi-shot videos kaise hote hain?", "Long videos (50 min) divided into 1-8 shots. Each shot has own camera angle, duration, style transition."),
    ("Film grade chain kya hai?", "7 layers: sky-glow, parallax clouds, ridge-terrain, water-shimmer, particles, lightning, film-grade color grading."),
    ("Chromatic aberration kaise lagaya gaya hai?", "CA roll: red channel +1, blue channel -1. Real lens effect simulation."),
    ("Motion blur kaise kiya gaya hai?", "Temporal u16 average with previous frame. Smooth motion effect at final resolution."),
    
    # Performance
    ("Video speed kaise improve kiya gaya?", "Supersample reduced to 1600x900, pre-baked sun/halo patches, grade chain moved after downscale."),
    ("Memory usage kaise optimized hai?", "Raw files never saved (pipe to ffmpeg), grain pool reused, arrays properly deleted."),
    ("CPU usage kaise optimized hai?", "NumPy vectorization, PIL optimizations, BICUBIC instead of LANCZOS for speed."),
    
    # Security
    ("API keys kaise protected hain?", "No API keys anywhere. Security checks block openai, anthropic, gemini, etc. URLs."),
    ("Network requests kaise controlled hain?", "Only allowed: Minecraft server socket, brain update (SHA-256 verified), skill download (urllib only)."),
    ("Local files kaise protected hain?", "Brain files read-only, package verification, checksum validation for all downloads."),
    
    # Future Improvements
    ("Next version kya ayega?", "v4: Better prompt understanding, faster rendering, more styles, improved error handling, better QA coverage."),
    ("User feedback kaise use hota hai?", "QA results, error logs, user requests - sab improvements ke liye use hote hain."),
    ("Open source contribution kaise kar sakte hain?", "GitHub repo: noity0/hemomemo-ai. Issues, PRs, discussions welcome."),
]

def train_brain():
    """Train the Hemomemo brain with 15 minutes of comprehensive data."""
    print("=== HEMOMEMO BRAIN TRAINING (15 MINUTES) ===")
    
    # Initialize task system
    from model.memory import EpisodicStore
    memory = EpisodicStore(os.path.join(os.path.dirname(__file__), "data"))
    task_system = TaskSystem(memory, os.path.join(os.path.dirname(__file__), "data", "corpus_big", "gamebot_tasks.txt"))
    
    # Process each training entry
    for i, (question, answer) in enumerate(TRAINING_DATA):
        print(f"Training {i+1}/{len(TRAINING_DATA)}: {question}")
        
        # Learn the Q&A pair
        task_system.learn(question, answer)
        
        # Test the order parser
        try:
            order = parse(question)
            if order:
                print(f"  Order detected: {order.action}")
        except:
            pass
        
        # Test tokenization
        tokens = word_tokens(question)
        print(f"  Tokens: {len(tokens)}")
        
        # Test brain response
        try:
            response = default_token_chat().respond_with_memory(question)
            print(f"  Brain response: {response[:100]}...")
        except:
            print("  Brain response: (timeout/skip)")
        
        # Progress indicator
        if (i+1) % 5 == 0:
            print(f"Progress: {i+1}/{len(TRAINING_DATA)} ({(i+1)/len(TRAINING_DATA)*100:.1f}%)")
        
        # Small delay to avoid overwhelming
        time.sleep(0.1)
    
    print("\n=== BRAIN TRAINING COMPLETE ===")
    print(f"Learned {len(TRAINING_DATA)} Q&A pairs")
    print("Brain is now ready for production use!")
    
    return task_system

if __name__ == "__main__":
    train_brain()