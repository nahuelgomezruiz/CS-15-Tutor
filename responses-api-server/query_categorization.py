"""
Query Categorization System for CS 15 Tutor

This module implements the categorization system that:
1. Categorizes student queries into different types
2. Loads appropriate system prompts for each category
3. Handles category-specific response generation
"""

import json
from typing import Dict, List, Optional, Tuple
from enum import Enum
from llmproxy import generate
from utils import _retrieve_rag_context, _format_rag_context

class QueryCategory(Enum):
    """Categories for student queries"""
    HOMEWORK_HELP = "Homework Help"
    EXPLANATION_OF_CONCEPTS = "Explanation of Concepts"
    COURSE_INFORMATION = "Course Information"
    UNRELATED_TO_COURSE = "Unrelated to Course"

class QueryCategorizer:
    """
    System for categorizing student queries and managing category-specific prompts
    """
    
    def __init__(self):
        self.category_prompts = self._load_category_prompts()
        self.quality_checkers = self._load_quality_checkers()
    
    def categorize_query(self, user_query: str) -> QueryCategory:
        """
        Categorize a student query using LLM
        """
        categorization_prompt = f"""
        Categorize this CS 15 student query into exactly one of these categories:
        
        - Homework Help: Questions about implementing assignments, debugging code, or getting help with specific project requirements (CS15 projects are called: Array Lists, Linked Lists, CalcYouLater, MetroSim, Zap, Typewriter, and Gerp)
        - Explanation of Concepts: Questions about understanding data structures, algorithms, C++ concepts, or theoretical topics
        - Course Information: Questions about course logistics, policies, deadlines, or administrative matters
        - Unrelated to Course: Questions that are not related to CS 15 content, programming, or course administration
        
        Student Query: "{user_query}"
        
        Return ONLY the category name, nothing else.
        """
        
        try:
            response = generate(
                model='4o-mini',
                system="You are a query categorizer. Return only the category name.",
                query=categorization_prompt,
                temperature=0.1,  # Low temperature for consistent categorization
                lastk=0,
                rag_usage=False,
            )
            
            if isinstance(response, dict) and 'response' in response:
                print(f"🔍 Categorization response: {response}")
                category_text = response['response'].strip()
            else:
                category_text = str(response).strip()
            
            # Map response to enum
            for category in QueryCategory:
                if category.value.lower() in category_text.lower():
                    return category
            
            # Default to explanation if unclear
            return QueryCategory.EXPLANATION_OF_CONCEPTS
            
        except Exception as e:
            print(f"Error categorizing query: {e}")
            # Default to explanation on error
            return QueryCategory.EXPLANATION_OF_CONCEPTS
    
    def get_system_prompt_for_category(self, category: QueryCategory, base_system_prompt: str = "") -> str:
        """
        Get the appropriate system prompt for a given category
        """
        category_prompt = self.category_prompts.get(category, "")
        return f"{base_system_prompt}\n\n{category_prompt}"
    
    def check_response_quality(self, category: QueryCategory, user_query: str, 
                             assistant_response: str, rag_context: str = "") -> Tuple[bool, str]:
        """
        Check response quality based on category-specific criteria
        Returns: (passes_check, feedback_message)
        """
        if category == QueryCategory.UNRELATED_TO_COURSE:
            return True, "Unrelated query - no quality check needed"
        
        quality_checker = self.quality_checkers.get(category)
        if not quality_checker:
            return True, "No quality checker for this category"
        
        return quality_checker(user_query, assistant_response, rag_context)
    
    def _load_category_prompts(self) -> Dict[QueryCategory, str]:
        """Load category-specific system prompts"""
        return {
            QueryCategory.HOMEWORK_HELP: """
**HOMEWORK HELP MODE - Special Instructions**

You are helping with CS 15 homework assignments. Follow these strict guidelines:

**Academic Integrity Rules:**
- NEVER provide complete code solutions
- NEVER give step-by-step implementation details
- NEVER show exact error messages or debugging output
- NEVER provide pseudocode that directly solves the assignment

**What You CAN Do:**
- Explain concepts and principles
- Suggest debugging approaches and strategies
- Ask leading questions to guide the student
- Reference relevant course materials and specifications
- Explain why certain approaches might work or not work
- Help students understand the problem better

**Response Strategy:**
1. First, understand what the student is trying to accomplish
2. Identify the underlying concept or principle they need to understand
3. Explain the concept clearly and concisely
4. Ask a guiding question that helps them think through the problem
5. Reference relevant course materials if applicable

**Example Approach:**
Instead of: "Here's how to implement a linked list..."
Say: "Linked lists connect nodes through pointers. Think about how you'd traverse from one node to the next. What would you need to store in each node to make this possible?"

**Quality Check Focus:**
- No complete code solutions
- No step-by-step implementation
- Accurate information according to course materials
- Helpful guidance without giving away answers
""",
            
            QueryCategory.EXPLANATION_OF_CONCEPTS: """
**CONCEPT EXPLANATION MODE - Special Instructions**

You are explaining CS 15 concepts and theoretical topics. Focus on clear, educational explanations.

**What You Should Do:**
- Explain concepts clearly and thoroughly
- Use analogies and examples when helpful
- Connect concepts to practical applications
- Reference course materials and specifications
- Help students build deep understanding

**What You Should NOT Do:**
- Provide implementation details for specific projects
- Give step-by-step coding instructions
- Focus on assignment-specific requirements
- Reveal project-specific solutions

**Response Strategy:**
1. Identify the core concept being asked about
2. Provide a clear, concise explanation
3. Use examples or analogies if helpful
4. Connect to broader CS principles
5. Ask a follow-up question to deepen understanding

**Quality Check Focus:**
- No logic mistakes in explanations
- No direct project implementation details
- Clear and accurate concept explanations
- Educational value and depth
""",
            
            QueryCategory.COURSE_INFORMATION: """
**COURSE INFORMATION MODE - Special Instructions**

You are providing information about CS 15 course logistics, policies, and administration.

**What You Should Do:**
- Provide accurate course information when available
- Reference official sources such as the course website, Piazza, homework specifications, or syllabus
- Help with administrative questions
- Clarify course policies and procedures if explicitly covered in provided materials
- Direct students to appropriate resources (course website, Piazza, homework specs, TA, professor) when information is not available

**What You Should NOT Do:**
- Make up information that is not in course documents
- Provide personal opinions about course policies
- Give specific coding or implementation advice
- Reveal confidential course information

**Response Strategy:**
1. Check if the information is available in course materials
2. If yes → provide accurate, factual information and reference the source
3. If no or uncertain → state clearly that you do not have that information and suggest the student check:
   - Course website
   - Piazza
   - Homework specifications
   - A TA or professor
4. Always make the boundary clear: provide what you know, and redirect for what you don’t

"""
        }
    
    def _load_quality_checkers(self) -> Dict[QueryCategory, callable]:
        """Load category-specific quality checkers"""
        return {
            QueryCategory.HOMEWORK_HELP: self._check_homework_help_quality,
            QueryCategory.EXPLANATION_OF_CONCEPTS: self._check_concept_explanation_quality,
            QueryCategory.COURSE_INFORMATION: self._check_course_info_quality
        }
    
    def _check_homework_help_quality(self, user_query: str, assistant_response: str, rag_context: str = "") -> Tuple[bool, str]:
        """Check homework help response quality"""
        quality_prompt = f"""
        Review this CS 15 homework help response for quality issues:
        
        Student Query: "{user_query}"
        Assistant Response: "{assistant_response}"
        Course Context: "{rag_context}"
        
        Focus only on serious problems that violate homework help guidelines. Minor hints, general guidance, or partial explanations should not cause failure.

        Check for these major issues:
        1. Does it include full code solutions or large runnable code blocks? (FAIL if yes)
        2. Does it walk through a complete step-by-step implementation rather than giving hints? (FAIL if yes)
        3. Is any provided information clearly inaccurate or misleading about course content? (FAIL if yes)
        4. Does it give away so much of the final answer that the student could bypass learning? (FAIL if yes)

        
        Return JSON with:
        {{
            "passes_check": (boolean, true if it passes, false if it fails),
            "issues": ["list of specific issues found"],
            "feedback": "specific feedback for improvement, if fails"
        }}
        """

        rag_context = _retrieve_rag_context(user_query, 0.4, 2) # Smaller k for quality checks
        rag_context_formatted = _format_rag_context(rag_context) if rag_context else ""
        
        try:
            response = generate(
                model='4o-mini',
                system="You are a quality checker for CS 15 homework help responses. Return ONLY valid JSON.",
                query=quality_prompt + "\n\n" + rag_context_formatted,
                temperature=0.1,
                lastk=0,
                rag_usage=False,
            )
            
            if isinstance(response, dict) and 'response' in response:
                print(f"🔍 Quality check response: {response}")
                # Success path - parse the response string as JSON
                result = json.loads(response['response'])
            else:
                # Error path - raise exception
                raise RuntimeError(f"Generation failed: {response}")
            
            return result.get('passes_check', True), result.get('feedback', 'No specific feedback')
            
        except Exception as e:
            print(f"Error in homework quality check: {e}")
            return True, "Quality check failed - proceeding with response"
    
    def _check_concept_explanation_quality(self, user_query: str, assistant_response: str, rag_context: str = "") -> Tuple[bool, str]:
        """Check concept explanation response quality"""
        quality_prompt = f"""
        Review this CS 15 concept explanation response for quality issues:
        
        Student Query: "{user_query}"
        Assistant Response: "{assistant_response}"
        Course Context: "{rag_context}"
        
        Check for these issues:
        1. Are there any logic mistakes in the explanation?
        2. Does it contain project-specific implementation details?
        3. Is the concept explained clearly and accurately?
        4. Does it provide educational value?
        5. Is it appropriate for the student's level?
        
        Return JSON with:
        {{
            "passes_check": (boolean, true if it passes, false if it fails),
            "issues": ["list of specific issues found"],
            "feedback": "specific feedback for improvement, if fails"
        }}
        """
        
        try:
            response = generate(
                model='4o-mini',
                system="You are a quality checker for CS 15 concept explanations. Return ONLY valid JSON.",
                query=quality_prompt,
                temperature=0.1,
                lastk=0,
                rag_usage=False,
            )

            if isinstance(response, dict) and 'response' in response:
                # Success path - parse the response string as JSON
                print(f"🔍 Quality check response: {response}")
                result = json.loads(response['response'])
            else:
                # Error path - raise exception
                raise RuntimeError(f"Generation failed: {response}")
            
            return result.get('passes_check', True), result.get('feedback', 'No specific feedback')
            
        except Exception as e:
            print(f"Error in concept explanation quality check: {e}")
            return True, "Quality check failed - proceeding with response"
    
    def _check_course_info_quality(self, user_query: str, assistant_response: str, rag_context: str = "") -> Tuple[bool, str]:
        """Check course information response quality"""
        quality_prompt = f"""
        Review this CS 15 course information response for quality issues:
        
        Student Query: "{user_query}"
        Assistant Response: "{assistant_response}"
        Course Context: "{rag_context}"
        
        ONLY fail if the response contains clearly inaccurate info, misleading guidance, or directly contradicts course materials.  
        Do NOT fail for responses that are generally helpful but could be slightly more detailed.  

        Check for these major issues:
        1. Is any information clearly inaccurate or contradictory to course documents?
        2. Does it invent or speculate about policies not supported by the context?
        3. Does it fail to clarify when information is unavailable (instead of redirecting to resources)?
        
        Return JSON with:
        {{
            "passes_check": (boolean, true if it passes, false if it fails),
            "issues": ["list of specific issues found"],
            "feedback": "specific feedback for improvement, if fails"
        }}
        """
        
        rag_context = _retrieve_rag_context(user_query, 0.4, 2) # Smaller k for quality checks
        rag_context_formatted = _format_rag_context(rag_context) if rag_context else ""
        
        try:
            response = generate(
                model='4o-mini',
                system="You are a quality checker for CS 15 homework help responses. Return ONLY valid JSON.",
                query=quality_prompt + "\n\n" + rag_context_formatted,
                temperature=0.1,
                lastk=0,
                rag_usage=False,
            )
            
            if isinstance(response, dict) and 'response' in response:
                # Success path - parse the response string as JSON
                print(f"🔍 Quality check response: {response}")
                result = json.loads(response['response'])
            else:
                # Error path - raise exception
                raise RuntimeError(f"Generation failed: {response}")
            
            return result.get('passes_check', True), result.get('feedback', 'No specific feedback')
            
        except Exception as e:
            print(f"Error in course info quality check: {e}")
            return True, "Quality check failed - proceeding with response" 