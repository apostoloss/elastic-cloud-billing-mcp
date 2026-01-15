"""Configuration management for Elastic Billing MCP Server."""
import logging

import os
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings."""
    # You normally don't need to change these defaults
    elastic_region: str = "us-east-1"
    elastic_base_url: str = "https://api.elastic-cloud.com"
    billing_base_url: str = "https://billing.elastic-cloud.com"
    default_account: str = "dev"

    """Account Credentials Configuration."""
    # Elastic Cloud API Configuration
    elastic_api_key: str
    elastic_org_id: str

    # Multi-account support
    accounts_dir: str = "accounts"

    def get_account_credentials(self, account: str = default_account) -> tuple[str, str]:
        """Get API key and org ID for specified account."""
        
        if account in available_accounts().get("accounts", []):
            try:
                env_file_path = os.path.join(self.accounts_dir, f".env.{account}")
                temp_settings = Settings(_env_file=env_file_path)
                logger.info(
                    f"Loaded settings from {env_file_path} for account {account}"
                )
                return temp_settings.elastic_api_key, temp_settings.elastic_org_id
            except Exception as e:
                raise ValueError(f"Could not load credentials for account {account}, confirm .env file exists.{e!s}") from e
        raise ValueError(f"Account {account} not found in accounts directory.")


    model_config = SettingsConfigDict(
        env_file=f"{accounts_dir}/.env.{default_account}",
    )


def available_accounts() -> dict:
    """List all available accounts based on .env files in accounts_dir directory."""
    accounts = []
    try:
        for filename in os.listdir(settings.accounts_dir):
            if filename.startswith(".env."):
                account_name = filename[len(".env.") :]
                accounts.append(account_name)
        return {"accounts": accounts}
    except Exception as e:
        logger.error(f"Failed to list accounts: {e!s}")
        return {"error": f"Failed to list accounts: {e!s}"}


# Global settings instance
settings = Settings()
