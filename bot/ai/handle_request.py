import os
from google import genai

API_KEY = os.getenv("GOOGLE_API_KEY")


async def forward_to_google_api(prompt):
    """
    Forwards the message content and optional image URL to a Google API.

    Args:
        prompt (discord.Message): The message object to forward.
    """
    client = genai.Client(api_key=API_KEY)

    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=prompt.content
    )

    await prompt.reply(
        response.text,
        mention_author=True,
    )
