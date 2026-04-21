import json
import os
from config import CORE_PATH


def core_parser(data):
    if isinstance(data, dict) and "offers" in data:
        data = data["offers"]
    elif isinstance(data, dict):
        data = [data]

    core_db = {}
    if os.path.exists(CORE_PATH):
        with open(CORE_PATH, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
                core_db = {item.get("allegro_id"): item for item in existing_data}
            except json.JSONDecodeError:
                pass

    list_offers = []
    for item in data:
        try:
            if not isinstance(item, dict):
                continue
            duplicate = item.get("id")
            if duplicate in core_db:
                core_db[duplicate]["remainder"] = item.get("stock", {}).get("available")
                core_db[duplicate]["price"] = (
                    item.get("sellingMode", {}).get("price", {}).get("amount")
                )
            else:
                selected = {
                    "allegro_signature": item.get("external", {}).get("id"),
                    "allegro_id": item.get("id"),
                    "name": item.get("name"),
                    "remainder": item.get("stock", {}).get("available"),
                    "price": item.get("sellingMode", {}).get("price", {}).get("amount"),
                    "currency": item.get("sellingMode", {})
                    .get("price", {})
                    .get("currency"),
                    "description": item.get("description", {}).get("sections"),
                    "parameters": item.get("parameters"),
                    "allegro_category": item.get("category", {}).get("id"),
                    "stock_status": item.get("publication", {}).get("status"),
                    "price_for_other_countries": item.get(
                        "additionalMarketplaces", {}
                    ).get("allegro-cz"),
                    "b2b": item.get("b2b", {}).get("buyableOnlyByBusiness"),
                    "VAT": item.get("taxSettings", {}).get("rates"),
                    "contact": item.get("contact"),
                    "attachments": item.get("attachments"),
                    "images": item.get("images"),
                    "language": item.get("language"),
                    "errors": item.get("validation"),
                    "discounts": item.get("discounts"),
                    "createdAt": item.get("createdAt"),
                    "updatedAt": item.get("updatedAt"),
                    "auctions": item.get("sellingMode"),
                    "location": item.get("location"),
                    "size": item.get("sizeTable", {}).get("id"),
                }
                core_db[duplicate] = selected
        except Exception as e:
            print(f"Error: {e}")

    if core_db:
        list_offers = list(core_db.values())

        with open(CORE_PATH, "w", encoding="utf-8") as f:
            json.dump(list_offers, f, ensure_ascii=False, indent=4)
    else:
        print("!Помилка на етапі маппінгу")


if __name__ == "__main__":
    core_parser()
