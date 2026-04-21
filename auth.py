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


def get_offers(access_token):
    url = "https://api.allegro.pl/sale/offers"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.allegro.public.v1+json",
        "User-Agent": "AllegroTo-offers/1.0.0",
    }
    all_offers = []
    limit = 100
    offset = 0
    total_count = None

    while True:
        params = {"limit": limit, "offset": offset}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()

                if total_count is None:
                    total_count = data.get("count", 0)
                    print(f"📦 Всього товарів до завантаження: {total_count}")

                offers = data.get("offers", [])
                if not offers:
                    break

                all_offers.extend(offers)

                save_raw_api_response({"offers": all_offers, "status": "partial"})

                print(f"✅ Отримано пачку: {offset} - {offset + len(offers)}...")

                offset += limit
                if len(all_offers) >= total_count:
                    break

                time.sleep(0.5)

            elif response.status_code == 401:
                return {"status": 401, "data": all_offers}

            else:
                print(f"❌ Помилка API: {response.status_code}, {response.text}")
                break

        except Exception as e:
            print(f"💥 Критична помилка мережі: {e}")
            break

    return {"status": 200, "data": all_offers}


def save_raw_api_response(data, filename=RAW_DATA_FILE):
    """Зберігає отримані дані в JSON-файл для подальшого аналізу."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ Сирі дані успішно збережені у файл: {filename}")
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
