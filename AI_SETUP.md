# AI Question Generation Setup

## Overview

The AI question generation feature uses OpenAI's GPT models to automatically generate educational questions based on topics, difficulty levels, and question types.

## Prerequisites

1. **OpenAI API Key**: You need an OpenAI account and API key
   - Sign up at: https://platform.openai.com/
   - Get your API key from: https://platform.openai.com/api-keys

## Setup Instructions

### 1. Get OpenAI API Key

1. Go to https://platform.openai.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (it starts with `sk-...`)

### 2. Configure Environment Variable

Add your OpenAI API key to your `.env` file in the backend directory:

```bash
# Backend .env file
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini  # Optional: defaults to gpt-4o-mini (cheaper)
```

**Recommended Models:**
- `gpt-4o-mini` - Cheapest, good quality (default)
- `gpt-4o` - Better quality, more expensive
- `gpt-3.5-turbo` - Older, cheaper alternative

### 3. Verify Installation

The OpenAI package is already installed. Verify it works:

```bash
cd backend
source ../backend-venv/bin/activate
python -c "import openai; print('OpenAI installed successfully')"
```

### 4. Test the API

Start your Django server and test the generation:

```bash
python manage.py runserver
```

Then use the frontend to generate questions, or test via API:

```bash
curl -X POST http://localhost:8000/api/questions/generate/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Python Programming",
    "count": 3,
    "difficulty": "medium",
    "type": "mcq"
  }'
```

## How It Works

1. **User Input**: User provides topic, count, difficulty, and question type
2. **AI Prompt**: System builds a detailed prompt for the AI
3. **AI Generation**: OpenAI generates questions in JSON format
4. **Validation**: Questions are validated and formatted
5. **Database**: Valid questions are saved to the database
6. **Response**: Generated questions are returned to the frontend

## Fallback Behavior

If the OpenAI API key is not set or there's an error:
- The system automatically falls back to mock/sample questions
- No errors are shown to the user
- The feature continues to work (with sample data)

## Cost Considerations

- **gpt-4o-mini**: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- **gpt-4o**: ~$2.50 per 1M input tokens, ~$10 per 1M output tokens

**Estimated costs per question generation:**
- 5 questions with gpt-4o-mini: ~$0.01-0.02
- 5 questions with gpt-4o: ~$0.05-0.10

## Troubleshooting

### Error: "OPENAI_API_KEY environment variable is not set"

**Solution**: Add `OPENAI_API_KEY` to your `.env` file

### Error: "AI generation failed"

**Possible causes:**
1. Invalid API key
2. Insufficient API credits
3. Network issues
4. Rate limiting

**Solution**: 
- Check your API key is correct
- Verify you have credits in your OpenAI account
- Check your internet connection
- Wait a few minutes and try again (rate limit)

### Questions are not generating

**Solution**: Check Django logs for detailed error messages:
```bash
python manage.py runserver --verbosity 2
```

## Security Notes

⚠️ **Important**: Never commit your API key to version control!

- Keep `.env` in `.gitignore`
- Use environment variables in production
- Rotate API keys regularly
- Monitor API usage in OpenAI dashboard

## Advanced Configuration

### Custom Model Selection

Edit `.env`:
```bash
OPENAI_MODEL=gpt-4o  # Use GPT-4o instead
```

### Adjust Temperature

Edit `api/services/ai_generator.py`:
```python
temperature=0.7,  # Lower = more focused, Higher = more creative
```

### Adjust Token Limits

Edit `api/services/ai_generator.py`:
```python
max_tokens=2000 * count,  # Adjust based on question complexity
```

