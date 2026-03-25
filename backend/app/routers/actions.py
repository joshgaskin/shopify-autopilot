"""Action endpoints — write operations to Shopify."""
import logging

from fastapi import APIRouter, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["actions"])


class DiscountRequest(BaseModel):
    code: str
    percentage: float


class EmailRequest(BaseModel):
    to: str
    subject: str
    html: str


class InjectScriptRequest(BaseModel):
    src: str


class ThemeAssetRequest(BaseModel):
    key: str
    value: str


@router.post("/discounts")
async def create_discount(body: DiscountRequest, request: Request):
    """Create a discount code on Shopify via price rules + discount codes."""
    shopify = request.app.state.shopify

    # Step 1: Create a price rule
    price_rule_data = {
        "price_rule": {
            "title": body.code,
            "target_type": "line_item",
            "target_selection": "all",
            "allocation_method": "across",
            "value_type": "percentage",
            "value": f"-{body.percentage}",
            "customer_selection": "all",
            "starts_at": "2024-01-01T00:00:00Z",
        }
    }
    price_rule_result = await shopify.rest("POST", "price_rules.json", json=price_rule_data)
    price_rule_id = price_rule_result.get("price_rule", {}).get("id")

    if not price_rule_id:
        return {"error": "Failed to create price rule", "details": price_rule_result}

    # Step 2: Create the discount code
    discount_data = {
        "discount_code": {
            "code": body.code,
        }
    }
    result = await shopify.rest(
        "POST",
        f"price_rules/{price_rule_id}/discount_codes.json",
        json=discount_data,
    )
    return result


@router.post("/notifications/email")
async def send_email(body: EmailRequest):
    """Placeholder email sender — logs to console."""
    logger.info("EMAIL NOTIFICATION:")
    logger.info("  To: %s", body.to)
    logger.info("  Subject: %s", body.subject)
    logger.info("  Body: %s", body.html[:200])
    return {
        "status": "logged",
        "message": "Email logged to console (no email provider configured)",
        "to": body.to,
        "subject": body.subject,
    }


@router.post("/storefront/inject")
async def inject_script(body: InjectScriptRequest, request: Request):
    """Create a ScriptTag on the Shopify storefront."""
    shopify = request.app.state.shopify
    result = await shopify.create_script_tag(body.src)
    return result


@router.post("/storefront/theme")
async def write_theme_asset(body: ThemeAssetRequest, request: Request):
    """Write a theme asset (snippet, template, etc.)."""
    shopify = request.app.state.shopify
    theme_id = await shopify.get_theme_id()
    result = await shopify.write_theme_asset(theme_id, body.key, body.value)
    return result
