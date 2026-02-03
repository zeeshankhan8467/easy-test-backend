"""
AI Question Generator Service using Google Gemini (Free Tier)
Google Gemini offers a generous free tier with no credit card required
"""
import json
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class GeminiQuestionGenerator:
    def __init__(self):
        if not GEMINI_AVAILABLE:
            raise ValueError("google-generativeai package not installed. Run: pip install google-generativeai")
        
        api_key = os.getenv('GEMINI_API_KEY', '')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set. Get free key from: https://makersuite.google.com/app/apikey")
        
        genai.configure(api_key=api_key)
        # Try to find an available model
        try:
            # List available models and find one that supports generateContent
            available_models = list(genai.list_models())
            model_name = None
            for model in available_models:
                if 'generateContent' in model.supported_generation_methods:
                    # Prefer newer models
                    if 'gemini' in model.name.lower():
                        model_name = model.name.split('/')[-1]  # Get just the model name
                        break
            
            if not model_name:
                # Fallback to common model names
                model_name = 'gemini-pro'
            
            self.model = genai.GenerativeModel(model_name)
            self.model_name = model_name
        except Exception:
            # Fallback to default
            self.model = genai.GenerativeModel('gemini-pro')
            self.model_name = 'gemini-pro'
    
    def _build_prompt(self, topic: str, count: int, difficulty: str, qtype: str) -> str:
        """Build a prompt for AI question generation"""
        
        difficulty_description = {
            'easy': 'basic concepts that a beginner would understand',
            'medium': 'intermediate concepts requiring some knowledge and understanding',
            'hard': 'advanced concepts requiring deep understanding and critical thinking'
        }
        
        question_type_instructions = {
            'mcq': """Generate Multiple Choice Questions (MCQ) with exactly 4 options each.
            Format each question as JSON with:
            - "question": The question text in HTML format (use <p>, <strong>, <em>, <u> tags for formatting)
            - "options": Array of exactly 4 options [option1, option2, option3, option4]
            - "correct_answer": Index of correct answer (0-3)
            - "marks": Number (default 1.0, can be 0.5, 1.0, 1.5, 2.0, etc.)
            - "explanation": Brief explanation of why the answer is correct
            
            Example question format:
            {
              "question": "<p>What is the <strong>primary purpose</strong> of Python's <em>if</em> statement?</p>",
              "options": ["To define a function", "To make decisions based on conditions", "To loop through data", "To import modules"],
              "correct_answer": 1,
              "marks": 1.0,
              "explanation": "The if statement is used for conditional execution"
            }""",
            
            'true_false': """Generate True/False questions.
            Format each question as JSON with:
            - "question": The question text in HTML format (use <p>, <strong>, <em>, <u> tags)
            - "options": ["True", "False"]
            - "correct_answer": 0 for True, 1 for False
            - "marks": Number (default 1.0)
            - "explanation": Brief explanation
            
            Example:
            {
              "question": "<p>Python is a <strong>compiled</strong> programming language.</p>",
              "options": ["True", "False"],
              "correct_answer": 1,
              "marks": 1.0,
              "explanation": "Python is an interpreted language, not compiled"
            }""",
            
            'multiple_select': """Generate Multiple Select questions where more than one answer can be correct.
            Format each question as JSON with:
            - "question": The question text in HTML format (use <p>, <strong>, <em>, <u> tags)
            - "options": Array of 4-5 options
            - "correct_answer": Array of indices of correct answers (e.g., [0, 2])
            - "marks": Number (default 1.0)
            - "explanation": Brief explanation
            
            Example:
            {
              "question": "<p>Which of the following are <strong>Python data types</strong>?</p>",
              "options": ["list", "dictionary", "array", "tuple", "set"],
              "correct_answer": [0, 1, 3, 4],
              "marks": 2.0,
              "explanation": "list, dictionary, tuple, and set are all Python data types"
            }"""
        }
        
        prompt = f"""You are an expert educational content creator. Generate {count} {difficulty} level {qtype} questions about "{topic}".

Difficulty Level: {difficulty_description.get(difficulty, difficulty_description['medium'])}

{question_type_instructions.get(qtype, question_type_instructions['mcq'])}

Requirements:
- Questions should be clear, unambiguous, and educational
- Each question should test understanding of "{topic}"
- Difficulty should match {difficulty} level
- Options should be plausible and well-thought-out
- For MCQ: Only one option should be clearly correct
- For Multiple Select: Clearly indicate which options are correct
- Avoid trick questions or ambiguous wording
- Use HTML formatting in question text: <p> for paragraphs, <strong> for bold, <em> for italic, <u> for underline
- Assign appropriate marks based on difficulty (easy: 0.5-1.0, medium: 1.0-1.5, hard: 1.5-2.0)

IMPORTANT FORMATTING RULES:
- Question text MUST be in HTML format (wrap in <p> tags)
- Use <strong> for important terms, <em> for emphasis
- Marks should be numbers (0.5, 1.0, 1.5, 2.0, etc.)
- For MCQ: correct_answer is a single number (0-3)
- For True/False: correct_answer is 0 (True) or 1 (False)
- For Multiple Select: correct_answer is an array like [0, 2]

Return ONLY a valid JSON array of question objects. No additional text or markdown formatting.
Generate {count} questions now. Return only the JSON array:"""
        
        return prompt
    
    def generate_questions(self, topic: str, count: int, difficulty: str, qtype: str) -> List[Dict[str, Any]]:
        """
        Generate questions using Google Gemini
        
        Args:
            topic: The topic/subject for questions
            count: Number of questions to generate
            difficulty: easy, medium, or hard
            qtype: mcq, true_false, or multiple_select
            
        Returns:
            List of question dictionaries with: question, options, correct_answer, explanation
        """
        try:
            prompt = self._build_prompt(topic, count, difficulty, qtype)
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 2000 * count,
                }
            )
            
            content = response.text.strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            # Parse JSON response
            try:
                parsed = json.loads(content)
                
                # Handle different response formats
                if isinstance(parsed, list):
                    questions = parsed
                elif isinstance(parsed, dict):
                    if 'questions' in parsed:
                        questions = parsed['questions']
                    elif 'question' in parsed:
                        questions = [parsed]
                    else:
                        questions = [parsed]
                else:
                    raise ValueError("Unexpected response format")
                    
            except json.JSONDecodeError:
                # Fallback: try to extract JSON array from text
                import re
                json_match = re.search(r'\[[\s\S]*\]', content)
                if json_match:
                    try:
                        questions = json.loads(json_match.group())
                    except:
                        raise ValueError(f"Could not parse extracted JSON: {content[:200]}")
                else:
                    raise ValueError(f"Could not parse AI response as JSON: {content[:200]}")
            
            # Validate and format questions
            formatted_questions = []
            for q in questions[:count]:  # Limit to requested count
                if not isinstance(q, dict):
                    continue
                    
                question_text = q.get('question', '').strip()
                options = q.get('options', [])
                correct_answer = q.get('correct_answer')
                explanation = q.get('explanation', '')
                
                if not question_text or not options:
                    continue
                
                # Ensure options is a list
                if not isinstance(options, list):
                    continue
                
                # Ensure correct_answer format matches question type
                if qtype == 'multiple_select':
                    if not isinstance(correct_answer, list):
                        correct_answer = [correct_answer] if correct_answer is not None else []
                elif qtype in ['mcq', 'true_false']:
                    if isinstance(correct_answer, list):
                        correct_answer = correct_answer[0] if correct_answer else 0
                    correct_answer = int(correct_answer) if correct_answer is not None else 0
                
                # Get marks from AI response or assign based on difficulty
                marks = q.get('marks', 1.0)
                if isinstance(marks, str):
                    try:
                        marks = float(marks)
                    except:
                        marks = 1.0
                elif not isinstance(marks, (int, float)):
                    marks = 1.0
                
                # Adjust marks based on difficulty if not specified
                if marks == 1.0:  # Default, adjust by difficulty
                    if difficulty == 'easy':
                        marks = 0.5
                    elif difficulty == 'medium':
                        marks = 1.0
                    else:  # hard
                        marks = 1.5
                
                formatted_questions.append({
                    'text': question_text,
                    'options': options,
                    'correct_answer': correct_answer,
                    'explanation': explanation,
                    'difficulty': difficulty,
                    'tags': [topic],
                    'marks': float(marks)
                })
            
            return formatted_questions
            
        except Exception as e:
            raise Exception(f"AI generation failed: {str(e)}")
    
    def generate_questions_safe(self, topic: str, count: int, difficulty: str, qtype: str) -> List[Dict[str, Any]]:
        """
        Safe wrapper that falls back to empty list if AI fails
        """
        try:
            return self.generate_questions(topic, count, difficulty, qtype)
        except Exception as e:
            # Log error but don't crash - return empty list
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Gemini AI generation error: {str(e)}")
            return []

