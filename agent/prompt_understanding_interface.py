"""
Prompt Understanding Interface for Hemomemo AI
Integrates 20M parameter system for understanding user prompts
"""

import sys
import os
sys.path.append('..')

from model.prompt_understanding import PromptUnderstandingSystem
from typing import Dict, List, Optional


class PromptUnderstandingInterface:
    """
    Interface for prompt understanding system
    Provides easy-to-use methods for understanding user prompts
    """
    
    def __init__(self):
        self.understanding_system = PromptUnderstandingSystem()
        
    def understand(self, prompt: str) -> Dict:
        """
        Understand user prompt
        Returns detailed understanding including intent, context, and confidence
        """
        return self.understanding_system.understand_prompt(prompt)
    
    def get_intent(self, prompt: str) -> str:
        """
        Get the primary intent of the prompt
        """
        understanding = self.understand(prompt)
        return understanding['intent']
    
    def get_confidence(self, prompt: str) -> float:
        """
        Get confidence score for prompt understanding
        """
        understanding = self.understand(prompt)
        return understanding['confidence']
    
    def get_entities(self, prompt: str) -> List[str]:
        """
        Extract entities from the prompt
        """
        understanding = self.understand(prompt)
        return understanding['entities']
    
    def get_context(self, prompt: str) -> Dict:
        """
        Get context information for the prompt
        """
        understanding = self.understand(prompt)
        return understanding['context']
    
    def classify_for_domain_routing(self, prompt: str) -> str:
        """
        Classify prompt for domain-specific routing
        Returns the appropriate domain for processing
        """
        intent = self.get_intent(prompt)
        
        # Map intents to domains
        domain_mapping = {
            'social': 'social',
            'identity': 'identity',
            'memory': 'memory',
            'math': 'math',
            'code': 'code',
            'hadith': 'hadith',
            'quran': 'quran',
            'ilm': 'ilm',
            'general': 'general'
        }
        
        return domain_mapping.get(intent, 'general')
    
    def get_conversation_summary(self) -> Dict:
        """
        Get summary of conversation history
        """
        return self.understanding_system.get_conversation_summary()
    
    def analyze_query_complexity(self, prompt: str) -> Dict:
        """
        Analyze query complexity and requirements
        """
        understanding = self.understand(prompt)
        
        # Calculate complexity based on various factors
        word_count = len(prompt.split())
        entity_count = len(understanding['entities'])
        intent = understanding['intent']
        confidence = understanding['confidence']
        
        # Determine complexity level
        complexity_score = word_count * 0.1 + entity_count * 0.5
        
        if complexity_score < 3:
            complexity_level = 'simple'
        elif complexity_score < 7:
            complexity_level = 'moderate'
        else:
            complexity_level = 'complex'
        
        return {
            'complexity_level': complexity_level,
            'complexity_score': complexity_score,
            'word_count': word_count,
            'entity_count': entity_count,
            'intent': intent,
            'confidence': confidence,
            'requires_external_data': intent in ['web-search', 'deep-research'],
            'requires_code_execution': intent == 'code',
            'requires_math_calculation': intent == 'math'
        }
    
    def get_understanding_report(self, prompt: str) -> str:
        """
        Generate a detailed understanding report
        """
        understanding = self.understand(prompt)
        complexity = self.analyze_query_complexity(prompt)
        
        report = f"""
PROMPT UNDERSTANDING REPORT
===========================

Original Prompt: "{prompt}"

Intent Analysis:
- Primary Intent: {understanding['intent']}
- Confidence Score: {understanding['confidence']:.2f}
- Entities Found: {', '.join(understanding['entities']) if understanding['entities'] else 'None'}

Complexity Analysis:
- Complexity Level: {complexity['complexity_level']}
- Complexity Score: {complexity['complexity_score']:.2f}
- Word Count: {complexity['word_count']}
- Entity Count: {complexity['entity_count']}

Context Information:
- Conversation History: {understanding['context']['conversation_history']} interactions
- Previous Context: {understanding['context']['previous_intent'] if understanding['context']['previous_intent'] else 'None'}

Processing Requirements:
- Requires External Data: {'Yes' if complexity['requires_external_data'] else 'No'}
- Requires Code Execution: {'Yes' if complexity['requires_code_execution'] else 'No'}
- Requires Math Calculation: {'Yes' if complexity['requires_math_calculation'] else 'No'}

Domain Routing:
- Recommended Domain: {self.classify_for_domain_routing(prompt)}

Timestamp: {understanding['timestamp']}
"""
        return report


# Example usage
if __name__ == "__main__":
    # Initialize interface
    interface = PromptUnderstandingInterface()
    
    # Test prompts
    test_prompts = [
        "hello how are you today",
        "write a python function to calculate fibonacci",
        "what is the capital of france",
        "explain the concept of machine learning",
        "tell me about the life of prophet muhammad"
    ]
    
    # Test understanding
    for prompt in test_prompts:
        print(f"\n{'='*60}")
        print(f"Testing prompt: {prompt}")
        print(f"{'='*60}")
        
        # Get basic understanding
        intent = interface.get_intent(prompt)
        confidence = interface.get_confidence(prompt)
        entities = interface.get_entities(prompt)
        
        print(f"Intent: {intent}")
        print(f"Confidence: {confidence:.2f}")
        print(f"Entities: {entities}")
        
        # Get complexity analysis
        complexity = interface.analyze_query_complexity(prompt)
        print(f"Complexity: {complexity['complexity_level']} ({complexity['complexity_score']:.2f})")
        
        # Get domain routing
        domain = interface.classify_for_domain_routing(prompt)
        print(f"Domain: {domain}")
        
        # Generate report
        report = interface.get_understanding_report(prompt)
        print(f"\n{report}")