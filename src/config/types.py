from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
)
from typing import Type


class AmazonAccount(BaseModel):
    email: str
    password: str


class Config(BaseSettings):
    amazon_accounts: list[AmazonAccount]

    model_config = SettingsConfigDict(env_prefix="mmac_", case_sensitive=False)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Env settings take precedence over init settings
        return env_settings, init_settings, file_secret_settings
