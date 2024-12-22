import openai
import os

class LLMTool:
    def __init__(self):
        self._llm = openai.OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )

    def get_llm_response(self, system_prompt: str, prompt: str) -> str | None:
        response = self._llm.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content