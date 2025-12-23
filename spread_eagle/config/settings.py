from pydantic_settings import BaseSettings
from pydantic import PostgresDsn


class Settings(BaseSettings):
    ENV: str = "dev"
    DATABASE_URL: PostgresDsn = "postgresql://user:pass@localhost:5432/spread_eagle"

    # API Keys
    CFB_API_KEY: str | None = None
    CBB_API_KEY: str | None = None

    @property
    def cfb_api_key(self) -> str:
        """Backwards-compatible alias for CFB ingest scripts."""
        return (self.CFB_API_KEY or "").strip()

    @property
    def cbb_api_key(self) -> str:
        """CBB API key for college basketball data."""
        return (self.CBB_API_KEY or "").strip()

    def require_cfb(self) -> None:
        """Validate CFB API key at runtime."""
        if not self.cfb_api_key:
            raise RuntimeError(
                "Missing CFBD API key. Set CFB_API_KEY in .env"
            )

    def require_cbb(self) -> None:
        """Validate CBB API key at runtime."""
        if not self.cbb_api_key:
            raise RuntimeError(
                "Missing CBB API key. Set CBB_API_KEY in .env"
            )

    def require(self, sport: str = "cfb") -> None:
        """Validate API key for a sport."""
        if sport == "cfb":
            self.require_cfb()
        elif sport == "cbb":
            self.require_cbb()
        else:
            raise ValueError(f"Unknown sport: {sport}")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
