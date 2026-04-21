from core_mapper import core_parser
from auth import launch
from horoshop_exporter import data_parser
import traceback

if __name__ == "__main__":
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
                print("✅ Весь цикл успішно завершено!")
        else:
            print("❌ Помилка АПІ. Перевірте .env файл.")

    except Exception as e:
        print(f"\n!!!КРИТИЧНА ПОМИЛКА: {e}")
        traceback.print_exc()

    finally:
        input("\nНатисніть Enter для виходу... ")
