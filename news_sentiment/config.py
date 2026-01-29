"""
Configuration management for the news sentiment comparison tool.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class NewsAPIConfig(BaseModel):
    """NewsAPI configuration."""

    api_key: str = Field(..., description="NewsAPI.org API key")
    base_url: str = "https://newsapi.org/v2"
    timeout: int = 30
    max_retries: int = 3


class LLMConfig(BaseModel):
    """LLM API configuration (Groq or OpenAI)."""

    provider: str = Field(
        default="groq", description="LLM provider: 'groq' or 'openai'"
    )
    groq_api_key: Optional[str] = Field(default=None, description="Groq API key")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    model: str = Field(
        default="llama-3.1-70b-versatile", description="Model name for Groq"
    )
    openai_model: str = Field(
        default="gpt-4o-mini", description="Model name for OpenAI"
    )
    temperature: float = 0.3
    max_tokens: int = 100
    timeout: int = 60


class MongoDBConfig(BaseModel):
    """MongoDB configuration."""

    uri: str = Field(default="mongodb://localhost:27017/news_sentiment")
    database_name: str = "news_sentiment"
    connection_timeout: int = 10


class APIConfig(BaseModel):
    """FastAPI configuration."""

    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"]
    )


class RSSSourceConfig(BaseModel):
    """RSS feed source configuration."""

    url: str = Field(..., description="RSS feed URL")
    name: str = Field(..., description="Source display name")
    id: str = Field(..., description="Source ID")


class SourceConfig(BaseModel):
    """News source configuration."""

    headlines_per_side: int = Field(
        default=20,
        description="Max headlines per side (conservative/liberal) for even comparison",
    )
    conservative: list[str] = Field(
        default_factory=lambda: ["breitbart-news", "the-blaze", "national-review"],
        description="NewsAPI source IDs for conservative sources",
    )
    liberal: list[str] = Field(
        default_factory=lambda: [
            "cnn",
            "msnbc",
            "the-new-york-times",
            "washington-post",
            "the-guardian",
            "npr",
        ],
        description="NewsAPI source IDs for liberal sources",
    )
    conservative_rss: list[RSSSourceConfig] = Field(
        default_factory=lambda: [
            RSSSourceConfig(
                url="https://www.newsmax.com/rss/Newsfront/16",
                name="Newsmax",
                id="newsmax",
            ),
            RSSSourceConfig(
                url="https://www.newsmax.com/rss/Politics/1",
                name="Newsmax Politics",
                id="newsmax-politics",
            ),
        ],
        description="RSS feed sources for conservative news",
    )
    liberal_rss: list[RSSSourceConfig] = Field(
        default_factory=lambda: [], description="RSS feed sources for liberal news"
    )


class PuffPieceConfig(BaseModel):
    """Configuration for puff piece keyword boosting."""

    keywords: list[str] = Field(
        default_factory=lambda: [
            "heartwarming",
            "inspiring",
            "rescue",
            "hero",
            "cute",
            "adorable",
            "kind",
            "community",
            "hope",
            "smile",
            "joy",
            "volunteer",
            "puppy",
            "kitten",
            "baby",
            "wedding",
            "graduation",
            "surprise",
            "reunion",
            "generous",
            "charity",
            "donation",
            "helping",
            "saved",
            "miracle",
        ]
    )
    boost_multiplier: float = 0.5  # Add 0.5 points per keyword match


class Config(BaseModel):
    """Main application configuration."""

    news_api: NewsAPIConfig
    llm: LLMConfig
    mongodb: MongoDBConfig
    api: APIConfig
    sources: SourceConfig
    puff_pieces: PuffPieceConfig
    log_level: str = "INFO"
    collection_schedule: str = "0 10 * * *"  # Daily at 6 AM

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        # NewsAPI
        news_api_key = os.getenv("NEWS_API_KEY")
        if not news_api_key:
            raise ValueError("NEWS_API_KEY environment variable is required")

        # LLM
        groq_key = os.getenv("GROQ_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        # Filter out placeholder values
        placeholder_patterns = [
            "your_groq_api_key_here",
            "your_key",
            "your_openai_api_key_here",
        ]
        if groq_key and groq_key.strip().lower() in [
            p.lower() for p in placeholder_patterns
        ]:
            groq_key = None
        if openai_key and openai_key.strip().lower() in [
            p.lower() for p in placeholder_patterns
        ]:
            openai_key = None

        if not groq_key and not openai_key:
            raise ValueError(
                "Either GROQ_API_KEY or OPENAI_API_KEY must be set (not placeholders)"
            )

        # Prefer OpenAI if it looks like a real key (starts with sk-), otherwise use Groq if available
        if openai_key and openai_key.startswith("sk-"):
            provider = "openai"
        elif groq_key:
            provider = "groq"
        else:
            provider = "openai"

        # MongoDB

        mongodb_uri = os.getenv(
            "MONGODB_URI", "mongodb://localhost:27017/news_sentiment"
        )

        # API
        cors_origins_str = os.getenv(
            "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
        )
        cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

        return cls(
            news_api=NewsAPIConfig(api_key=news_api_key),
            llm=LLMConfig(
                provider=provider,
                groq_api_key=groq_key,
                openai_api_key=openai_key,
                model=os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile"),
                openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            ),
            mongodb=MongoDBConfig(uri=mongodb_uri),
            api=APIConfig(
                host=os.getenv("API_HOST", "0.0.0.0"),
                port=int(os.getenv("API_PORT", "8000")),
                cors_origins=cors_origins,
            ),
            sources=SourceConfig(),  # Use defaults
            puff_pieces=PuffPieceConfig(),  # Use defaults
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            collection_schedule=os.getenv("COLLECTION_SCHEDULE", "0 10 * * *"),
        )


# Global configuration instance (will be initialized when needed)
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config
