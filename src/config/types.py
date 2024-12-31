from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
)
from typing import Optional, Type


class AmazonAccount(BaseModel):
    email: str
    password: str


class MonarchAccount(BaseModel):
    email: str
    password: str


class TransactionTag(BaseModel):
    name: str = "MMAC"
    color: str = "#0390fc"


class AmazonAccountTag(BaseModel):
    enabled: bool = True
    color: str = "#ff9900"
    prefix: str = "AMZ Account: "


class Debug(BaseModel):
    pause_between_navigation: bool = False


class TransactionFilters(BaseModel):
    merchant_name: str
    ignore_case: bool = True
    # Only care if the merchant name _contains_ the name.
    search_by_contains: bool = False


class LLM(BaseModel):
    enable_llm_captcha_solver: bool = False
    api_key: str = ""
    llm_model_name: str = "gpt-4o"
    base_url: Optional[str] = None
    project: Optional[str] = None
    organization: Optional[str] = None


class Config(BaseSettings):
    monarch_account: MonarchAccount
    amazon_accounts: list[AmazonAccount]
    transaction_tag: TransactionTag = TransactionTag()
    transaction_filters: list[TransactionFilters] = []
    amazon_account_tag: AmazonAccountTag = AmazonAccountTag()
    debug: Debug = Debug()
    llm: LLM = LLM()

    headless: bool = True

    # Prefix environment variables with MMAC_, and set them to be case insensitive.
    model_config = SettingsConfigDict(
        env_prefix="mmac_",
        case_sensitive=False,
        extra="ignore",
        env_nested_delimiter="__",
    )

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
