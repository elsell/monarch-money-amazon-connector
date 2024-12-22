from pydantic import BaseModel


class AmazonAccount(BaseModel):
    email: str
    password: str


class Config(BaseModel):
    amazon_accounts: list[AmazonAccount]
