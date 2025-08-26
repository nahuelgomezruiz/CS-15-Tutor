"""
Enhanced Chat Handler with Multi-Stage Processing

This module implements the three-stage system:
1. Query Categorization
2. Category-Specific Response Generation  
3. Quality Checking and Regeneration
"""

import time
import os
from typing import Dict, Any, Optional, Tuple
from query_categorization import QueryCategorizer, QueryCategory
from llmproxy import generate, retrieve
from utils import _retrieve_rag_context, _format_rag_context


class EnhancedChatHandler:
    """
    Enhanced chat handler with categorization and quality checking
    """
    
    def __init__(self):
        self.categorizer = QueryCategorizer()
        self.base_system_prompt = self._load_system_prompt()
        self.max_regeneration_attempts = 3
    
    def process_chat_request(self, message: str, conversation_id: str, 
                           conversation_history: list, conversation_rag_context: list,
                           utln: str, platform: str) -> Dict[str, Any]:
        """
        Process a chat request through the three-stage system
        """
        request_start_time = time.time()
        
        print(f"🤖 Enhanced processing message from {utln} ({platform}): {message}")
        print(f"💬 Conversation ID: {conversation_id}")
        
        # Stage 1: Query Categorization
        print("📋 Stage 1: Categorizing query...")
        category = self.categorizer.categorize_query(message)
        print(f"📋 Query categorized as: {category.value}")
        
        # Handle unrelated queries immediately
        if category == QueryCategory.UNRELATED_TO_COURSE:
            unrelated_response = self._generate_unrelated_response()
            return self._prepare_response(
                unrelated_response, conversation_id, request_start_time,
                category, utln, platform, conversation_rag_context
            )
        
        # Stage 2: RAG Context Retrieval
        print("🔍 Stage 2: Retrieving RAG context...")
        rag_context = _retrieve_rag_context(message, 0.4, 5)
        
        # Stage 3: Response Generation with Quality Checking
        print("🚀 Stage 3: Generating response with quality checking...")
        final_response = self._generate_quality_checked_response(
            message, category, rag_context, conversation_history
        )
        
        # Prepare and return response
        return self._prepare_response(
            final_response, conversation_id, request_start_time,
            category, utln, platform, rag_context  # Pass the current rag_context instead of conversation_rag_context
        )
    
    def _generate_quality_checked_response(self, message: str, category: QueryCategory, 
                                         rag_context: list, conversation_history: list) -> str:
        """Generate response with quality checking and regeneration"""
        
        rag_context_formatted = _format_rag_context(rag_context) if rag_context else ""

    # Generate the first response (initial attempt)
        response = self._generate_response(message, category, rag_context_formatted, conversation_history)
        print(f"\n\nInitial response: {response}\n")

        # Each time it will improve on the enhanced response
        for attempt in range(self.max_regeneration_attempts):
            print(f"🔄 Generation attempt {attempt + 1}/{self.max_regeneration_attempts}")

            # Run quality check
            passes_check, feedback = self.categorizer.check_response_quality(
                category, message, response, rag_context_formatted
            )
            
            if passes_check:
                print(f"✅ Quality check passed on attempt {attempt + 1}")
                return response
            else:
                print(f"❌ Quality check failed on attempt {attempt + 1}: {feedback}")
                
                if attempt < self.max_regeneration_attempts - 1:
                    # Regenerate with feedback
                    enhanced_message = self._enhance_response_with_feedback(response, feedback, category)
                    print(f"🔄 Regenerating with enhanced instructions...")
                    print(f"\n\nEnhanced message: {enhanced_message}\n")
                    
                    response = self._generate_response(enhanced_message, category, rag_context_formatted, conversation_history)
                    print(f"\n\nEnhanced response: {response}\n")
                else:
                    # Last resort
                    print(f"⚠️ Using response despite quality issues (final attempt)")
                    return response
        
        return "I apologize, but I'm having trouble generating an appropriate response. Please try rephrasing your question."
    
    def _load_system_prompt(self) -> str:
        """Load the base system prompt from system_prompt.txt"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            prompt_file_path = os.path.join(current_dir, 'system_prompt.txt')
            
            with open(prompt_file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
                
        except FileNotFoundError:
            print(f"⚠️ Warning: system_prompt.txt not found, using default prompt")
            return "You are a friendly and brief Teaching Assistant (TA) for CS 15: Data Structures at Tufts University."
        except IOError as e:
            print(f"⚠️ Warning: Error reading system_prompt.txt: {e}, using default prompt")
            return "You are a friendly and brief Teaching Assistant (TA) for CS 15: Data Structures at Tufts University."
    
    def _generate_response(self, message: str, category: QueryCategory,
                          rag_context: list, conversation_history: list) -> str:
        """Generate a response for the given category"""
        
        # Get category-specific system prompt
        system_prompt = self.categorizer.get_system_prompt_for_category(
            category, self.base_system_prompt
        )
        
        # Calculate conversation history context
        num_previous_pairs = (len(conversation_history) - 1) // 2 if conversation_history else 0
        
        query_with_rag_context = "student query: " + message + "\n\n" + rag_context

        try:
            response = generate(
                model='4o-mini',
                system=system_prompt,
                query=query_with_rag_context,
                temperature=0.7,
                lastk=num_previous_pairs,
                rag_usage=False,
            )
            
            if isinstance(response, dict) and 'response' in response:
                return response['response']
            else:
                return str(response)
                
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            return "I apologize, but I encountered an error while generating a response. Please try again."
    
    def _enhance_response_with_feedback(self, original_response: str, feedback: str, category: QueryCategory) -> str:
        """Enhance the original message with quality check feedback"""
        
        enhancement_prompt = f"""
        The following assistant response to a CS 15 student query failed quality checks:
    
        Original Response: "{original_response}"
        Category: {category.value}
        Quality Feedback: "{feedback}"
        
        Please rewrite the assistant's response so that it addresses the student's query appropriately,
        incorporates the feedback, and avoids the listed issues.
        
        Return only the improved response, nothing else.
        """
        
        return enhancement_prompt

        # try:
        #     response = generate(
        #         model='4o-mini',
        #         system="You are a query enhancer. Return only the enhanced query.",
        #         query=enhancement_prompt,
        #         temperature=0.3,
        #         lastk=2,
        #         rag_usage=False,
        #     )
            
        #     if isinstance(response, dict) and 'response' in response:
        #         return response['response'].strip()
        #     else:
        #         return str(response).strip()
                
        # except Exception as e:
        #     print(f"❌ Error enhancing message: {e}")
        #     return original_message
    
    def _generate_unrelated_response(self) -> str:
        """Generate response for unrelated queries"""
        return """I can only help with questions related to CS 15: Data Structures. This includes C++ programming, data structures, algorithms, course logistics, and CS 15 projects. Please feel free to ask any CS 15 related questions!"""
    
    def _prepare_response(self, assistant_response: str, conversation_id: str, 
                         request_start_time: float, category: QueryCategory,
                         utln: str, platform: str, rag_context: list) -> Dict[str, Any]:
        """Prepare the final response with metadata"""
        
        response_time_ms = int((time.time() - request_start_time) * 1000)
        
        # Format RAG context for logging
        formatted_rag_context = ""
        if rag_context:
            formatted_rag_context = _format_rag_context(rag_context)
        
        print(f"📄 Generated response length: {len(assistant_response)}")
        print(f"⏱️ Total request time: {response_time_ms}ms")
        print(f"🏷️ Query category: {category.value}")

        
        return {
            "response": assistant_response,
            "rag_context": formatted_rag_context,
            "conversation_id": conversation_id,
            "category": category.value,
            "response_time_ms": response_time_ms,
            "enhanced_metadata": {
                "query_category": category.value,
                "processing_stages": ["categorization", "rag_retrieval", "quality_checked_generation"],
                "quality_checks_performed": True,
                "rag_context_used": bool(formatted_rag_context)
            }
        }

# Example usage function
def example_enhanced_processing():
    """Example of how to use the enhanced chat handler"""
    
    handler = EnhancedChatHandler()
    
    # Example queries for different categories
    test_queries = [
        "How do I implement a linked list in C++?",  # Homework Help
        "What is the difference between a stack and a queue?",  # Explanation of Concepts
        "When is the MetroSim project due?",  # Course Information
        "What's the weather like today?"  # Unrelated to Course
    ]
    
    conversation_history = [
        {"role": "system", "content": "You are a CS 15 tutor."}
    ]
    conversation_rag_context = []
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing query: {query}")
        print(f"{'='*60}")
        
        try:
            result = handler.process_chat_request(
                message=query,
                conversation_id="test_conversation",
                conversation_history=conversation_history,
                conversation_rag_context=conversation_rag_context,
                utln="testuser",
                platform="web"
            )
            
            print(f"Category: {result['category']}")
            print(f"Response: {result['response'][:200]}...")
            print(f"Processing time: {result['response_time_ms']}ms")
            print(f"Enhanced metadata: {result['enhanced_metadata']}")
            
        except Exception as e:
            print(f"Error processing query: {e}")

if __name__ == "__main__":
    example_enhanced_processing() 