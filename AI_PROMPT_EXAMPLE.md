# AI Question Generation - Prompt Examples

## Current Prompt Structure

The AI receives a carefully crafted prompt that includes:

1. **Role Definition**: "You are an expert educational content creator"
2. **Task**: Generate X questions of Y difficulty about Z topic
3. **Format Instructions**: Detailed JSON structure requirements
4. **Quality Requirements**: Clear, educational, appropriate difficulty
5. **HTML Formatting**: Instructions for rich text formatting

## Example Prompt (MCQ Question)

Here's what the AI receives when you request:
- Topic: "Python Programming"
- Count: 2
- Difficulty: "medium"
- Type: "mcq"

```
You are an expert educational content creator. Generate 2 medium level mcq questions about "Python Programming".

Difficulty Level: intermediate concepts requiring some knowledge and understanding

Generate Multiple Choice Questions (MCQ) with exactly 4 options each.
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
}

Requirements:
- Questions should be clear, unambiguous, and educational
- Each question should test understanding of "Python Programming"
- Difficulty should match medium level
- Options should be plausible and well-thought-out
- For MCQ: Only one option should be clearly correct
- Avoid trick questions or ambiguous wording
- Use HTML formatting in question text: <p> for paragraphs, <strong> for bold, <em> for italic, <u> for underline
- Assign appropriate marks based on difficulty (easy: 0.5-1.0, medium: 1.0-1.5, hard: 1.5-2.0)

IMPORTANT FORMATTING RULES:
- Question text MUST be in HTML format (wrap in <p> tags)
- Use <strong> for important terms, <em> for emphasis
- Marks should be numbers (0.5, 1.0, 1.5, 2.0, etc.)
- For MCQ: correct_answer is a single number (0-3)

Return ONLY a valid JSON array of question objects. No additional text or markdown formatting.
Generate 2 questions now. Return only the JSON array:
```

## Example AI Response

The AI should return something like:

```json
[
  {
    "question": "<p>What is the <strong>primary purpose</strong> of Python's <em>if</em> statement?</p>",
    "options": ["To define a function", "To make decisions based on conditions", "To loop through data", "To import modules"],
    "correct_answer": 1,
    "marks": 1.0,
    "explanation": "The if statement is used for conditional execution based on boolean expressions"
  },
  {
    "question": "<p>Which method is used to <strong>add an item</strong> to the end of a Python list?</p>",
    "options": ["append()", "add()", "insert()", "push()"],
    "correct_answer": 0,
    "marks": 1.0,
    "explanation": "The append() method adds an item to the end of a list"
  }
]
```

## Format Matching Manual Creation

The AI-generated questions match the exact format used in manual creation:

✅ **Question Text**: HTML formatted (same as rich text editor)
✅ **Options**: Array of strings
✅ **Correct Answer**: Number (MCQ/True-False) or Array (Multiple Select)
✅ **Difficulty**: easy, medium, or hard
✅ **Tags**: Array containing the topic
✅ **Marks**: Decimal number (0.5, 1.0, 1.5, 2.0, etc.)

## Marks Assignment

The system automatically assigns marks based on difficulty:
- **Easy**: 0.5 marks
- **Medium**: 1.0 marks (default)
- **Hard**: 1.5 marks

The AI can also specify custom marks in the response, which will be used if provided.

## Customizing the Prompt

To modify the prompt, edit:
- `backend/api/services/ai_generator_gemini.py` - For Gemini
- `backend/api/services/ai_generator.py` - For OpenAI

The `_build_prompt()` method contains the prompt template.

## Testing the Prompt

You can test what prompt is being sent by adding logging:

```python
import logging
logger = logging.getLogger(__name__)
logger.info(f"Prompt: {prompt}")
```

## Tips for Better Questions

1. **Be specific with topics**: "Python loops" is better than "Python"
2. **Use appropriate difficulty**: Don't ask advanced concepts for "easy"
3. **Clear instructions**: The AI follows your prompt closely
4. **HTML formatting**: The AI will format questions with HTML tags
5. **Marks**: AI can assign marks, or system uses defaults based on difficulty

