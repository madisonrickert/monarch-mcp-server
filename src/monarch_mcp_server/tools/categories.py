"""Category tools."""

import logging
from typing import Any, Dict, Optional

from monarch_mcp_server.app import mcp
from monarch_mcp_server.client import get_monarch_client
from monarch_mcp_server.helpers import json_success, json_error

logger = logging.getLogger(__name__)


@mcp.tool()
async def get_categories() -> str:
    """
    Get all transaction categories from Monarch Money.

    Returns a list of categories with their groups, icons, and metadata.
    Useful for selecting a category when categorizing transactions.
    """
    try:
        client = await get_monarch_client()
        categories_data = await client.get_transaction_categories()

        category_list = []
        for cat in categories_data.get("categories", []):
            category_info = {
                "id": cat.get("id"),
                "name": cat.get("name"),
                "icon": cat.get("icon"),
                "group": cat.get("group", {}).get("name") if cat.get("group") else None,
                "group_id": cat.get("group", {}).get("id") if cat.get("group") else None,
                "is_system_category": cat.get("isSystemCategory", False),
                "is_disabled": cat.get("isDisabled", False),
            }
            category_list.append(category_info)

        return json_success(category_list)
    except Exception as e:
        return json_error("get_categories", e)


@mcp.tool()
async def get_transaction_categories() -> str:
    """Get all available transaction categories from Monarch Money."""
    try:
        client = await get_monarch_client()
        data = await client.get_transaction_categories()
        categories = []
        for cat in data.get("categories", []):
            group = cat.get("group") or {}
            categories.append(
                {
                    "id": cat.get("id"),
                    "name": cat.get("name"),
                    "icon": cat.get("icon"),
                    "group": group.get("name") if isinstance(group, dict) else None,
                    "group_id": group.get("id") if isinstance(group, dict) else None,
                }
            )
        return json_success(categories)
    except Exception as e:
        return json_error("get_transaction_categories", e)


@mcp.tool()
async def get_transaction_category_groups() -> str:
    """Get all transaction category groups (parent groupings for categories)."""
    try:
        client = await get_monarch_client()
        data = await client.get_transaction_category_groups()
        groups = [
            {"id": g.get("id"), "name": g.get("name"), "type": g.get("type")}
            for g in data.get("categoryGroups", [])
        ]
        return json_success(groups)
    except Exception as e:
        return json_error("get_transaction_category_groups", e)


@mcp.tool()
async def create_transaction_category(
    group_id: str,
    transaction_category_name: str,
    icon: Optional[str] = None,
    rollover_enabled: Optional[bool] = None,
    rollover_type: Optional[str] = None,
) -> str:
    """
    Create a new transaction category.

    Args:
        group_id: The category group ID this category belongs to
        transaction_category_name: Name of the new category
        icon: Optional emoji icon for the category
        rollover_enabled: Optional, whether budget rollover is enabled
        rollover_type: Optional rollover type (e.g. "monthly")
    """
    try:
        client = await get_monarch_client()
        kwargs: Dict[str, Any] = {
            "group_id": group_id,
            "transaction_category_name": transaction_category_name,
        }
        if icon is not None:
            kwargs["icon"] = icon
        if rollover_enabled is not None:
            kwargs["rollover_enabled"] = rollover_enabled
        if rollover_type is not None:
            kwargs["rollover_type"] = rollover_type
        result = await client.create_transaction_category(**kwargs)
        return json_success(result)
    except Exception as e:
        return json_error("create_transaction_category", e)


@mcp.tool()
async def get_category_groups() -> str:
    """
    Get all transaction category groups from Monarch Money.

    Returns groups like Income, Expenses, etc. with their associated categories.
    """
    try:
        client = await get_monarch_client()
        groups_data = await client.get_transaction_category_groups()

        group_list = []
        for group in groups_data.get("categoryGroups", []):
            group_info = {
                "id": group.get("id"),
                "name": group.get("name"),
                "type": group.get("type"),
                "budget_variability": group.get("budgetVariability"),
                "group_level_budgeting_enabled": group.get("groupLevelBudgetingEnabled", False),
                "categories": [
                    {
                        "id": cat.get("id"),
                        "name": cat.get("name"),
                        "icon": cat.get("icon"),
                    }
                    for cat in group.get("categories", [])
                ],
            }
            group_list.append(group_info)

        return json_success(group_list)
    except Exception as e:
        return json_error("get_category_groups", e)
