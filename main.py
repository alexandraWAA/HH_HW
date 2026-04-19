"""Основной модуль для запуска парсера вакансий hh.ru."""

import sys
from typing import Dict, Any
from src.hh_api import HHAPI
from src.db_utils import create_database, create_tables, save_employers, save_vacancies
from src.db_manager import DBManager
from config import Config
import psycopg2


def parse_employers_data(api_data: Dict[int, Dict[str, Any]]) -> list:
    """
    Преобразует данные из API в формат для сохранения в БД.

    Args:
        api_data: Данные от API hh.ru

    Returns:
        Список словарей с данными о работодателях
    """
    employers = []

    for employer_id, data in api_data.items():
        employer_info = data['employer']
        employers.append({
            'employer_id': employer_id,
            'employer_name': employer_info.get('name', ''),
            'employer_url': employer_info.get('url', ''),
            'description': employer_info.get('description', ''),
            'site_url': employer_info.get('site_url', ''),
            'area': employer_info.get('area', {}).get('name', '')
        })

    return employers


def parse_vacancies_data(api_data: Dict[int, Dict[str, Any]]) -> list:
    """
    Преобразует данные о вакансиях из API в формат для сохранения в БД.

    Args:
        api_data: Данные от API hh.ru

    Returns:
        Список словарей с данными о вакансиях
    """
    vacancies = []
    for employer_id, data in api_data.items():
        for vacancy in data['vacancies']:
            salary = vacancy.get('salary', {})

            vacancies.append({
                'vacancy_id': vacancy.get('id'),
                'employer_id': employer_id,
                'vacancy_name': vacancy.get('name', ''),
                'salary_from': salary.get('from') if salary else None,
                'salary_to': salary.get('to') if salary else None,
                'salary_currency': salary.get('currency') if salary else None,
                'url': vacancy.get('alternate_url', ''),
                'requirement': vacancy.get('snippet', {}).get('requirement', ''),
                'responsibility': vacancy.get('snippet', {}).get('responsibility', '')
            })

    return vacancies


def main_menu():
    """Отображает главное меню и обрабатывает выбор пользователя."""

    # Проверка подключения к PostgreSQL
    import psycopg2
    from config import Config

    try:
        test_conn = psycopg2.connect(**Config.get_db_connection_params())
        test_conn.close()
        print("✓ Подключение к PostgreSQL успешно")
    except psycopg2.Error as e:
        print(f"✗ Ошибка подключения к PostgreSQL: {e}")
        print("Проверьте:")
        print("  1. Запущен ли PostgreSQL (служба)")
        print("  2. Пароль в файле .env")
        print("  3. Имя базы данных (должна существовать или будет создана)")
        return

    print("\n" + "=" * 60)
    print("ПАРСЕР ВАКАНСИЙ HH.RU")
    print("=" * 60)

    print("\n" + "=" * 60)
    print("ПАРСЕР ВАКАНСИЙ HH.RU")
    print("=" * 60)

    # Шаг 1: Создание базы данных и таблиц
    print("\n1. Инициализация базы данных...")
    create_database()

    # Подключение к БД для создания таблиц
    params = Config.get_db_connection_params()
    conn = None
    try:
        conn = psycopg2.connect(**params)
        create_tables(conn)
    except psycopg2.Error as e:
        print(f"Ошибка при работе с БД: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()

    # Шаг 2: Получение данных из API
    print("\n2. Получение данных из API hh.ru...")
    api = HHAPI()
    employers_data_raw = api.get_employers_with_vacancies(Config.EMPLOYERS)

    # Шаг 3: Преобразование и сохранение данных
    print("\n3. Сохранение данных в базу данных...")

    employers_list = parse_employers_data(employers_data_raw)
    vacancies_list = parse_vacancies_data(employers_data_raw)

    params = Config.get_db_connection_params()
    conn = None
    try:
        conn = psycopg2.connect(**params)
        save_employers(conn, employers_list)
        save_vacancies(conn, vacancies_list)
    except psycopg2.Error as e:
        print(f"Ошибка при сохранении данных: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()

    print(f"\nЗагрузка завершена!")
    print(f"Сохранено компаний: {len(employers_list)}")
    print(f"Сохранено вакансий: {len(vacancies_list)}")

    # Шаг 4: Взаимодействие с пользователем через DBManager
    while True:
        print("\n" + "=" * 60)
        print("МЕНЮ РАБОТЫ С ДАННЫМИ")
        print("=" * 60)
        print("1. Список компаний и количество вакансий")
        print("2. Список всех вакансий")
        print("3. Средняя зарплата по всем вакансиям")
        print("4. Вакансии с зарплатой выше средней")
        print("5. Поиск вакансий по ключевому слову")
        print("0. Выход")
        print("-" * 60)

        choice = input("Выберите действие (0-5): ").strip()

        with DBManager() as db:
            if choice == '1':
                print("\n" + "=" * 60)
                print("КОМПАНИИ И КОЛИЧЕСТВО ВАКАНСИЙ")
                print("=" * 60)
                results = db.get_companies_and_vacancies_count()
                for company, count in results:
                    print(f"  • {company}: {count} вакансий")

            elif choice == '2':
                print("\n" + "=" * 60)
                print("ВСЕ ВАКАНСИИ")
                print("=" * 60)
                results = db.get_all_vacancies()
                for company, title, salary, url, currency in results:
                    salary_str = f"{salary} {currency}" if salary and currency else "Зарплата не указана"
                    print(f"\n  Компания: {company}")
                    print(f"  Вакансия: {title}")
                    print(f"  Зарплата: {salary_str}")
                    print(f"  Ссылка: {url}")
                    print("-" * 40)

            elif choice == '3':
                print("\n" + "=" * 60)
                print("СРЕДНЯЯ ЗАРПЛАТА")
                print("=" * 60)
                avg_salary = db.get_avg_salary()
                print(f"  Средняя зарплата по всем вакансиям: {avg_salary} руб.")

            elif choice == '4':
                print("\n" + "=" * 60)
                print("ВАКАНСИИ С ЗАРПЛАТОЙ ВЫШЕ СРЕДНЕЙ")
                print("=" * 60)
                results = db.get_vacancies_with_higher_salary()
                for company, title, salary, url, currency in results:
                    salary_str = f"{salary} {currency}" if salary and currency else "Зарплата не указана"
                    print(f"\n  Компания: {company}")
                    print(f"  Вакансия: {title}")
                    print(f"  Зарплата: {salary_str}")
                    print(f"  Ссылка: {url}")
                    print("-" * 40)

            elif choice == '5':
                keyword = input("\nВведите ключевое слово для поиска: ").strip()
                print("\n" + "=" * 60)
                print(f"ВАКАНСИИ, СОДЕРЖАЩИЕ '{keyword}'")
                print("=" * 60)
                results = db.get_vacancies_with_keyword(keyword)
                if results:
                    for company, title, salary, url, currency in results:
                        salary_str = f"{salary} {currency}" if salary and currency else "Зарплата не указана"
                        print(f"\n  Компания: {company}")
                        print(f"  Вакансия: {title}")
                        print(f"  Зарплата: {salary_str}")
                        print(f"  Ссылка: {url}")
                        print("-" * 40)
                else:
                    print(f"  Вакансии с ключевым словом '{keyword}' не найдены")

            elif choice == '0':
                print("\nДо свидания!")
                break
            else:
                print("\nНеверный выбор. Пожалуйста, выберите число от 0 до 5.")


if __name__ == "__main__":
    main_menu()