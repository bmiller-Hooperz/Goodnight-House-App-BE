from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openai/gpt-oss-20b:free"
    openrouter_fallback_model: str = "meta-llama/llama-3.3-70b-instruct:free"

    library_path: Path = ROOT / "resources" / "goodnight_house_AI_Library.jsonl"
    system_prompt_path: Path = ROOT / "prompts" / "system_prompt.txt"
    always_on_path: Path = ROOT / "prompts" / "always_on.txt"
    chroma_dir: Path = ROOT / "data" / "chroma"
    chroma_collection: str = "gnh_library"

    chat_top_k: int = 6
    host: str = "0.0.0.0"
    port: int = 8000


settings = Settings()


def has_openrouter_key() -> bool:
    key = (settings.openrouter_api_key or "").strip()
    if not key:
        return False
    placeholders = {
        "sk-or-v1-your-key-here",
        "your-key-here",
        "changeme",
    }
    return key not in placeholders
