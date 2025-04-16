import os
import requests
from google.genai import types
from google import genai

API_KEY = os.getenv("GOOGLE_API_KEY")


class DiscourseSummarizer:
    def __init__(self):
        self.model = "gemini-2.0-flash"
        self.display_name = "alterware"
        self.cache = None
        self.ttl = "21600s"
        self.discourse_data = None

        if not API_KEY:
            print("Google API key is not set. Please contact the administrator.")
            return

        self.client = genai.Client(api_key=API_KEY)

    def set_discourse_data(self, topic_data):
        """
        Sets the discourse data for the summarizer.

        Args:
            topic_data (str): The combined text of discourse posts.
        """
        self.discourse_data = topic_data

    def summarize_discourse_topic(self, topic_data, system_instruction=None):
        """
        Creates a cache for the discourse topic data.

        Args:
            topic_data (str): The combined text of discourse posts.
            system_instruction (str, optional): Custom system instruction for the model.
        """
        self.cache = self.client.caches.create(
            model=self.model,
            config=types.CreateCachedContentConfig(
                display_name=self.display_name,
                system_instruction=system_instruction
                or (
                    "You are a Discord chat bot named 'AlterWare' who helps users. You should limit your answers to be less than 2000 characters."
                ),
                contents=[topic_data],
                ttl=self.ttl,
            ),
        )
        print(f"Cached content created: {self.cache.name}")

    def update_cache(self):
        """
        Updates the cache TTL.
        """
        if not self.cache:
            raise RuntimeError(
                "Cache has not been created. Run summarize_discourse_topic first."
            )

        self.client.caches.update(
            name=self.cache.name, config=types.UpdateCachedContentConfig(ttl="21600s")
        )
        print("Cache updated.")

    def ask(self, prompt):
        """
        Generates a response using the cached content.

        Args:
            prompt (str): The user prompt.

        Returns:
            str: The generated response.
        """
        if not self.cache:
            raise RuntimeError(
                "Cache has not been created. Run summarize_discourse_topic first."
            )

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=400,
                system_instruction="You are a Discord chat bot named 'AlterWare' who helps users. You should limit your answers to be less than 2000 characters.",
                cached_content=self.cache.name,
            ),
        )
        return response.text

    def ask_without_cache(self, prompt):
        """
        Generates a response without using cached content, including discourse data.

        Args:
            prompt (str): The user prompt.

        Returns:
            str: The generated response.
        """
        if not self.discourse_data:
            raise RuntimeError(
                "Discourse data has not been set. Use set_discourse_data first."
            )

        prompt.insert(0, self.discourse_data)
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=400,
                system_instruction="You are a Discord chat bot named 'AlterWare' who helps users. You should limit your answers to be less than 2000 characters.",
            ),
        )
        return response.text


async def forward_to_google_api(prompt, bot, image_object=None, reply=None):
    """
    Forwards the message content and optional image object to a Google API.

    Args:
        prompt (discord.Message): The message object to forward.
        bot (discord.Client): The Discord bot instance.
        image_object (tuple, optional): A tuple containing the image URL and its MIME type (e.g., ("url", "image/jpeg")).
        reply (discord.Message, optional): The message that was referenced by prompt.
    """
    if not API_KEY:
        await prompt.reply(
            "Google API key is not set. Please contact the administrator.",
            mention_author=True,
        )
        return

    input = [prompt.content]

    # Have the reply come first in the prompt
    if reply:
        input.insert(0, reply.content)

    if image_object:
        try:
            image_url, mime_type = image_object
            image = requests.get(image_url)
            image.raise_for_status()

            # If there is an image, add it to the input before anything else
            input.insert(
                0, types.Part.from_bytes(data=image.content, mime_type=mime_type)
            )
        except requests.RequestException:
            await prompt.reply(f"Failed to fetch the image", mention_author=True)
            return

    response = bot.ai_helper.ask_without_cache(input)

    await prompt.reply(
        response,
        mention_author=True,
    )
