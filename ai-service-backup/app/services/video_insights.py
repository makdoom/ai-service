import logging
import json
from app.core.config import settings
from app.core.clients import get_genai_client

logger = logging.getLogger(__name__)

async def generate_video_insights(transcript: str):
    """
    Generates a detailed summary and a list of starter questions for a video.
    """
    logger.info("🧠 Generating Video Insights (Summary & Questions)...")
    
    if not transcript or len(transcript) < 50:
        return {
            "summary": "The video content is too short to generate a detailed summary.",
            "start_questions": []
        }

    system_prompt = (
        "You are a Video Analyst AI. Your task is to analyze a video transcript and provide insights.\n\n"
        "Requirements:\n"
        "1. Detailed Summary: Provide a coherent 2-3 paragraph overview of the content, "
        "followed by a bulleted list of 5-7 key takeaways.\n"
        "2. Starter Questions: Provide at least 5 high-quality questions that a viewer can answer "
        "EXPLICITLY using only the information in this transcript.\n"
        "- Do NOT generate questions that require external knowledge.\n"
        "- Do NOT generate questions that go 'beyond' the video content.\n"
        "- Every question MUST have a clear answer in the provided text.\n\n"
        "Output Format (STRICT JSON):\n"
        "{\n"
        "  \"summary\": \"The detailed summary text with markdown bullets\",\n"
        "  \"start_questions\": [\"Question 1\", \"Question 2\", ...]\n"
        "}"
    )

    client = get_genai_client()

    try:
        # Use Async client (aio)
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=f"Analyze this transcript and generate insights:\n\n{transcript}",
            config={
                "system_instruction": system_prompt,
                "response_mime_type": "application/json"
            }
        )
        
        insights = json.loads(response.text)
        logger.info(f"✅ Generated {len(insights.get('start_questions', []))} starter questions.")
        return insights
        
    except Exception as e:
        logger.error(f"❌ Error generating video insights: {e}")
        return {
            "summary": "Error generating detailed summary.",
            "start_questions": []
        }
