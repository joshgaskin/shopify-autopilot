"""
Shopify GraphQL + REST client. Single-tenant, single-store.

Handles rate limiting, retries, and pagination.
"""
import asyncio
import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class ShopifyAPIError(Exception):
    """Raised on Shopify API errors."""

    def __init__(self, message: str | list) -> None:
        if isinstance(message, list):
            message = "; ".join(str(e.get("message", e)) for e in message)
        super().__init__(message)


class ShopifyClient:
    """
    Async Shopify client for a single store.

    Args:
        store_url: The myshopify.com domain (e.g. "store.myshopify.com").
        access_token: Shopify admin access token.
        api_version: Shopify API version.
    """

    MAX_RETRIES = 3
    RATE_LIMIT_DELAY = 0.5  # seconds between GraphQL calls

    def __init__(
        self,
        store_url: str,
        access_token: str,
        api_version: str = "2025-01",
    ) -> None:
        self.store_url = store_url
        self.access_token = access_token
        self.api_version = api_version
        self.base_url = f"https://{store_url}/admin/api/{api_version}"
        self.graphql_url = f"{self.base_url}/graphql.json"
        self.headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(timeout=30.0)

    # ------------------------------------------------------------------
    # Low-level transport
    # ------------------------------------------------------------------

    async def graphql(
        self,
        query: str,
        variables: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Execute a GraphQL query with retries and rate-limit handling."""
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        for attempt in range(self.MAX_RETRIES):
            try:
                resp = await self.client.post(
                    self.graphql_url, json=payload, headers=self.headers,
                )
                resp.raise_for_status()
                data = resp.json()

                if "errors" in data:
                    raise ShopifyAPIError(data["errors"])

                await asyncio.sleep(self.RATE_LIMIT_DELAY)
                return data.get("data", {})

            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning("Rate limited, retrying in %ds...", wait)
                    await asyncio.sleep(wait)
                    continue
                raise ShopifyAPIError(
                    f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"
                )
            except httpx.RequestError as exc:
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(1)
                    continue
                raise ShopifyAPIError(f"Request failed: {exc}")

        raise ShopifyAPIError("Max retries exceeded")

    async def rest(
        self,
        method: str,
        path: str,
        json: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Send a REST request to the Shopify Admin API."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        for attempt in range(self.MAX_RETRIES):
            try:
                resp = await self.client.request(
                    method, url, json=json, headers=self.headers,
                )
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning("Rate limited (REST), retrying in %ds...", wait)
                    await asyncio.sleep(wait)
                    continue
                raise ShopifyAPIError(
                    f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"
                )
            except httpx.RequestError as exc:
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(1)
                    continue
                raise ShopifyAPIError(f"Request failed: {exc}")
        raise ShopifyAPIError("Max retries exceeded")

    async def raw_graphql(
        self,
        query: str,
        variables: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Raw passthrough — returns the full GraphQL response for advanced users."""
        return await self.graphql(query, variables)

    # ------------------------------------------------------------------
    # Products
    # ------------------------------------------------------------------

    PRODUCTS_QUERY = """
    query GetProducts($first: Int!, $after: String) {
        products(first: $first, after: $after) {
            edges {
                cursor
                node {
                    id
                    title
                    handle
                    status
                    productType
                    vendor
                    totalInventory
                    tracksInventory
                    priceRangeV2 {
                        minVariantPrice { amount currencyCode }
                        maxVariantPrice { amount currencyCode }
                    }
                    featuredImage { url }
                    variants(first: 100) {
                        edges {
                            node {
                                id
                                title
                                sku
                                price
                                inventoryQuantity
                            }
                        }
                    }
                    collections(first: 10) {
                        edges { node { title } }
                    }
                }
            }
            pageInfo { hasNextPage endCursor }
        }
    }
    """

    async def get_products(
        self, cursor: Optional[str] = None, limit: int = 50,
    ) -> dict[str, Any]:
        """Fetch a page of products."""
        return await self.graphql(
            self.PRODUCTS_QUERY, {"first": limit, "after": cursor},
        )

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    ORDERS_QUERY = """
    query GetOrders($first: Int!, $after: String, $query: String) {
        orders(first: $first, after: $after, query: $query, sortKey: PROCESSED_AT, reverse: true) {
            edges {
                cursor
                node {
                    id
                    name
                    totalPriceSet { shopMoney { amount currencyCode } }
                    subtotalPriceSet { shopMoney { amount } }
                    totalTaxSet { shopMoney { amount } }
                    totalDiscountsSet { shopMoney { amount } }
                    financialStatus
                    fulfillmentStatus
                    customer { id email firstName lastName }
                    processedAt
                    lineItems(first: 50) {
                        edges {
                            node {
                                id
                                title
                                quantity
                                originalTotalSet { shopMoney { amount } }
                                variant { id }
                                product { id }
                            }
                        }
                    }
                    discountCodes
                    landingSite
                    referringSite
                    tags
                }
            }
            pageInfo { hasNextPage endCursor }
        }
    }
    """

    async def get_orders(
        self,
        cursor: Optional[str] = None,
        limit: int = 50,
        since: Optional[str] = None,
    ) -> dict[str, Any]:
        """Fetch a page of orders, optionally filtered by date."""
        query_filter = f"processed_at:>'{since}'" if since else None
        return await self.graphql(
            self.ORDERS_QUERY,
            {"first": limit, "after": cursor, "query": query_filter},
        )

    # ------------------------------------------------------------------
    # Customers
    # ------------------------------------------------------------------

    CUSTOMERS_QUERY = """
    query GetCustomers($first: Int!, $after: String) {
        customers(first: $first, after: $after) {
            edges {
                cursor
                node {
                    id
                    email
                    firstName
                    lastName
                    ordersCount
                    totalSpentV2 { amount currencyCode }
                    tags
                    createdAt
                    lastOrder { processedAt }
                }
            }
            pageInfo { hasNextPage endCursor }
        }
    }
    """

    async def get_customers(
        self, cursor: Optional[str] = None, limit: int = 50,
    ) -> dict[str, Any]:
        """Fetch a page of customers."""
        return await self.graphql(
            self.CUSTOMERS_QUERY, {"first": limit, "after": cursor},
        )

    # ------------------------------------------------------------------
    # Inventory
    # ------------------------------------------------------------------

    INVENTORY_QUERY = """
    query GetInventory($first: Int!, $after: String) {
        productVariants(first: $first, after: $after) {
            edges {
                cursor
                node {
                    id
                    title
                    sku
                    inventoryQuantity
                    product { id title }
                    inventoryItem {
                        inventoryLevels(first: 5) {
                            edges {
                                node {
                                    quantities(names: "available") { quantity }
                                    location { name }
                                }
                            }
                        }
                    }
                }
            }
            pageInfo { hasNextPage endCursor }
        }
    }
    """

    async def get_inventory_levels(self) -> list[dict[str, Any]]:
        """Fetch all inventory levels across all variants."""
        items: list[dict[str, Any]] = []
        cursor = None
        while True:
            data = await self.graphql(
                self.INVENTORY_QUERY, {"first": 50, "after": cursor},
            )
            variants = data.get("productVariants", {})
            for edge in variants.get("edges", []):
                node = edge["node"]
                cursor = edge["cursor"]
                product = node.get("product", {})
                inv_item = node.get("inventoryItem", {})
                for level_edge in inv_item.get("inventoryLevels", {}).get("edges", []):
                    level = level_edge["node"]
                    qty_list = level.get("quantities", [])
                    qty = qty_list[0]["quantity"] if qty_list else 0
                    items.append({
                        "variant_id": node.get("id", ""),
                        "product_id": product.get("id", ""),
                        "product_title": product.get("title", ""),
                        "variant_title": node.get("title", ""),
                        "sku": node.get("sku", ""),
                        "quantity": qty,
                        "location": level.get("location", {}).get("name", ""),
                    })
            page_info = variants.get("pageInfo", {})
            if not page_info.get("hasNextPage"):
                break
        return items

    # ------------------------------------------------------------------
    # Order creation (for simulator — uses REST API)
    # ------------------------------------------------------------------

    async def create_order(
        self,
        line_items: list[dict[str, Any]],
        customer: Optional[dict[str, Any]] = None,
        discount_code: Optional[str] = None,
        tags: str = "simulated,hackathon",
    ) -> dict[str, Any]:
        """Create an order via the REST Admin API."""
        order_data: dict[str, Any] = {
            "order": {
                "line_items": line_items,
                "financial_status": "paid",
                "tags": tags,
                "note": "Auto-generated hackathon test order",
            }
        }
        if customer:
            order_data["order"]["customer"] = customer
        if discount_code:
            order_data["order"]["discount_codes"] = [
                {"code": discount_code, "amount": "10.00", "type": "percentage"}
            ]
        return await self.rest("POST", "orders.json", json=order_data)

    # ------------------------------------------------------------------
    # ScriptTag injection
    # ------------------------------------------------------------------

    async def create_script_tag(self, src: str) -> dict[str, Any]:
        """Inject a ScriptTag onto the storefront."""
        return await self.rest(
            "POST",
            "script_tags.json",
            json={"script_tag": {"event": "onload", "src": src}},
        )

    # ------------------------------------------------------------------
    # Theme assets
    # ------------------------------------------------------------------

    async def get_theme_id(self) -> int:
        """Get the main theme ID."""
        themes = await self.rest("GET", "themes.json")
        main_theme = next(
            (t for t in themes.get("themes", []) if t.get("role") == "main"),
            None,
        )
        if not main_theme:
            raise ShopifyAPIError("No main theme found")
        return main_theme["id"]

    async def write_theme_asset(
        self, theme_id: int, key: str, value: str,
    ) -> dict[str, Any]:
        """Write a snippet to a theme via the Asset API."""
        return await self.rest(
            "PUT",
            f"themes/{theme_id}/assets.json",
            json={"asset": {"key": key, "value": value}},
        )
