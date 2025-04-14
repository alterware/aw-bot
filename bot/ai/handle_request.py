import os
import requests
from google.genai import types
from google import genai

API_KEY = os.getenv("GOOGLE_API_KEY")


async def forward_to_google_api(prompt, image_object=None):
    """
    Forwards the message content and optional image object to a Google API.

    Args:
        prompt (discord.Message): The message object to forward.
        image_object (tuple, optional): A tuple containing the image URL and its MIME type (e.g., ("url", "image/jpeg")).
    """
    if not API_KEY:
        await prompt.reply(
            "Google API key is not set. Please contact the administrator.",
            mention_author=True,
        )
        return

    client = genai.Client(api_key=API_KEY)

    input = [prompt.content]
    if image_object:
        try:
            image_url, mime_type = image_object
            image = requests.get(image_url)
            image.raise_for_status()
            input.append(types.Part.from_bytes(data=image.content, mime_type=mime_type))
        except requests.RequestException:
            await prompt.reply(f"Failed to fetch the image", mention_author=True)
            return

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=input,
        config=types.GenerateContentConfig(
            max_output_tokens=400,
            system_instruction="You are a Discord chat bot named 'AlterWare' who helps users. You should limit your answers to be less than 2000 characters.",
        ),
    )

    await prompt.reply(
        response.text,
        mention_author=True,
    )
