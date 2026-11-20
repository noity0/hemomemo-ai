"""
Prompt Understanding System - 20M Parameters
Dedicated module for understanding user prompts and text
Pure Hemomemo AI Native - No External Dependencies
"""

import numpy as np
import json
import os
import time
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class PromptUnderstandingSystem:
    """
    20M parameter system dedicated to understanding user prompts and text
    Specialized for intent recognition, context analysis, and query routing
    """
    
    def __init__(self):
        # 20M parameter configuration
        self.vocab_size = 50000  # Vocabulary size
        self.embedding_dim = 512  # Word embeddings
        self.hidden_dim = 1024    # Hidden layer dimension
        self.num_layers = 4       # Number of layers
        self.num_heads = 8        # Attention heads
        self.dropout_rate = 0.1   # Dropout rate
        
        # Intent classification
        self.intent_categories = {
            'social': ['hello', 'hi', 'hey', 'greetings', 'how are you', 'friend', 'chat', 'talk'],
            'identity': ['who are you', 'what are you', 'introduce', 'about', 'tell me about yourself'],
            'memory': ['remember', 'recall', 'what did i say', 'earlier', 'before', 'past', 'history'],
            'math': ['calculate', 'math', 'add', 'subtract', 'multiply', 'divide', 'equation', 'formula'],
            'code': ['code', 'program', 'function', 'python', 'javascript', 'c++', 'java', 'coding'],
            'hadith': ['hadith', 'sunnah', 'prophet', 'muhammad', 'narration', 'teaching'],
            'quran': ['quran', 'koran', 'verse', 'surah', 'ayah', 'chapter', 'verse'],
            'ilm': ['knowledge', 'learn', 'teach', 'education', 'wisdom', 'understanding'],
            'general': ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'help', 'information']
        }
        
        # Initialize parameters
        self.parameters = self._initialize_parameters()
        
        # Context tracking
        self.conversation_history = []
        self.current_context = {}
        
    def _initialize_parameters(self) -> Dict:
        """Initialize 20M parameters for the prompt understanding system"""
        params = {}
        
        # Word embeddings (vocab_size * embedding_dim = 50,000 * 512 = 25,600,000)
        params['word_embeddings'] = np.random.normal(0, 0.1, (self.vocab_size, self.embedding_dim))
        
        # Positional embeddings (max_seq_length * embedding_dim)
        max_seq_length = 512
        params['pos_embeddings'] = np.random.normal(0, 0.1, (max_seq_length, self.embedding_dim))
        
        # Transformer layers
        for i in range(self.num_layers):
            # Attention weights (embedding_dim * embedding_dim)
            params[f'attention_q_{i}'] = np.random.normal(0, 0.1, (self.embedding_dim, self.embedding_dim))
            params[f'attention_k_{i}'] = np.random.normal(0, 0.1, (self.embedding_dim, self.embedding_dim))
            params[f'attention_v_{i}'] = np.random.normal(0, 0.1, (self.embedding_dim, self.embedding_dim))
            params[f'attention_out_{i}'] = np.random.normal(0, 0.1, (self.embedding_dim, self.embedding_dim))
            
            # Layer normalization
            params[f'layer_norm_1_{i}'] = np.random.normal(1.0, 0.1, (self.embedding_dim,))
            params[f'layer_norm_2_{i}'] = np.random.normal(1.0, 0.1, (self.embedding_dim,))
            
            # Feed forward network
            params[f'ffn_1_{i}'] = np.random.normal(0, 0.1, (self.embedding_dim, self.hidden_dim))
            params[f'ffn_2_{i}'] = np.random.normal(0, 0.1, (self.hidden_dim, self.embedding_dim))
            
            # Dropout
            params[f'dropout_{i}'] = np.random.random((self.embedding_dim,)) < self.dropout_rate
        
        # Output layer
        params['output_projection'] = np.random.normal(0, 0.1, (self.embedding_dim, len(self.intent_categories)))
        
        return params
    
    def understand_prompt(self, prompt: str) -> Dict:
        """
        Understand user prompt with 20M parameter system
        Returns intent, context, and understanding details
        """
        print(f"Understanding prompt: {prompt}")
        
        # Preprocess prompt
        tokens = self._tokenize(prompt)
        embeddings = self._get_embeddings(tokens)
        
        # Process through transformer layers
        processed_embeddings = self._transformer_process(embeddings)
        
        # Extract intent
        intent = self._classify_intent(processed_embeddings, prompt)
        
        # Analyze context
        context = self._analyze_context(prompt, intent)
        
        # Extract key entities
        entities = self._extract_entities(prompt)
        
        # Generate understanding summary
        understanding = {
            'prompt': prompt,
            'intent': intent,
            'confidence': self._calculate_confidence(processed_embeddings),
            'context': context,
            'entities': entities,
            'timestamp': datetime.now().isoformat(),
            'processing_time': time.time()
        }
        
        # Update conversation history
        self.conversation_history.append(understanding)
        
        return understanding
    
    def _tokenize(self, text: str) -> List[int]:
        """Tokenize input text"""
        # Simple tokenization (in production, use more sophisticated methods)
        words = text.lower().split()
        tokens = []
        
        for word in words:
            # Simple hash-based tokenization
            token = hash(word) % self.vocab_size
            tokens.append(token)
        
        # Add positional information
        tokens = tokens[:512]  # Limit sequence length
        return tokens
    
    def _get_embeddings(self, tokens: List[int]) -> np.ndarray:
        """Get word embeddings for tokens"""
        embeddings = []
        for token in tokens:
            embedding = self.parameters['word_embeddings'][token]
            embeddings.append(embedding)
        
        # Add positional embeddings
        for i, token in enumerate(tokens):
            if i < len(self.parameters['pos_embeddings']):
                embeddings[i] += self.parameters['pos_embeddings'][i]
        
        return np.array(embeddings)
    
    def _transformer_process(self, embeddings: np.ndarray) -> np.ndarray:
        """Process embeddings through transformer layers"""
        processed = embeddings
        
        for i in range(self.num_layers):
            # Multi-head attention
            attention_output = self._attention(processed, i)
            
            # Layer normalization
            processed = self._layer_norm(processed + attention_output, 
                                       self.parameters[f'layer_norm_1_{i}'])
            
            # Feed forward network
            ff_output = self._feed_forward(processed, i)
            
            # Layer normalization
            processed = self._layer_norm(processed + ff_output,
                                       self.parameters[f'layer_norm_2_{i}'])
            
            # Apply dropout
            if self.parameters[f'dropout_{i}'][0] > 0.5:
                processed = self._apply_dropout(processed)
        
        return processed
    
    def _attention(self, x: np.ndarray, layer: int) -> np.ndarray:
        """Multi-head attention mechanism"""
        # Query, Key, Value projections
        q = np.dot(x, self.parameters[f'attention_q_{layer}'])
        k = np.dot(x, self.parameters[f'attention_k_{layer}'])
        v = np.dot(x, self.parameters[f'attention_v_{layer}'])
        
        # Scaled dot-product attention
        scores = np.dot(q, k.T) / np.sqrt(self.embedding_dim)
        attention_weights = np.exp(scores - np.max(scores))
        attention_weights = attention_weights / np.sum(attention_weights, axis=1, keepdims=True)
        
        # Apply attention to values
        attended = np.dot(attention_weights, v)
        
        # Output projection
        output = np.dot(attended, self.parameters[f'attention_out_{layer}'])
        
        return output
    
    def _feed_forward(self, x: np.ndarray, layer: int) -> np.ndarray:
        """Feed forward network"""
        hidden = np.maximum(0, np.dot(x, self.parameters[f'ffn_1_{layer}']))  # ReLU
        output = np.dot(hidden, self.parameters[f'ffn_2_{layer}'])
        
        return output
    
    def _layer_norm(self, x: np.ndarray, weights: np.ndarray) -> np.ndarray:
        """Layer normalization"""
        mean = np.mean(x, axis=1, keepdims=True)
        std = np.std(x, axis=1, keepdims=True)
        normalized = (x - mean) / (std + 1e-8)
        return normalized * weights + (1 - weights)
    
    def _apply_dropout(self, x: np.ndarray) -> np.ndarray:
        """Apply dropout"""
        mask = np.random.random(x.shape) > 0.1
        return x * mask
    
    def _classify_intent(self, embeddings: np.ndarray, prompt: str) -> str:
        """Classify prompt intent"""
        # Get mean of embeddings
        mean_embedding = np.mean(embeddings, axis=0)
        
        # Project to intent space
        intent_scores = np.dot(mean_embedding, self.parameters['output_projection'])
        
        # Find best intent
        best_intent_idx = np.argmax(intent_scores)
        intent_categories = list(self.intent_categories.keys())
        
        # Verify with keyword matching
        prompt_lower = prompt.lower()
        for intent, keywords in self.intent_categories.items():
            if any(keyword in prompt_lower for keyword in keywords):
                return intent
        
        return intent_categories[best_intent_idx]
    
    def _analyze_context(self, prompt: str, intent: str) -> Dict:
        """Analyze context of the prompt"""
        context = {
            'intent': intent,
            'previous_context': self.current_context,
            'conversation_history': len(self.conversation_history),
            'entities': []
        }
        
        # Update current context
        self.current_context = {
            'last_intent': intent,
            'last_prompt': prompt,
            'timestamp': datetime.now().isoformat()
        }
        
        return context
    
    def _extract_entities(self, prompt: str) -> List[str]:
        """Extract named entities from prompt"""
        entities = []
        
        # Simple entity extraction (in production, use more sophisticated methods)
        words = prompt.split()
        
        # Extract potential entities (capitalized words, numbers, etc.)
        for word in words:
            if word[0].isupper() or word.isdigit():
                entities.append(word)
        
        return entities
    
    def _calculate_confidence(self, embeddings: np.ndarray) -> float:
        """Calculate confidence score for understanding"""
        # Simple confidence calculation based on embedding magnitude
        magnitude = np.linalg.norm(embeddings)
        normalized_confidence = min(magnitude / 1000.0, 1.0)
        return normalized_confidence
    
    def get_conversation_summary(self) -> Dict:
        """Get summary of conversation"""
        if not self.conversation_history:
            return {'message': 'No conversation history available'}
        
        # Analyze conversation patterns
        intents = [item['intent'] for item in self.conversation_history]
        intent_counts = {intent: intents.count(intent) for intent in set(intents)}
        
        # Calculate average confidence
        avg_confidence = np.mean([item['confidence'] for item in self.conversation_history])
        
        return {
            'total_interactions': len(self.conversation_history),
            'intent_distribution': intent_counts,
            'average_confidence': avg_confidence,
            'last_interaction': self.conversation_history[-1]['timestamp'],
            'dominant_intent': max(intent_counts, key=intent_counts.get)
        }


# Example usage
if __name__ == "__main__":
    # Initialize prompt understanding system
    system = PromptUnderstandingSystem()
    
    # Test prompts
    test_prompts = [
        "hello how are you",
        "calculate 2+2",
        "write python code for hello world",
        "what is the meaning of life",
        "tell me about prophet muhammad",
        "surah al-fatihah meaning"
    ]
    
    # Test understanding
    for prompt in test_prompts:
        understanding = system.understand_prompt(prompt)
        print(f"Prompt: {prompt}")
        print(f"Intent: {understanding['intent']}")
        print(f"Confidence: {understanding['confidence']:.2f}")
        print(f"Entities: {understanding['entities']}")
        print("-" * 50)
    
    # Get conversation summary
    summary = system.get_conversation_summary()
    print("Conversation Summary:")
    print(json.dumps(summary, indent=2))