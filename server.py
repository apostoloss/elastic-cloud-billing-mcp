"""MCP Server for Elastic Cloud Billing Analysis."""

import json
import logging
import sys
from datetime import datetime

from fastmcp import FastMCP

from config import settings, available_accounts
from elastic_client import ElasticCloudClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("elastic_cloud_billing_mcp.log"),
        logging.StreamHandler(sys.stderr),
    ],
)
logger = logging.getLogger("elastic-cloud-billing-mcp")

# Initialize FastMCP server
mcp = FastMCP(name="elastic-cloud-billing")


# Initialize billing tools
try:
    logger.info("Initializing Elastic Billing MCP Server...")
    elastic_client = ElasticCloudClient(settings.default_account)
    logger.info("MCP Server initialized successfully")
except Exception as e:
    logger.exception(f"Failed to initialize elastic client: {e!s}")
    raise


# decorators to be used with tools
def auto_doc_mcp_tool():
    """Decorator that automatically uses the function's docstring as MCP tool description."""
    def decorator(func):
        return mcp.tool(description=func.__doc__)(func)
    return decorator


# add a tool to get the list of deployments
@auto_doc_mcp_tool()
async def get_deployments() -> dict:
    """Get the list of deployments."""
    try:
        logger.info("Getting list of deployments")
        result = await elastic_client.get_deployments()
        logger.info(
            f"Successfully retrieved {len(result.get('deployments', []))} deployments"
        )
        return result
    except Exception as e:
        logger.error(f"Failed to get list of deployments: {e!s}")
        return {
            "error": f"Failed to get list of deployments: {e!s}",
        }


@auto_doc_mcp_tool()
async def get_deployment(deployment_id: str) -> dict:
    """Get a specific deployment."""
    try:
        logger.info(f"Getting deployment {deployment_id}")
        result = await elastic_client.get_deployment(deployment_id)
        logger.info(f"Successfully retrieved deployment {deployment_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to get deployment: {e!s}")
        return {
            "error": f"Failed to get deployment: {e!s}",
            "deployment_id": deployment_id,
        }


@auto_doc_mcp_tool()
async def get_items_costs(start_date: datetime, end_date: datetime) -> dict:
    """Get costs broken down by environment/deployment."""
    try:
        logger.info(
            f"Getting items costs for date range from {start_date} to {end_date}"
        )
        result = await elastic_client.get_items_costs(start_date, end_date)
        return result
    except Exception as e:
        logger.error(f"Failed to get items costs: {e!s}")
        return {
            "error": f"Failed to get items costs: {e!s}",
            "start_date": start_date,
            "end_date": end_date,
        }


@auto_doc_mcp_tool()
async def get_instances_costs(start_date: datetime, end_date: datetime) -> dict:
    """Get costs associated with all instances for date range.

        Limitations:
            The period that api works for is up to 140 days.
            Anything above it will fail.
            In cases the user needs more than that you need to split the period to chunks of 4 months.
    """
    try:
        logger.info(
            f"Getting instances costs for date range from {start_date} to {end_date}"
        )
        result = await elastic_client.get_instances_costs(start_date, end_date)
        return result
    except Exception as e:
        logger.error(f"Failed to get instances costs: {e!s}")
        return {
            "error": f"Failed to get instances costs: {e!s}",
            "start_date": start_date,
            "end_date": end_date,
        }



@auto_doc_mcp_tool()
async def get_instance_costs(
    start_date: datetime, end_date: datetime, instance_id: str
) -> dict:
    """Get costs associated to a set of items billed for a single instance for date range.
    Suggested Usage:
        To get the full cost for an instance over a period longer than 12 months, 
        split the period into multiple 12-month segments and call this tool for each segment separately. 
        If this fails, split in monthly segments.

    Limitations:
            The period that api works for is up to 15 months.
            Anything above it will fail.
            In cases the user needs more than that you need to split the period to chunks of 15 months.

    Args:
        start_date: The start date of the time period if this is more than 12 months from end date the api will fail,
            reduce this to 12 months and repeat the call for the rest of the period.
        end_date: The end date of the time period if this is more than 12 months from start date the api will fail, 
            reduce this to 12 months and repeat the call for the rest of the period.
        instance_id: The id of the instance or environment can be found from the get_deployments tool and is the cluster id.
    """
    try:
        logger.info(
            f"Getting instance costs for date range from {start_date} to {end_date} for instance {instance_id}"
        )
        result = await elastic_client.get_instance_costs(
            start_date, end_date, instance_id
        )
        # logger.info(f"Instance costs: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to get instance costs: {e!s}")
        return {
            "error": f"Failed to get instance costs: {e!s}",
            "start_date": start_date,
            "end_date": end_date,
            "instance_id": instance_id,
        }


@mcp.tool(description="Total cost of an environment for a given time period")
async def get_environment_cost(
    start_date: datetime, end_date: datetime, instance_id: str
) -> dict:
    """Total cost of an environment for a given time period"""
    result = await elastic_client.get_instance_costs(start_date, end_date, instance_id)
    if result.get("total_ecu"):
        return {
            "total_ecu": result.get("total_ecu"),
        }
    return {
        "error": "Failed to get environment cost",
    }


@auto_doc_mcp_tool()
async def switch_account(account: str) -> dict:
    """Switch between Elastic Cloud accounts (dev, preprod, default)."""
    try:
        logger.info(f"Switching to account: {account}")
        elastic_client.switch_account(account)
        return {
            "success": True,
            "account": account,
            "org_id": elastic_client.org_id,
            "message": f"Switched to {account} account",
        }
    except Exception as e:
        logger.error(f"Failed to switch account: {e!s}")
        return {
            "success": False,
            "error": f"Failed to switch account: {e!s}",
            "account": account,
        }


@auto_doc_mcp_tool()
async def get_current_account() -> dict:
    """Get current active account information."""
    return {
        "account": elastic_client.account,
        "org_id": elastic_client.org_id,
        "api_key_prefix": elastic_client.api_key[:10] + "..."
        if elastic_client.api_key
        else None,
    }


@auto_doc_mcp_tool()
async def list_accounts() -> dict:
    """List all available accounts based on .env files in configured accounts directory."""
    return available_accounts()


if __name__ == "__main__":
    mcp.run(transport="stdio")
