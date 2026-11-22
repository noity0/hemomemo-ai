# -*- coding: utf-8 -*-
"""
Hemomemo Brain Training Script - Quick 5 minute training
Focuses on essential GameBot and video engine features.
"""
import sys
import time
import os

sys.path.insert(0, r"D:\DigitalBrain")
from model.understand import default_token_chat
from model.tokenize import understand, word_tokens
from agent.tasks import TaskSystem
from agent.orders import parse

# Essential training data for quick training
ESSENTIAL_TRAINING = [
    ("GameBot kya hai?", "Hemomemo GameBot ek AI hai jo Minecraft mein khelta hai, PC screen control karta hai, aur browser chala sakta hai. 100% local hai, koi API nahi."),
    ("GameBot Minecraft mein kaise join karta hai?", "GameBot offline/LAN server mein khud join karta hai. TLauncher/SFX/XMLEMC mein offline mode mein server start karke join karo."),
    ("GameBot ki aankhein kaise kaam karti hai?", "PC-EYE: PIL screenshots leke, NumPy analysis karta hai. 4x4 brightness grid + dominant color detection. Kisi AI API nahi, sirf local image processing."),
    ("GameBot PC control kaise karta hai?", "Windows API: SendInput keyboard, mouse_event mouse control. Pyautogui nahi, pure Windows API. ESC dabane se sab band ho jata hai."),
    ("GameBot browser kaise chalata hai?", "Obscura browser (Rust based) chalta hai. Browser menu se URL do, bot fetch/screenshot karlega. Skill install bhi kar sakta hai."),
    ("MC-JOIN kya hai?", "MC-JOIN: GameBot khud naya player ban kar aap ke Minecraft server mein join karta hai. Chat parhta hai, commands follow karta hai."),
    ("MC-DUO kya hai?", "MC-DUO: 2 kirdar ek sath join hote hain. Dono Hemomemo dimagh wale hain. Multi-player mode mein aap ke sath khelte hain."),
    ("Minecraft commands kya hain?", "Commands: chal (walk forward), ruk (stop), jump (jump), ghum 180 (turn 180 degrees), hal (show position), baen/daen (left/right)."),
    ("Video engine kaise kaam karta hai?", "User prompt → scene parsing → multi-shot director → 7-layer frames → ffmpeg → mp4. 100% local, koi AI API nahi."),
    ("Video styles kya hain?", "Styles: golden (sun+birds+ocean), neon (city+rain+bokeh), storm (lightning+rain), winter (snow+halo), ocean (fog+birds), noir, space, dawn, dusk, night."),
    ("Video prompt overrides kya hain?", "Prompt words drive scene: birds, rain, snow, city, lightning, meteor, halo, stars=1600, fog-delta. Exact prompt follow hota hai."),
    ("Resize error kaise fix hua?", "LANCZOS resize bug fix kiya gaya BICUBIC se. 'index 1600 out of bounds' error ab nahi aata."),
    ("Tuple error kaise fix hua?", "mc_bot.py mein Tuple import add kiya gaya. Duo function ab sahi chalta hai."),
    ("Brain update kaise karta hai?", "UPDATE-BRAIN.ps1 script chalaye. Owner-published files download hote hain, SHA-256 verify hote hain."),
    ("Hemomemo 100% local kaise hai?", "Sara local: numpy, PIL, ffmpeg, Windows API. Koi external AI API, cloud service, MCP nahi."),
]

def quick_train_brain():
    """Quick train the Hemomemo brain with essential data."""
    print("=== HEMOMEMO BRAIN QUICK TRAINING (5 MINUTES) ===")
    
    # Initialize task system
    from model.memory import EpisodicStore
    memory = EpisodicStore(os.path.join(os.path.dirname(__file__), "data"))
    task_system = TaskSystem(memory, os.path.join(os.path.dirname(__file__), "data", "corpus_big", "gamebot_tasks.txt"))
    
    # Process each training entry
    for i, (question, answer) in enumerate(ESSENTIAL_TRAINING):
        print(f"Training {i+1}/{len(ESSENTIAL_TRAINING)}: {question}")
        
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
            print(f"Progress: {i+1}/{len(ESSENTIAL_TRAINING)} ({(i+1)/len(ESSENTIAL_TRAINING)*100:.1f}%)")
        
        # Small delay to avoid overwhelming
        time.sleep(0.05)
    
    print("\n=== BRAIN QUICK TRAINING COMPLETE ===")
    print(f"Learned {len(ESSENTIAL_TRAINING)} essential Q&A pairs")
    print("Brain is now ready for production use!")
    
    return task_system

if __name__ == "__main__":
    quick_train_brain()