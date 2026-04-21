import json
import os
import pandas as pd
from datetime import datetime
from config import CORE_PATH, BASE_DIR


def data_parser():
    if os.path.exists(CORE_PATH):
        print("Формуємо Excel-файл для Хорошопу...")
        with open(CORE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

            xlsx_prepare = []

            for item in data:
                stock_count = item.get("remainder")
                if stock_count and int(stock_count) > 0:
                    remainder = "Dostępny"
                else:
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
                            images_row = ";".join(img_list)
                    except json.JSONDecodeError:
                        pass

                params = item.get("parameters", [])
                ean = get_param_value(params, "EAN")
                signature = item.get("allegro_signature")
                artikul = ean if ean else signature

                template = {
                    "Артикул": artikul,
                    "Родительский артикул": artikul,
                    "Штрихкод": ean,
                    "Код производителя товара (MPN)": signature,
                    "Название (PL)": item.get("name"),
                    "Бренд": get_param_value(params, "Marka"),
                    "Раздел": "Nowości",
                    "Цена": item.get("price"),
                    "Старая цена": "0.00",
                    "Валюта": item.get("currency"),
                    "Отображать": "Да",
                    "Наличие": remainder,
                    "Фото": images_row,
                    "Алиас": "",
                    "Ссылка": "",
                    "Дата добавления": item.get("createdAt"),
                    "Скидка %": "0",
                    "Популярность": "0",
                    "Количество": item.get("remainder"),
                    "Описание товара (PL)": parse_allegro_description(
                        item.get("description")
                    ),
                    "Цвет": get_param_value(params, "Kolor"),
                    "Гарантийный срок, мес.": "0",
                    "Дата и время окончания акции": item.get("createdAt"),
                    "Только для взрослых": "Нет",
                    "Срок доставки предзаказа в днях": "0",
                    "«Оплата частями» ПриватБанка": "Выкл",
                    "«Покупка частями» от monobank": "Выкл",
                    "На складе для Prom": "Нет",
                    "Электронный товар": "Нет",
                }
                xlsx_prepare.append(template)

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
        return True
    else:
        print("Файл CORE не знайдено")
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
