#!/usr/bin/env python3
"""
Seed script — loads a curated DTC product catalog into a Shopify dev store.

Usage:
  python backend/seed.py                              # Uses .env
  python backend/seed.py --tokens tokens.json --all   # All stores
  python backend/seed.py --store gzh-07.myshopify.com --token shpat_xxx
"""
import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import httpx
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Curated DTC fashion/lifestyle catalog
# ---------------------------------------------------------------------------

COLLECTIONS = [
    {"title": "Best Sellers", "handle": "best-sellers"},
    {"title": "New Arrivals", "handle": "new-arrivals"},
    {"title": "Sale", "handle": "sale"},
    {"title": "Core Collection", "handle": "core"},
    {"title": "Limited Edition", "handle": "limited-edition"},
]

PRODUCTS = [
    {"title": "Classic Logo Tee", "type": "T-Shirts", "vendor": "House Brand", "collection": "Best Sellers",
     "variants": [
         {"title": "S / Black", "price": "29.00", "sku": "CLT-S-BLK", "inventory": 45},
         {"title": "M / Black", "price": "29.00", "sku": "CLT-M-BLK", "inventory": 62},
         {"title": "L / Black", "price": "29.00", "sku": "CLT-L-BLK", "inventory": 38},
         {"title": "S / White", "price": "29.00", "sku": "CLT-S-WHT", "inventory": 51},
         {"title": "M / White", "price": "29.00", "sku": "CLT-M-WHT", "inventory": 73},
         {"title": "L / White", "price": "29.00", "sku": "CLT-L-WHT", "inventory": 29},
     ]},
    {"title": "Everyday Hoodie", "type": "Hoodies", "vendor": "House Brand", "collection": "Best Sellers",
     "variants": [
         {"title": "S / Charcoal", "price": "65.00", "sku": "EH-S-CHR", "inventory": 22},
         {"title": "M / Charcoal", "price": "65.00", "sku": "EH-M-CHR", "inventory": 41},
         {"title": "L / Charcoal", "price": "65.00", "sku": "EH-L-CHR", "inventory": 33},
         {"title": "XL / Charcoal", "price": "65.00", "sku": "EH-XL-CHR", "inventory": 18},
     ]},
    {"title": "Signature Cap", "type": "Accessories", "vendor": "House Brand", "collection": "Best Sellers",
     "variants": [
         {"title": "One Size / Black", "price": "32.00", "sku": "SC-OS-BLK", "inventory": 89},
         {"title": "One Size / Navy", "price": "32.00", "sku": "SC-OS-NVY", "inventory": 67},
     ]},
    {"title": "Essential Joggers", "type": "Pants", "vendor": "House Brand", "collection": "Best Sellers",
     "variants": [
         {"title": "S / Grey", "price": "55.00", "sku": "EJ-S-GRY", "inventory": 30},
         {"title": "M / Grey", "price": "55.00", "sku": "EJ-M-GRY", "inventory": 48},
         {"title": "L / Grey", "price": "55.00", "sku": "EJ-L-GRY", "inventory": 25},
         {"title": "S / Black", "price": "55.00", "sku": "EJ-S-BLK", "inventory": 37},
         {"title": "M / Black", "price": "55.00", "sku": "EJ-M-BLK", "inventory": 52},
         {"title": "L / Black", "price": "55.00", "sku": "EJ-L-BLK", "inventory": 19},
     ]},
    {"title": "Weekend Tote", "type": "Bags", "vendor": "House Brand", "collection": "Best Sellers",
     "variants": [
         {"title": "One Size / Canvas", "price": "45.00", "sku": "WT-OS-CNV", "inventory": 74},
     ]},
    {"title": "Oversized Crew Sweatshirt", "type": "Sweatshirts", "vendor": "House Brand", "collection": "New Arrivals",
     "variants": [
         {"title": "S / Sage", "price": "58.00", "sku": "OCS-S-SAG", "inventory": 40},
         {"title": "M / Sage", "price": "58.00", "sku": "OCS-M-SAG", "inventory": 55},
         {"title": "L / Sage", "price": "58.00", "sku": "OCS-L-SAG", "inventory": 35},
         {"title": "S / Dusty Rose", "price": "58.00", "sku": "OCS-S-DR", "inventory": 28},
         {"title": "M / Dusty Rose", "price": "58.00", "sku": "OCS-M-DR", "inventory": 42},
     ]},
    {"title": "Ribbed Tank Top", "type": "Tops", "vendor": "House Brand", "collection": "New Arrivals",
     "variants": [
         {"title": "XS / White", "price": "24.00", "sku": "RTT-XS-WHT", "inventory": 60},
         {"title": "S / White", "price": "24.00", "sku": "RTT-S-WHT", "inventory": 85},
         {"title": "M / White", "price": "24.00", "sku": "RTT-M-WHT", "inventory": 70},
         {"title": "XS / Black", "price": "24.00", "sku": "RTT-XS-BLK", "inventory": 55},
         {"title": "S / Black", "price": "24.00", "sku": "RTT-S-BLK", "inventory": 90},
         {"title": "M / Black", "price": "24.00", "sku": "RTT-M-BLK", "inventory": 65},
     ]},
    {"title": "Linen Blend Shorts", "type": "Shorts", "vendor": "House Brand", "collection": "New Arrivals",
     "variants": [
         {"title": "S / Sand", "price": "42.00", "sku": "LBS-S-SND", "inventory": 33},
         {"title": "M / Sand", "price": "42.00", "sku": "LBS-M-SND", "inventory": 47},
         {"title": "L / Sand", "price": "42.00", "sku": "LBS-L-SND", "inventory": 26},
         {"title": "S / Olive", "price": "42.00", "sku": "LBS-S-OLV", "inventory": 38},
         {"title": "M / Olive", "price": "42.00", "sku": "LBS-M-OLV", "inventory": 51},
     ]},
    {"title": "Crossbody Sling Bag", "type": "Bags", "vendor": "House Brand", "collection": "New Arrivals",
     "variants": [
         {"title": "One Size / Black", "price": "38.00", "sku": "CSB-OS-BLK", "inventory": 63},
         {"title": "One Size / Olive", "price": "38.00", "sku": "CSB-OS-OLV", "inventory": 44},
     ]},
    {"title": "Performance Socks (3-Pack)", "type": "Accessories", "vendor": "House Brand", "collection": "New Arrivals",
     "variants": [
         {"title": "S/M / White", "price": "19.00", "sku": "PS3-SM-WHT", "inventory": 120},
         {"title": "L/XL / White", "price": "19.00", "sku": "PS3-LX-WHT", "inventory": 95},
         {"title": "S/M / Black", "price": "19.00", "sku": "PS3-SM-BLK", "inventory": 110},
         {"title": "L/XL / Black", "price": "19.00", "sku": "PS3-LX-BLK", "inventory": 88},
     ]},
    {"title": "Heavyweight Pocket Tee", "type": "T-Shirts", "vendor": "House Brand", "collection": "Core Collection",
     "variants": [
         {"title": "S / Navy", "price": "35.00", "sku": "HPT-S-NVY", "inventory": 42},
         {"title": "M / Navy", "price": "35.00", "sku": "HPT-M-NVY", "inventory": 58},
         {"title": "L / Navy", "price": "35.00", "sku": "HPT-L-NVY", "inventory": 31},
         {"title": "XL / Navy", "price": "35.00", "sku": "HPT-XL-NVY", "inventory": 15},
     ]},
    {"title": "Slim Chinos", "type": "Pants", "vendor": "House Brand", "collection": "Core Collection",
     "variants": [
         {"title": "30 / Khaki", "price": "68.00", "sku": "SC-30-KHK", "inventory": 20},
         {"title": "32 / Khaki", "price": "68.00", "sku": "SC-32-KHK", "inventory": 35},
         {"title": "34 / Khaki", "price": "68.00", "sku": "SC-34-KHK", "inventory": 28},
         {"title": "30 / Navy", "price": "68.00", "sku": "SC-30-NVY", "inventory": 22},
         {"title": "32 / Navy", "price": "68.00", "sku": "SC-32-NVY", "inventory": 40},
         {"title": "34 / Navy", "price": "68.00", "sku": "SC-34-NVY", "inventory": 30},
     ]},
    {"title": "Quarter-Zip Pullover", "type": "Outerwear", "vendor": "House Brand", "collection": "Core Collection",
     "variants": [
         {"title": "S / Heather Grey", "price": "72.00", "sku": "QZP-S-HG", "inventory": 18},
         {"title": "M / Heather Grey", "price": "72.00", "sku": "QZP-M-HG", "inventory": 27},
         {"title": "L / Heather Grey", "price": "72.00", "sku": "QZP-L-HG", "inventory": 21},
     ]},
    {"title": "Canvas Belt", "type": "Accessories", "vendor": "House Brand", "collection": "Core Collection",
     "variants": [
         {"title": "S/M / Brown", "price": "28.00", "sku": "CB-SM-BRN", "inventory": 55},
         {"title": "L/XL / Brown", "price": "28.00", "sku": "CB-LX-BRN", "inventory": 42},
         {"title": "S/M / Black", "price": "28.00", "sku": "CB-SM-BLK", "inventory": 61},
         {"title": "L/XL / Black", "price": "28.00", "sku": "CB-LX-BLK", "inventory": 38},
     ]},
    {"title": "Cotton Boxer Briefs (2-Pack)", "type": "Underwear", "vendor": "House Brand", "collection": "Core Collection",
     "variants": [
         {"title": "S / Mixed", "price": "22.00", "sku": "CBB-S-MX", "inventory": 80},
         {"title": "M / Mixed", "price": "22.00", "sku": "CBB-M-MX", "inventory": 105},
         {"title": "L / Mixed", "price": "22.00", "sku": "CBB-L-MX", "inventory": 72},
         {"title": "XL / Mixed", "price": "22.00", "sku": "CBB-XL-MX", "inventory": 45},
     ]},
    {"title": "Last Season Windbreaker", "type": "Outerwear", "vendor": "House Brand", "collection": "Sale",
     "variants": [
         {"title": "M / Orange", "price": "49.00", "sku": "LSW-M-ORG", "inventory": 8},
         {"title": "L / Orange", "price": "49.00", "sku": "LSW-L-ORG", "inventory": 5},
         {"title": "M / Teal", "price": "49.00", "sku": "LSW-M-TEL", "inventory": 12},
         {"title": "L / Teal", "price": "49.00", "sku": "LSW-L-TEL", "inventory": 7},
     ]},
    {"title": "Graphic Print Tee - Archive", "type": "T-Shirts", "vendor": "House Brand", "collection": "Sale",
     "variants": [
         {"title": "S / White", "price": "19.00", "sku": "GPT-S-WHT", "inventory": 14},
         {"title": "M / White", "price": "19.00", "sku": "GPT-M-WHT", "inventory": 22},
         {"title": "L / White", "price": "19.00", "sku": "GPT-L-WHT", "inventory": 9},
     ]},
    {"title": "Fleece Beanie", "type": "Accessories", "vendor": "House Brand", "collection": "Sale",
     "variants": [
         {"title": "One Size / Charcoal", "price": "15.00", "sku": "FB-OS-CHR", "inventory": 35},
         {"title": "One Size / Burgundy", "price": "15.00", "sku": "FB-OS-BRG", "inventory": 28},
     ]},
    {"title": "Denim Trucker Jacket", "type": "Outerwear", "vendor": "House Brand", "collection": "Sale",
     "variants": [
         {"title": "S / Indigo", "price": "79.00", "sku": "DTJ-S-IND", "inventory": 6},
         {"title": "M / Indigo", "price": "79.00", "sku": "DTJ-M-IND", "inventory": 11},
         {"title": "L / Indigo", "price": "79.00", "sku": "DTJ-L-IND", "inventory": 4},
     ]},
    {"title": "Outlet Polo", "type": "Tops", "vendor": "House Brand", "collection": "Sale",
     "variants": [
         {"title": "M / White", "price": "25.00", "sku": "OP-M-WHT", "inventory": 17},
         {"title": "L / White", "price": "25.00", "sku": "OP-L-WHT", "inventory": 10},
         {"title": "M / Navy", "price": "25.00", "sku": "OP-M-NVY", "inventory": 23},
         {"title": "L / Navy", "price": "25.00", "sku": "OP-L-NVY", "inventory": 13},
     ]},
    {"title": "Artist Collab Hoodie - Drop 01", "type": "Hoodies", "vendor": "House Brand", "collection": "Limited Edition",
     "variants": [
         {"title": "S / Multicolor", "price": "120.00", "sku": "ACH-S-MC", "inventory": 10},
         {"title": "M / Multicolor", "price": "120.00", "sku": "ACH-M-MC", "inventory": 15},
         {"title": "L / Multicolor", "price": "120.00", "sku": "ACH-L-MC", "inventory": 8},
     ]},
    {"title": "Embroidered Varsity Jacket", "type": "Outerwear", "vendor": "House Brand", "collection": "Limited Edition",
     "variants": [
         {"title": "S / Black-Gold", "price": "185.00", "sku": "EVJ-S-BG", "inventory": 5},
         {"title": "M / Black-Gold", "price": "185.00", "sku": "EVJ-M-BG", "inventory": 8},
         {"title": "L / Black-Gold", "price": "185.00", "sku": "EVJ-L-BG", "inventory": 3},
     ]},
    {"title": "Numbered Print Tee (1/100)", "type": "T-Shirts", "vendor": "House Brand", "collection": "Limited Edition",
     "variants": [
         {"title": "M / White", "price": "55.00", "sku": "NPT-M-WHT", "inventory": 12},
         {"title": "L / White", "price": "55.00", "sku": "NPT-L-WHT", "inventory": 8},
     ]},
    {"title": "Heritage Leather Wallet", "type": "Accessories", "vendor": "House Brand", "collection": "Limited Edition",
     "variants": [
         {"title": "One Size / Tan", "price": "89.00", "sku": "HLW-OS-TAN", "inventory": 20},
         {"title": "One Size / Black", "price": "89.00", "sku": "HLW-OS-BLK", "inventory": 25},
     ]},
    {"title": "Premium Scented Candle Set", "type": "Home", "vendor": "House Brand", "collection": "Limited Edition",
     "variants": [
         {"title": "3-Pack / Cedar-Amber-Sage", "price": "48.00", "sku": "PSC-3P-CAS", "inventory": 40},
     ]},
]

DISCOUNT_CODES = [
    {"code": "WELCOME10", "percentage": 10},
    {"code": "FLASH20", "percentage": 20},
    {"code": "VIP30", "percentage": 30},
    {"code": "HACK15", "percentage": 15},
    {"code": "SAVE25", "percentage": 25},
    {"code": "FIRST10", "percentage": 10},
    {"code": "SUMMER15", "percentage": 15},
    {"code": "LOYALTY20", "percentage": 20},
    {"code": "DEMO25", "percentage": 25},
    {"code": "BETA50", "percentage": 50},
]

CUSTOMERS = [
    {"first_name": "Emma", "last_name": "Wilson", "email": "emma.wilson@example.com", "tags": ["vip", "repeat"]},
    {"first_name": "James", "last_name": "Chen", "email": "james.chen@test.io", "tags": ["new"]},
    {"first_name": "Sofia", "last_name": "Martinez", "email": "sofia.m@demo.org", "tags": ["vip"]},
    {"first_name": "Liam", "last_name": "O'Brien", "email": "liam.obrien@example.com", "tags": ["repeat"]},
    {"first_name": "Ava", "last_name": "Johnson", "email": "ava.j@test.io", "tags": ["new"]},
    {"first_name": "Noah", "last_name": "Kim", "email": "noah.kim@demo.org", "tags": ["repeat", "vip"]},
    {"first_name": "Mia", "last_name": "Anderson", "email": "mia.a@example.com", "tags": []},
    {"first_name": "Oliver", "last_name": "Davis", "email": "oliver.d@test.io", "tags": ["new"]},
    {"first_name": "Isabella", "last_name": "Garcia", "email": "isabella.g@demo.org", "tags": ["vip"]},
    {"first_name": "Ethan", "last_name": "Brown", "email": "ethan.b@example.com", "tags": ["repeat"]},
    {"first_name": "Charlotte", "last_name": "Lee", "email": "charlotte.lee@test.io", "tags": []},
    {"first_name": "Lucas", "last_name": "Taylor", "email": "lucas.t@demo.org", "tags": ["new"]},
    {"first_name": "Harper", "last_name": "White", "email": "harper.w@example.com", "tags": ["repeat"]},
    {"first_name": "Mason", "last_name": "Harris", "email": "mason.h@test.io", "tags": ["vip", "repeat"]},
    {"first_name": "Aria", "last_name": "Clark", "email": "aria.c@demo.org", "tags": []},
    {"first_name": "Logan", "last_name": "Lewis", "email": "logan.l@example.com", "tags": ["new"]},
    {"first_name": "Ella", "last_name": "Walker", "email": "ella.w@test.io", "tags": ["repeat"]},
    {"first_name": "Alexander", "last_name": "Hall", "email": "alex.h@demo.org", "tags": ["vip"]},
    {"first_name": "Luna", "last_name": "Allen", "email": "luna.a@example.com", "tags": []},
    {"first_name": "Benjamin", "last_name": "Young", "email": "ben.y@test.io", "tags": ["new"]},
    {"first_name": "Chloe", "last_name": "King", "email": "chloe.k@demo.org", "tags": ["repeat"]},
    {"first_name": "Daniel", "last_name": "Wright", "email": "daniel.w@example.com", "tags": []},
    {"first_name": "Scarlett", "last_name": "Lopez", "email": "scarlett.l@test.io", "tags": ["vip"]},
    {"first_name": "Jack", "last_name": "Hill", "email": "jack.h@demo.org", "tags": ["new", "repeat"]},
    {"first_name": "Lily", "last_name": "Scott", "email": "lily.s@example.com", "tags": []},
    {"first_name": "Henry", "last_name": "Green", "email": "henry.g@test.io", "tags": ["repeat"]},
    {"first_name": "Zoe", "last_name": "Adams", "email": "zoe.a@demo.org", "tags": ["vip"]},
    {"first_name": "Sebastian", "last_name": "Baker", "email": "seb.b@example.com", "tags": []},
    {"first_name": "Grace", "last_name": "Rivera", "email": "grace.r@test.io", "tags": ["new"]},
    {"first_name": "Owen", "last_name": "Campbell", "email": "owen.c@demo.org", "tags": ["repeat"]},
]


class ShopifySeeder:
    """Seeds a Shopify dev store with curated catalog data."""

    def __init__(self, store_url: str, access_token: str, api_version: str = "2025-01"):
        self.base_url = f"https://{store_url}/admin/api/{api_version}"
        self.headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(timeout=30.0)

    async def rest(self, method: str, path: str, json_data: dict = None) -> dict:
        url = f"{self.base_url}/{path.lstrip('/')}"
        resp = await self.client.request(method, url, json=json_data, headers=self.headers)
        if resp.status_code == 429:
            retry_after = float(resp.headers.get("Retry-After", "2"))
            logger.warning("Rate limited, waiting %.1fs...", retry_after)
            await asyncio.sleep(retry_after)
            resp = await self.client.request(method, url, json=json_data, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    async def seed_collections(self) -> dict:
        mapping = {}
        for col in COLLECTIONS:
            try:
                result = await self.rest("POST", "custom_collections.json", {
                    "custom_collection": {"title": col["title"], "handle": col["handle"], "published": True}
                })
                cid = result["custom_collection"]["id"]
                mapping[col["title"]] = cid
                logger.info("Created collection: %s (id=%d)", col["title"], cid)
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.warning("Collection '%s' may already exist: %s", col["title"], e)
        return mapping

    async def seed_products(self, collection_map: dict) -> list:
        product_ids = []
        for prod in PRODUCTS:
            try:
                variants = []
                for v in prod["variants"]:
                    parts = v["title"].split(" / ")
                    vd = {"title": v["title"], "price": v["price"], "sku": v["sku"],
                          "inventory_management": "shopify", "inventory_quantity": v["inventory"]}
                    if len(parts) >= 1: vd["option1"] = parts[0]
                    if len(parts) >= 2: vd["option2"] = parts[1]
                    variants.append(vd)

                result = await self.rest("POST", "products.json", {
                    "product": {"title": prod["title"], "product_type": prod["type"],
                                "vendor": prod["vendor"], "status": "active", "variants": variants}
                })
                pid = result["product"]["id"]
                product_ids.append(pid)
                logger.info("Created product: %s (id=%d)", prod["title"], pid)

                col_title = prod["collection"]
                if col_title in collection_map:
                    try:
                        await self.rest("POST", "collects.json", {
                            "collect": {"product_id": pid, "collection_id": collection_map[col_title]}
                        })
                    except Exception:
                        pass
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error("Failed to create product '%s': %s", prod["title"], e)
        return product_ids

    async def seed_customers(self) -> int:
        count = 0
        for cust in CUSTOMERS:
            try:
                await self.rest("POST", "customers.json", {
                    "customer": {"first_name": cust["first_name"], "last_name": cust["last_name"],
                                 "email": cust["email"],
                                 "tags": ", ".join(cust["tags"]) if cust["tags"] else "",
                                 "verified_email": True, "send_email_welcome": False}
                })
                count += 1
                await asyncio.sleep(0.3)
            except Exception as e:
                logger.warning("Customer '%s' may exist: %s", cust["email"], e)
        logger.info("Created %d customers", count)
        return count

    async def seed_discounts(self) -> int:
        count = 0
        for disc in DISCOUNT_CODES:
            try:
                pr = await self.rest("POST", "price_rules.json", {
                    "price_rule": {"title": disc["code"], "target_type": "line_item",
                                   "target_selection": "all", "allocation_method": "across",
                                   "value_type": "percentage", "value": f"-{disc['percentage']}",
                                   "customer_selection": "all", "starts_at": "2024-01-01T00:00:00Z"}
                })
                pr_id = pr["price_rule"]["id"]
                await self.rest("POST", f"price_rules/{pr_id}/discount_codes.json", {
                    "discount_code": {"code": disc["code"]}
                })
                count += 1
                logger.info("Created discount: %s (%d%%)", disc["code"], disc["percentage"])
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.warning("Discount '%s' may exist: %s", disc["code"], e)
        return count

    async def close(self):
        await self.client.aclose()


async def seed_store(store_url: str, access_token: str):
    logger.info("Seeding store: %s", store_url)
    seeder = ShopifySeeder(store_url, access_token)
    try:
        collections = await seeder.seed_collections()
        logger.info("Collections: %d created", len(collections))
        products = await seeder.seed_products(collections)
        logger.info("Products: %d created", len(products))
        customers = await seeder.seed_customers()
        logger.info("Customers: %d created", customers)
        discounts = await seeder.seed_discounts()
        logger.info("Discounts: %d created", discounts)
        logger.info("Seeding complete for %s!", store_url)
    finally:
        await seeder.close()


async def seed_all(tokens_path: str):
    with open(tokens_path) as f:
        tokens = json.load(f)
    for name, info in tokens.items():
        logger.info("--- Seeding %s (%s) ---", name, info["store"])
        await seed_store(info["store"], info["access_token"])
        logger.info("--- Done: %s ---\n", name)


def main():
    parser = argparse.ArgumentParser(description="Seed Shopify dev stores")
    parser.add_argument("--store", help="Store URL")
    parser.add_argument("--token", help="Access token")
    parser.add_argument("--tokens", help="Path to tokens.json")
    parser.add_argument("--all", action="store_true", help="Seed all stores")
    args = parser.parse_args()

    if args.tokens and args.all:
        asyncio.run(seed_all(args.tokens))
    elif args.store and args.token:
        asyncio.run(seed_store(args.store, args.token))
    else:
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()
        store_url = os.getenv("SHOPIFY_STORE_URL")
        access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
        if not store_url or not access_token:
            print("Error: Set SHOPIFY_STORE_URL and SHOPIFY_ACCESS_TOKEN in .env, or use --store/--token flags")
            sys.exit(1)
        asyncio.run(seed_store(store_url, access_token))


if __name__ == "__main__":
    main()
