# -*- coding: utf-8 -*-
"""
🧠 Frontolobe - Higher-Level Understanding Module

This module implements the brain's frontolobe functionality to better understand
the actual intent behind user input. It goes beyond literal interpretation to
understand context, intent, and emotional tone.

Features:
    ✓ Contextual understanding of user input
    ✓ Intent recognition and clarification
    ✓ Emotional tone analysis
    ✓ Multi-layered interpretation
    ✓ Cross-reference with knowledge base
    ✓ Memory integration for better context

Usage:
    from model.frontolobe import FrontolobeProcessor
    
    processor = FrontolobeProcessor()
    understanding = processor.understand_user_input(user_input)
"""

import os
import re
import json
import time
from collections import defaultdict
import numpy as np

# Import core components
import sys
if __name__ == "__main__":
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from model.understand import default_token_chat
from model.cognition import FlowTracker

class FrontolobeProcessor:
    """
    Frontolobe processor for higher-level understanding of user input.
    """
    
    def __init__(self):
        """Initialize the frontolobe processor."""
        self.token_chat = default_token_chat()
        self.cognition = FlowTracker()
        self.memory = defaultdict(list)
        self.knowledge_base = self._load_knowledge_base()
        
    def _load_knowledge_base(self):
        """Load knowledge base for better understanding."""
        knowledge = {
            "intent_patterns": {
                "question": ["?", "how", "what", "why", "when", "where", "who", "which"],
                "request": ["please", "can you", "would you", "could you", "help me"],
                "command": ["do", "make", "create", "generate", "build"],
                "statement": ["i think", "i believe", "i feel", "i want"],
                "greeting": ["hello", "hi", "hey", "assalamualaikum", "salam"],
                "farewell": ["bye", "goodbye", "see you", "allah hafiz"]
            },
            "emotional_indicators": {
                "positive": ["happy", "good", "great", "excellent", "wonderful", "love", "amazing"],
                "negative": ["sad", "angry", "frustrated", "disappointed", "upset", "hate"],
                "neutral": ["okay", "fine", "normal", "regular", "standard"],
                "urgent": ["urgent", "important", "asap", "quickly", "fast", "immediately"]
            },
            "context_clues": {
                "technical": ["code", "programming", "software", "computer", "algorithm"],
                "creative": ["art", "design", "creative", "imagine", "picture", "video"],
                "educational": ["learn", "study", "teach", "explain", "understand"],
                "personal": ["i", "me", "my", "mine", "personal", "private"]
            }
        }
        
        # Load additional knowledge if available
        knowledge_path = os.path.join(ROOT, "knowledge", "frontolobe_knowledge.json")
        if os.path.exists(knowledge_path):
            try:
                with open(knowledge_path, 'r', encoding='utf-8') as f:
                    additional = json.load(f)
                    knowledge.update(additional)
            except Exception as e:
                print(f"Warning: Could not load additional knowledge: {e}")
                
        return knowledge
    
    def understand_user_input(self, user_input, context=None):
        """
        Process user input to understand the actual intent and meaning.
        
        Args:
            user_input (str): The user's input text
            context (dict): Optional context information
            
        Returns:
            dict: Comprehensive understanding of the input
        """
        if not user_input or not user_input.strip():
            return {
                "input": user_input,
                "understanding": "empty_input",
                "intent": "null",
                "confidence": 0.0,
                "emotional_tone": "neutral",
                "contextual_clues": [],
                "clarification_needed": True,
                "response_suggestion": "Please provide some input."
            }
        
        # Normalize input
        normalized = self._normalize_input(user_input)
        
        # Perform multi-layered analysis
        analysis = {
            "input": user_input,
            "normalized": normalized,
            "intent": self._detect_intent(normalized),
            "emotional_tone": self._analyze_emotional_tone(normalized),
            "contextual_clues": self._extract_contextual_clues(normalized),
            "key_concepts": self._extract_key_concepts(normalized),
            "language_style": self._analyze_language_style(normalized),
            "complexity": self._assess_complexity(normalized),
            "time_sensitivity": self._detect_time_sensitivity(normalized),
            "clarification_needed": False,
            "confidence": 0.0,
            "response_suggestion": ""
        }
        
        # Apply cognitive flow for deeper understanding
        self.cognition.stage("understand", f"Processing input: {normalized[:50]}...")
        # For now, just add some cognitive processing
        cognitive_understanding = {
            "cognitive_depth": "deep",
            "processing_time": time.time(),
            "cognitive_steps": ["analyze", "interpret", "contextualize"]
        }
        analysis.update(cognitive_understanding)
        
        # Integrate with memory if context provided
        if context:
            analysis = self._integrate_memory(analysis, context)
        
        # Calculate confidence score
        analysis["confidence"] = self._calculate_confidence(analysis)
        
        analysis["input_text"] = user_input or ""

        # Determine if clarification is needed
        analysis["clarification_needed"] = self._determine_clarification_needs(analysis)
        
        # Generate response suggestion
        analysis["response_suggestion"] = self._generate_response_suggestion(analysis)
        
        # Store in memory
        self.memory["recent_inputs"].append({
            "input": user_input,
            "timestamp": time.time(),
            "understanding": analysis
        })
        
        return analysis
    
    def _normalize_input(self, text):
        """Normalize input text for analysis."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Convert to lowercase for analysis (preserve original for response)
        normalized = text.lower()
        
        # Remove special characters but keep important ones
        normalized = re.sub(r'[^\w\s\?\!\.\,\;\:\-]', ' ', normalized)
        
        return normalized
    
    def _detect_intent(self, text):
        """Detect the primary intent behind the user input."""
        intent_scores = {}
        
        # Check against intent patterns
        for intent_type, patterns in self.knowledge_base["intent_patterns"].items():
            score = 0
            for pattern in patterns:
                if pattern in text:
                    score += 1
            intent_scores[intent_type] = score
        
        # Determine primary intent
        if max(intent_scores.values()) == 0:
            return {
                "type": "statement",
                "confidence": 0.0,
                "scores": intent_scores
            }
        
        primary_intent = max(intent_scores, key=intent_scores.get)
        confidence = intent_scores[primary_intent] / sum(intent_scores.values())
        
        return {
            "type": primary_intent,
            "confidence": confidence,
            "scores": intent_scores
        }
    
    def _analyze_emotional_tone(self, text):
        """Analyze the emotional tone of the input."""
        tone_scores = {}
        
        for tone_type, indicators in self.knowledge_base["emotional_indicators"].items():
            score = 0
            for indicator in indicators:
                if indicator in text:
                    score += 1
            tone_scores[tone_type] = score
        
        # Determine primary tone
        if max(tone_scores.values()) == 0:
            return {
                "tone": "neutral",
                "confidence": 0.0,
                "scores": tone_scores
            }
        
        primary_tone = max(tone_scores, key=tone_scores.get)
        confidence = tone_scores[primary_tone] / sum(tone_scores.values())
        
        return {
            "tone": primary_tone,
            "confidence": confidence,
            "scores": tone_scores
        }
    
    def _extract_contextual_clues(self, text):
        """Extract contextual clues from the input."""
        clues = []
        
        for clue_type, keywords in self.knowledge_base["context_clues"].items():
            for keyword in keywords:
                if keyword in text:
                    clues.append(clue_type)
                    break
        
        return list(set(clues))  # Remove duplicates
    
    def _extract_key_concepts(self, text):
        """Extract key concepts from the input."""
        # Simple concept extraction - can be enhanced with more sophisticated NLP
        words = text.split()
        concepts = []
        
        # Filter out common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        
        for word in words:
            if word not in stop_words and len(word) > 2:
                concepts.append(word)
        
        return list(set(concepts))
    
    def _analyze_language_style(self, text):
        """Analyze the language style of the input."""
        # Count punctuation
        question_marks = text.count('?')
        exclamation_marks = text.count('!')
        periods = text.count('.')
        
        # Calculate average word length
        words = text.split()
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        # Determine style
        if question_marks > 0:
            style = "question"
        elif exclamation_marks > 0:
            style = "excited"
        elif avg_word_length > 7:
            style = "formal"
        else:
            style = "casual"
        
        return {
            "style": style,
            "question_marks": question_marks,
            "exclamation_marks": exclamation_marks,
            "avg_word_length": avg_word_length
        }
    
    def _assess_complexity(self, text):
        """Assess the complexity of the input."""
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Calculate metrics
        word_count = len(words)
        sentence_count = len(sentences)
        avg_words_per_sentence = word_count / sentence_count if sentence_count else 0
        
        # Determine complexity level
        if word_count < 10 and sentence_count == 1:
            complexity = "simple"
        elif word_count < 50 and avg_words_per_sentence < 15:
            complexity = "moderate"
        else:
            complexity = "complex"
        
        return {
            "level": complexity,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_words_per_sentence": avg_words_per_sentence
        }
    
    def _detect_time_sensitivity(self, text):
        """Detect if the input has time-sensitive elements."""
        time_keywords = ["urgent", "asap", "immediately", "quickly", "fast", "now", "today", "tonight"]
        
        for keyword in time_keywords:
            if keyword in text:
                return True
        
        return False
    
    def _integrate_memory(self, analysis, context):
        """Integrate memory with current analysis."""
        # Look for similar past inputs
        similar_inputs = []
        
        for past_input in self.memory["recent_inputs"][-10:]:  # Check last 10 inputs
            if self._calculate_similarity(analysis["normalized"], past_input["understanding"]["normalized"]) > 0.7:
                similar_inputs.append(past_input)
        
        # Add context information
        analysis["context"] = {
            "similar_inputs": similar_inputs,
            "session_context": context.get("session", {}),
            "user_profile": context.get("user_profile", {})
        }
        
        return analysis
    
    def _calculate_similarity(self, text1, text2):
        """Calculate similarity between two texts."""
        # Simple Jaccard similarity
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if len(words1) == 0 or len(words2) == 0:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_confidence(self, analysis):
        """Calculate confidence score for the understanding."""
        # Factors affecting confidence
        intent_confidence = analysis["intent"].get("confidence", 0.5)
        emotional_confidence = analysis["emotional_tone"].get("confidence", 0.5)
        complexity_factor = 1.0 if analysis["complexity"]["level"] == "simple" else 0.8
        
        # Calculate overall confidence
        confidence = (intent_confidence + emotional_confidence) / 2 * complexity_factor
        
        return min(confidence, 1.0)
    
    def _determine_clarification_needs(self, analysis):
        """Determine if clarification is needed."""
        # If confidence is low, clarification might be needed
        if analysis["confidence"] < 0.5:
            return True
        
        # If input is very complex, clarification might help
        if analysis["complexity"]["level"] == "complex":
            return True
        
        # If intent is unclear, clarification is needed
        if analysis["intent"]["type"] == "statement" and analysis["intent"]["confidence"] < 0.3:
            return True
        
        return False
    
    def _generate_response_suggestion(self, analysis):
        """Ab ye USER-visible hai — is liye: user-ka-text hamesha quote,
        aur koi English-canned-guided-template asli jawab ki jagah NAHI."""
        intent = analysis["intent"]["type"]
        said = (analysis.get("input_text") or "").strip()
        if len(said) > 80:
            said = said[:77].rstrip() + "…"
        if intent == "question":
            return ("aap ne sawal poocha: «%s» — bas thora tafseel dein"
                    " (kis cheez ke baray me) to foran jawab dunga." % said)
        if intent == "request":
            return ("aap ka request mila: «%s» — ek lafz me bata dein kya"
                    " karna hai (banana/dikhana/likhna)?" % said)
        if intent == "command":
            return ("hukum samajh aaya: «%s» — confirm karein: yehi karna hai?"
                    % said)
        if intent == "greeting":
            return "Assalamu Alaikum! Main Hazir hoon — kya madad karun?"
        if intent == "farewell":
            return "Khush rahiye — jab zaroorat ho main yahin hoon."
        # statement / unknown
        return ("aap ne likha: «%s» — ise thora kholein (kya jaanna hai,"
                " kya banana hai) to behtar-jawab dunga." % said)
    
    def get_memory_summary(self):
        """Get a summary of recent memory inputs."""
        return {
            "total_inputs": len(self.memory["recent_inputs"]),
            "recent_inputs": self.memory["recent_inputs"][-5:],  # Last 5 inputs
            "time_span": time.time() - self.memory["recent_inputs"][0]["timestamp"] if self.memory["recent_inputs"] else 0
        }


# Frontolobe processor instance
_frontolobe_instance = None

def get_frontolobe():
    """Get the frontolobe processor instance."""
    global _frontolobe_instance
    if _frontolobe_instance is None:
        _frontolobe_instance = FrontolobeProcessor()
    return _frontolobe_instance


def understand_user_input(user_input, context=None):
    """
    Convenience function to understand user input using the frontolobe.
    
    Args:
        user_input (str): The user's input text
        context (dict): Optional context information
        
    Returns:
        dict: Comprehensive understanding of the input
    """
    processor = get_frontolobe()
    return processor.understand_user_input(user_input, context)


if __name__ == "__main__":
    # Test the frontolobe processor
    processor = get_frontolobe()
    
    # Test cases
    test_inputs = [
        "Can you help me create a video about mountains?",
        "I'm feeling frustrated with this code",
        "What's the weather like today?",
        "Hello! How are you?",
        "I need a solution for this problem as soon as possible"
    ]
    
    print("Testing Frontolobe Processor:")
    print("=" * 50)
    
    for i, test_input in enumerate(test_inputs, 1):
        print(f"\nTest {i}: {test_input}")
        understanding = processor.understand_user_input(test_input)
        
        print(f"Intent: {understanding['intent']['type']} (confidence: {understanding['intent']['confidence']:.2f})")
        print(f"Emotional Tone: {understanding['emotional_tone']['tone']} (confidence: {understanding['emotional_tone']['confidence']:.2f})")
        print(f"Contextual Clues: {understanding['contextual_clues']}")
        print(f"Key Concepts: {understanding['key_concepts']}")
        print(f"Complexity: {understanding['complexity']['level']}")
        print(f"Clarification Needed: {understanding['clarification_needed']}")
        print(f"Response Suggestion: {understanding['response_suggestion']}")
        print("-" * 30)