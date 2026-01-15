"""Elastic Cloud API client for billing and deployment data."""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any

import httpx

from config import settings

logger = logging.getLogger("elastic-cloud-billing-mcp.elastic-client")


class ElasticCloudClient:
    """Client for interacting with Elastic Cloud API."""

    def __init__(self, account: str):
        try:
            logger.info(f"Initializing Elastic Cloud client for account: {account}")
            self.account = account
            self.api_key, self.org_id = settings.get_account_credentials(account)
            self.base_url = settings.elastic_base_url
            self.billing_base_url = settings.billing_base_url

            self.headers = {
                "Authorization": f"ApiKey {self.api_key}",
                "Content-Type": "application/json",
            }
            logger.info(
                f"Elastic Cloud client initialized for account: {account}, org: {self.org_id}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Elastic Cloud client: {e!s}")
            raise

    def switch_account(self, account: str):
        """Switch to a different account."""
        logger.info(f"Switching from {self.account} to {account}")
        try:
            self.api_key, self.org_id = settings.get_account_credentials(account)
            self.account = account
            self.headers["Authorization"] = f"ApiKey {self.api_key}"
            logger.info(f"Switched to account: {account}, org: {self.org_id}")
        except Exception as e:
            logger.error(f"Failed to switch account to {account}: {e!s}")
            raise ValueError(f"Could not switch to account {account}") from e

    async def _make_request(
        self, endpoint: str, params: dict | None = None
    ) -> dict[str, Any]:
        """Make authenticated request to Elastic Cloud API."""
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"Making API request to: {endpoint}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                logger.debug(f"API request successful: {response.status_code}")
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error {e.response.status_code} for {endpoint}: {e.response.text}"
            )
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for {endpoint}: {e!s}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {endpoint}: {e!s}")
            raise

    async def _make_billing_request(
        self, endpoint: str, params: dict | None = None
    ) -> dict[str, Any]:
        """Make authenticated request to Elastic Cloud Billing API."""
        url = f"{self.billing_base_url}{endpoint}"
        logger.debug(f"Making billing API request to: {endpoint}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                logger.debug(f"Billing API request successful: {response.status_code}")
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error {e.response.status_code} for billing {endpoint}: {e.response.text}"
            )
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for billing {endpoint}: {e!s}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error for billing {endpoint}: {e!s}")
            raise

    async def get_deployments(self) -> list[dict[str, Any]]:
        """Get all deployments for the organization."""
        endpoint = "/api/v1/deployments"
        params = {"q": f"organization_id:{self.org_id}"}
        return await self._make_request(endpoint, params)

    async def get_deployment(self, deployment_id: str) -> dict[str, Any]:
        """Get specific deployment details."""
        endpoint = f"/api/v1/deployments/{deployment_id}"
        return await self._make_request(endpoint)

    async def get_instances_costs(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Get costs associated with all instances for date range."""
        endpoint = f"/api/v2/billing/organizations/{self.org_id}/costs/instances"

        # Convert to UTC for API
        start_utc = start_date.astimezone(ZoneInfo("UTC"))
        end_utc = end_date.astimezone(ZoneInfo("UTC"))

        params = {
            "from": start_utc.isoformat(),
            "to": end_utc.isoformat(),
            "organization_id": self.org_id,
        }

        return await self._make_billing_request(endpoint, params)

    async def get_instance_costs(
        self, start_date: datetime, end_date: datetime, instance_id: str
    ) -> dict[str, Any]:
        """Get costs associated to a set of items billed for a single instance for date range."""
        endpoint = f"/api/v2/billing/organizations/{self.org_id}/costs/instances/{instance_id}/items"

        # Convert to UTC for API
        start_utc = start_date.astimezone(ZoneInfo("UTC"))
        end_utc = end_date.astimezone(ZoneInfo("UTC"))

        params = {
            "from": start_utc.isoformat(),
            "to": end_utc.isoformat(),
            "organization_id": self.org_id,
        }

        return await self._make_billing_request(endpoint, params)

    async def get_items_costs(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Get costs for specific deployment."""
        endpoint = f"/api/v2/billing/organizations/{self.org_id}/costs/items"

        start_utc = start_date.astimezone(ZoneInfo("UTC"))
        end_utc = end_date.astimezone(ZoneInfo("UTC"))

        params = {
            "from": start_utc.isoformat(),
            "to": end_utc.isoformat(),
            "organization_id": self.org_id,
        }

        return await self._make_billing_request(endpoint, params)
