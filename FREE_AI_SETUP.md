# Free AI Question Generation Setup

## 🆓 Free AI Options

We now support **Google Gemini** which offers a **completely free tier** with no credit card required!

### Option 1: Google Gemini (Recommended - FREE)

**Advantages:**
- ✅ Completely free (no credit card needed)
- ✅ Generous free tier (60 requests per minute)
- ✅ Good quality question generation
- ✅ Easy to set up

**Setup Steps:**

1. **Get Free API Key:**
   - Go to: https://makersuite.google.com/app/apikey
   - Sign in with your Google account
   - Click "Create API Key"
   - Copy your API key

2. **Add to .env file:**
   ```bash
   # In backend/.env
   GEMINI_API_KEY=your-gemini-api-key-here
   ```

3. **Install package (already done):**
   ```bash
   pip install google-generativeai
   ```

4. **That's it!** The system will automatically use Gemini if the key is set.

### Option 2: OpenAI GPT (paid)

- Uses the Chat Completions API (`openai` Python package).
- Set in `.env`:
  ```bash
  OPENAI_API_KEY=sk-...
  OPENAI_MODEL=gpt-4o-mini   # optional; default gpt-4o-mini. Try gpt-4o for higher quality.
  # Optional: Azure or custom gateway
  # OPENAI_BASE_URL=https://...
  ```
- **Prefer OpenAI first** (before Groq/Gemini):
  ```bash
  QUESTION_AI_PROVIDERS=openai,groq,gemini
  ```
- **OpenAI only** (skip other providers):
  ```bash
  QUESTION_AI_PROVIDERS=openai
  ```

### How It Works

Provider order is controlled by **`QUESTION_AI_PROVIDERS`** (comma-separated: `groq`, `gemini`, `openai`).  
Default if unset: `openai,groq,gemini` (GPT first, then Groq, then Gemini).

For each name in order, the backend uses that provider **only if** its API key is configured and generation returns questions; otherwise it tries the next.

4. **Mock/Sample** questions if no provider succeeds.

When you run the backend, the server console will print which provider was used, e.g.:
- `[EasyTest AI] Generated 5 questions using Groq for topic: ...`
- `[EasyTest AI] Generated 5 questions using OpenAI for topic: ...`
- `[EasyTest AI] No API key configured. Using sample questions...`

### Get Your Free Gemini API Key

1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with Google
3. Click "Create API Key"
4. Copy the key
5. Add to `backend/.env`:
   ```
   GEMINI_API_KEY=your-key-here
   ```

### Free Tier Limits

**Google Gemini:**
- 60 requests per minute
- 1,500 requests per day
- Completely free, no credit card needed

This is more than enough for generating questions!

### Testing

After adding your Gemini API key, restart your Django server and try generating questions. You should see real AI-generated questions instead of sample ones.

### Troubleshooting

**Error: "GEMINI_API_KEY not set"**
- Make sure you added the key to `.env` file
- Restart Django server after adding

**Error: "google-generativeai not installed"**
- Run: `pip install google-generativeai`

**Still getting sample questions?**
- Check Django logs for error messages
- Verify API key is correct
- Make sure you restarted the server

