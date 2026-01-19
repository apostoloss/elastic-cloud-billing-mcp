"""Elastic Cloud API client for billing and deployment data."""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any

import httpx
from async_lru import alru_cache

from config import settings

logger = logging.getLogger("elastic-cloud-billing-mcp.elastic-client")


class ElasticCloudClient:
    """Client for interacting with Elastic Cloud API."""

    def __init__(self, account: str):
        try:
            logger.info(f"Initializing Elastic Cloud client for account: {account}")
            self.account = account  # This is how we identify the account in our settings, not related to API or org IDs
            self.api_key  = settings.get_account_credentials(account)[0]
            self.org_id = settings.get_account_credentials(account)[1] or None  # Can be ommited in env
            self.base_url = settings.elastic_base_url
            self.billing_base_url = settings.billing_base_url
            self._account_id = None  # Lazy loaded account ID from /api/v1/account, acts as org_id if none provided

            self.headers = {
                "Authorization": f"ApiKey {self.api_key}",
                "Content-Type": "application/json",
            }
            logger.info(
                f"Elastic Cloud client initialized for account: {account}, org: {self.org_id or 'Not Provided'}"
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
            self._account_id = None  # Reset cached account ID
            logger.info(f"Switched to account: {account}, org: {self.org_id or 'Not Provided'}")
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

    @alru_cache(maxsize=128)
    async def _cached_billing_request(
        self, 
        endpoint: str, 
        startdate_iso: str | None=None, 
        enddate_iso: str | None=None, 
        ) -> dict[str, Any]:
        """Make authenticated request to Elastic Cloud Billing API with caching."""
        params = {}
        if startdate_iso:
            params["from"] = startdate_iso
        if enddate_iso:
            params["to"] = enddate_iso
            
        return await self._make_billing_request(endpoint, params)

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
        return await self._get_deployments_cached(self.org_id)

    @alru_cache(maxsize=32, ttl=300)
    async def _get_deployments_cached(self, org_id: str | None) -> list[dict[str, Any]]:
        """Get all deployments for the account or filtered with org_id, with caching."""
        endpoint = "/api/v1/deployments"
        if org_id is None:
            params = None
        else:
            params = {"q": f"organization_id:{org_id}"}
        return await self._make_request(endpoint, params)

    @alru_cache(maxsize=32, ttl=300)
    async def get_deployment(self, deployment_id: str) -> dict[str, Any]:
        """Get specific deployment details."""
        endpoint = f"/api/v1/deployments/{deployment_id}"
        return await self._make_request(endpoint)

    async def get_account_info(self) -> dict[str, Any]:
        """Get account information."""
        endpoint = f"/api/v1/account"
        if self._account_id is None:
            result = await self._make_request(endpoint)
            self._account_id = result.get("id") # Cache account ID
        return {"id" : self._account_id }

    async def get_organizations(self) -> list[dict[str, Any]]:
        """Get organizations accessible with the current API key."""
        endpoint = "/api/v1/organizations"
        return await self._make_request(endpoint)

    async def get_organization(self, org_id: str | None) -> dict[str, Any]:
        """Get specific organization details. If org_id is None, use current account id."""
        endpoint = f"/api/v1/organizations/{org_id or self._account_id}"
        return await self._make_request(endpoint)

    async def get_organization_members(self, org_id: str | None) -> list[dict[str, Any]]:
        """Get members of the current organization."""
        endpoint = f"/api/v1/organizations/{org_id or self._account_id}/members"
        return await self._make_request(endpoint)

    # Get billing data methods
    async def get_instances_costs(
        self, start_date: datetime, end_date: datetime, organization_id: str
    ) -> dict[str, Any]:
        """Get costs associated with all instances for date range."""
        endpoint = f"/api/v2/billing/organizations/{organization_id}/costs/instances"

        return await self._cached_billing_request(
            endpoint, 
            startdate_iso=start_date.astimezone(ZoneInfo("UTC")).isoformat(),
            enddate_iso=end_date.astimezone(ZoneInfo("UTC")).isoformat(),
            # org_id=organization_id
        )

    async def get_instance_costs(
        self, start_date: datetime, end_date: datetime, organization_id: str, instance_id: str
    ) -> dict[str, Any]:
        """Get costs associated to a set of items billed for a single instance for date range."""
        endpoint = f"/api/v2/billing/organizations/{organization_id}/costs/instances/{instance_id}/items"

        return await self._cached_billing_request(
            endpoint, 
            startdate_iso=start_date.astimezone(ZoneInfo("UTC")).isoformat(),
            enddate_iso=end_date.astimezone(ZoneInfo("UTC")).isoformat(),
            # org_id=organization_id
        )

    async def get_items_costs(
        self, start_date: datetime, end_date: datetime, organization_id: str
    ) -> dict[str, Any]:
        """Get costs for all items for specific organization."""
        endpoint = f"/api/v2/billing/organizations/{organization_id}/costs/items"

        return await self._cached_billing_request(
            endpoint, 
            startdate_iso=start_date.astimezone(ZoneInfo("UTC")).isoformat(),
            enddate_iso=end_date.astimezone(ZoneInfo("UTC")).isoformat(),
        )