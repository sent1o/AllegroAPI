from core_mapper import core_parser
from auth import launch
from horoshop_exporter import data_parser
from config import RAW_DATA_FILE
import traceback
import os

if __name__ == "__main__":
    if os.path.exists(RAW_DATA_FILE):
        os.remove(RAW_DATA_FILE)

    try:
        print("Старт системи: запускаємо зв'язок з Алегро...")
        raw_data = launch()

        if raw_data is not None:
            if len(raw_data) == 0:
                print("Hа акаунті 0 товарів! Експортувати нічого.")
            else:
                print("Дані отримано. Оновлюємо КОР-базу...")
                core_parser(raw_data)
                data_parser()
        else:
            print("❌ Помилка АПІ. Перевірте .env файл.")

    except Exception as e:
        print(f"\n!!!КРИТИЧНА ПОМИЛКА: {e}")
        traceback.print_exc()

    finally:
        if os.path.exists(RAW_DATA_FILE):
            try:
                os.remove(RAW_DATA_FILE)
            except Exception as e:
                print(f"Не вдалося видалити тимчасовий файл {RAW_DATA_FILE}")
                print(f"Помилка: {e}")
                print(f"Якщо можливо - видаліть файл вручну")

        input("\nНатисніть Enter для виходу... ")
