from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    discord_token: str


load_dotenv()
SETTINGS = Settings()  # pyright: ignore[reportCallIssue]
