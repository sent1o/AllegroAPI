import json
import os
import pandas as pd
from datetime import datetime
from config import CORE_PATH, BASE_DIR


def data_parser():
    if not os.path.exists(CORE_PATH):
        print("! Помилка: Файл CORE не знайдено")
        return False

    print("Формуємо Excel-файл для Хорошопу...")

    try:
        with open(CORE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print("! Помилка: Файл CORE пошкоджений (невалідний JSON)")
        return False
    except Exception as e:
        print(f"! Помилка читання бази: {e}")
        return False

    xlsx_prepare = []

    for item in data:
        try:
            stock_count = item.get("remainder")

            try:
                if stock_count is not None and int(float(stock_count)) > 0:
                    remainder = "Dostępny"
                else:
                    remainder = "Niedostępny"
            except (ValueError, TypeError):
                remainder = "Niedostępny"

            images_row = ""
            arr_images = item.get("images")
            if arr_images:
                try:
                    if isinstance(arr_images, str):
                        img_list = json.loads(arr_images)
                    else:
                        img_list = arr_images

                    if img_list:
                        formatted_images = [f"{img}?.png" for img in img_list]
                        images_row = "; ".join(formatted_images)
                except json.JSONDecodeError:
                    pass

            params = item.get("parameters", [])

            ean = get_param_value(params, "EAN (GTIN)")
            if not ean:
                ean = get_param_value(params, "EAN")

            signature = item.get("allegro_signature") or ""
            allegro_id = str(item.get("allegro_id", ""))

            artikul = ean if ean else (signature if signature else allegro_id)

            template = {
                "Артикул": artikul,
                "Родительский артикул": artikul,
                "Штрихкод": ean,
                "Код производителя товара (MPN)": signature,
                "Название (PL)": item.get("name", ""),
                "Бренд": get_param_value(params, "Marka"),
                "Раздел": "Nowości",
                "Цена": item.get("price", ""),
                "Старая цена": "0.00",
                "Валюта": item.get("currency", "PLN"),
                "Отображать": "Да",
                "Наличие": remainder,
                "Фото": images_row,
                "Алиас": "",
                "Ссылка": "",
                "Дата добавления": item.get("createdAt", ""),
                "Скидка %": "0",
                "Популярность": "0",
                "Количество": stock_count if stock_count else "0",
                "Описание товара (PL)": parse_allegro_description(
                    item.get("description")
                ),
                "Цвет": get_param_value(params, "Kolor"),
                "Гарантийный срок, мес.": "0",
                "Дата и время окончания акции": item.get("createdAt", ""),
                "Только для взрослых": "Нет",
                "Срок доставки предзаказа в днях": "0",
                "«Оплата частями» ПриватБанка": "Выкл",
                "«Покупка частями» от monobank": "Выкл",
                "На складе для Prom": "Нет",
                "Электронный товар": "Нет",
            }
            xlsx_prepare.append(template)

        except:
            continue

    if not xlsx_prepare:
        print("! Помилка: Немає валідних товарів для експорту")
        return False

    try:
        for_record = pd.DataFrame(xlsx_prepare)
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_filename = os.path.join(BASE_DIR, f"horoshop_{current_time}.xlsx")

        with pd.ExcelWriter(export_filename, engine="xlsxwriter") as writer:
            for_record.to_excel(writer, index=False, sheet_name="Products")

            workbook = writer.book
            worksheet = writer.sheets["Products"]
            bold_format = workbook.add_format({"bold": True, "border": 1})
            for col_num, value in enumerate(for_record.columns.values):
                worksheet.write(0, col_num, value, bold_format)
            worksheet.set_column(0, len(for_record.columns) - 1, 20)

        print(f"✅ Готово! Файл збережено як: {export_filename}")
        return True

    except PermissionError:
        print(
            f"! Помилка: Немає прав на запис файлу {export_filename}. Закрий схожі файли."
        )
        return False
    except Exception as e:
        print(f"! Помилка при створенні Excel: {e}")
        return False


def get_param_value(params, name_to_find):
    if not params or not isinstance(params, list):
        return ""
    for p in params:
        if p.get("name") == name_to_find:
            values = p.get("values", [])
            return values[0] if values else ""
    return ""


def parse_allegro_description(sections):
    if not sections or not isinstance(sections, list):
        return ""

    html_parts = []
    for section in sections:
        items = section.get("items", [])
        for item in items:
            if item.get("type") == "TEXT":
                content = item.get("content", "")
                if content:
                    html_parts.append(content)

    return "".join(html_parts)


if __name__ == "__main__":
    data_parser()
