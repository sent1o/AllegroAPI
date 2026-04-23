import requests
import os
import time
import json
from config import CLIENT_ID, CLIENT_SECRET, TOKEN_PATH, RAW_DATA_FILE
import base64


def get_tokens():
    print(
        "Потрібно оновити код. Використайте це посилання: https://allegro.pl/auth/oauth/authorize?response_type=code&client_id=862d358973144385b0983b6ee6460d2f&redirect_uri=http://localhost:8000&scope=allegro:api:sale:offers:read+allegro:api:orders:read"
    )
    temp_code = input("🔗 Встав новий код з браузера і натисни Enter: ").strip()
    data = {
        "grant_type": "authorization_code",
        "code": temp_code,
        "redirect_uri": "http://localhost:8000",
    }

    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_auth = base64.b64encode(auth_str.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    get_token_url = "https://allegro.pl/auth/oauth/token"
    response = requests.post(get_token_url, data=data, headers=headers)

    if response.status_code == 200:
        resp = response.json()
        save_tokens(resp)
        print("Отримано дані нових токенів!")
        return resp

    else:
        print(f"❌ Помилка авторизації: {response.status_code},{response.text}")
        return None


def save_tokens(token_data):
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        json.dump(token_data, f)


def refresh_access_token(refresh_token):
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_auth = base64.b64encode(auth_str.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "redirect_uri": "http://localhost:8000",
    }

    response = requests.post(
        "https://allegro.pl/auth/oauth/token", data=data, headers=headers
    )

    if response.status_code == 200:
        token_data = response.json()
        save_tokens(token_data)
        return token_data
    else:
        print(
            "❌ Не вдалося оновити токен. Можливо, термін refresh_token теж вичерпано."
        )
        return None


def token_out():
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("access_token"), data.get("refresh_token")
    else:
        print("Файл із токенами відсутній або пошкоджений!")
        return None, None


import time
import requests


def get_offers(access_token):
    url_list = "https://api.allegro.pl/sale/offers"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.allegro.public.v1+json",
        "User-Agent": "AllegroTo-offers/1.0.0",
    }

    all_offers = []
    limit = 100
    offset = 0
    total_count = None
    processed_count = 0

    while True:
        params = {"limit": limit, "offset": offset}
        try:
            response = requests.get(
                url_list, headers=headers, params=params, timeout=30
            )

            if response.status_code == 429:
                print("⚠️ Забагато запитів! Чекаємо 30 секунд...")
                time.sleep(30)
                continue

            if response.status_code == 200:
                data = response.json()
                if total_count is None:
                    total_count = data.get("totalCount", 0)
                    print(f"📦 Всього товарів у кабінеті: {total_count}")
                    print("Починаємо обробку... Це займе трохи часу!")

                batch_offers = data.get("offers", [])
                if not batch_offers:
                    break

                for i, short_offer in enumerate(batch_offers, 1):
                    offer_id = short_offer.get("id")
                    processed_count += 1

                    full_url = f"https://api.allegro.pl/sale/product-offers/{offer_id}"

                    try:
                        detail_res = requests.get(full_url, headers=headers, timeout=20)

                        if detail_res.status_code == 200:
                            full_data = detail_res.json()
                            all_offers.append(full_data)
                        elif detail_res.status_code == 429:
                            print("\n🔴 Ліміт вичерпано! Пауза 20 сек...")
                            time.sleep(20)
                            all_offers.append(short_offer)  # Щоб не загубити
                        else:
                            print(
                                f"\n❌ Помилка ID {offer_id}: {detail_res.status_code}"
                            )
                            all_offers.append(short_offer)

                        time.sleep(0.1)

                    except Exception as e:
                        print(f"\n💥 Помилка на товарі {offer_id}: {e}")
                        all_offers.append(short_offer)

                    if processed_count % 100 == 0 or processed_count == total_count:
                        percent = (
                            (processed_count / total_count) * 100 if total_count else 0
                        )
                        print(
                            f"⏳ Оброблено: {processed_count}/{total_count} ({percent:.1f}%)"
                        )

                save_raw_api_response({"offers": all_offers, "status": "partial"})

                offset += limit
                time.sleep(1)

            elif response.status_code == 401:
                print("\n⚠️ Токен недійсний!")
                return {"status": 401, "data": all_offers}
            else:
                print(f"\n❌ Помилка списку: {response.status_code}")
                break

        except Exception as e:
            print(f"\n!!!Критична помилка мережі: {e}")
            break

    print("\n✅ Завантаження даних завершено!")
    return {"status": 200, "data": all_offers}


def save_raw_api_response(data, filename=RAW_DATA_FILE):
    """Зберігає отримані дані в JSON-файл для подальшого аналізу."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ Не вдалося зберегти сирі дані: {e}")


def launch():
    access, refresh = token_out()
    if not access:
        get_tokens()
        access, refresh = token_out()
    if not access:
        print("Тимчасовий код недійсний, потрібен новий.")
        return
    offers_data = get_offers(access)

    if offers_data.get("status") == 401:
        refresh_access_token(refresh)
        access, refresh = token_out()
        offers_data = get_offers(access)

    if offers_data.get("status") == 200:
        save_raw_api_response(offers_data)
        return offers_data.get("data")
    else:
        print(f"Помилка: {offers_data.get('status')}")


if __name__ == "__main__":
    launch()
