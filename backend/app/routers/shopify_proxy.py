"""Shopify GraphQL passthrough — raw access for advanced builders."""
from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Any, Optional

router = APIRouter(tags=["shopify"])


class GraphQLRequest(BaseModel):
    query: str
    variables: Optional[dict[str, Any]] = None


@router.post("/shopify/graphql")
async def shopify_graphql(body: GraphQLRequest, request: Request):
    """Forward a raw GraphQL query to the Shopify Admin API."""
    shopify = request.app.state.shopify
    result = await shopify.raw_graphql(body.query, body.variables)
    return result
