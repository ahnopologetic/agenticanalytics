from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseSettings):
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_service_role_key: str = Field(..., env="SUPABASE_SERVICE_ROLE_KEY")
    github_app_id: str = Field(..., env="GITHUB_APP_ID")
    github_app_private_key_path: str

    model_config = SettingsConfigDict(env_file=".env")
    repo_reader_prompt_path: str = Field(..., env="REPO_READER_PROMPT_PATH")

    @property
    def github_app_private_key(self) -> str:
        with open(self.github_app_private_key_path, "r") as f:
            return f.read()


config = ServerConfig()
