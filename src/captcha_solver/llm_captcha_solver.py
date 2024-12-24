from typing import Optional
import openai
from .abstract_captcha_solver import AbstractCaptchaSolver
from pydantic import BaseModel


class LLMCaptchaOutput(BaseModel):
    letters: str


class LLMCaptchaSolver(AbstractCaptchaSolver):
    def __init__(
        self,
        openai_api_key: str,
        model_name: str,
        base_url: Optional[str] = None,
        organization: Optional[str] = None,
        project: Optional[str] = None,
    ):
        self._llm = openai.OpenAI(
            api_key=openai_api_key,
            base_url=base_url,
            project=project,
            organization=organization,
        )

        self._model_name = model_name

    def _get_prompt(self) -> str:
        return (
            "This image is a captcha, designed to be intentionally difficult to read. Please identify the letters and numbers contained within this image."
            "Respond only with a JSON object in this format: { 'letters': 'answer here' }"
        )

    def solve_captcha_from_url(self, image_url: str) -> str:
        prompt = self._get_prompt()

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url, "detail": "low"},
                    },
                ],
            },
        ]

        response = self._llm.beta.chat.completions.parse(
            messages=messages,  # type: ignore
            model=self._model_name,
            max_tokens=100,
            response_format=LLMCaptchaOutput,
        )

        letters = response.choices[0].message.parsed

        if not letters:
            raise ValueError("Failed to solve captcha")

        return letters.letters
