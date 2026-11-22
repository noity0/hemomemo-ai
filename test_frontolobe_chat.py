#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify frontolobe integration in chat functionality.
"""

import sys
import os
sys.path.insert(0, 'D:\\DigitalBrain')

def test_frontolobe_chat():
    """Test the frontolobe-enhanced chat functionality."""
    
    # Import the chat function
    from app.hemomemo_app import chat_async
    
    # Test inputs
    test_inputs = [
        "Can you help me create a video about mountains?",
        "I'm feeling frustrated with this code",
        "What's the weather like today?",
        "Hello! How are you?",
        "I need a solution for this problem as soon as possible"
    ]
    
    print("Testing Frontolobe-Enhanced Chat:")
    print("=" * 50)
    
    def on_done(text, meta):
        """Callback function for chat results."""
        print(f"\nResponse: {text}")
        print(f"Source: {meta.get('source', 'unknown')}")
        
        # Print understanding if available
        if 'understanding' in meta:
            understanding = meta['understanding']
            print(f"Intent: {understanding['intent']['type']}")
            print(f"Emotional Tone: {understanding['emotional_tone']['tone']}")
            print(f"Contextual Clues: {understanding['contextual_clues']}")
            print(f"Clarification Needed: {understanding['clarification_needed']}")
        print("-" * 50)
    
    # Test each input
    for i, test_input in enumerate(test_inputs, 1):
        print(f"\nTest {i}: {test_input}")
        print("Processing...")
        
        # Start the chat
        chat_async(test_input, on_done, think="auto")
        
        # Wait a bit for the response
        import time
        time.sleep(3)

if __name__ == "__main__":
    test_frontolobe_chat()