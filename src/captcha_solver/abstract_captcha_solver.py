from abc import ABC, abstractmethod


class AbstractCaptchaSolver(ABC):
    @abstractmethod
    def solve_captcha_from_url(self, image_url: str) -> str:
        pass
