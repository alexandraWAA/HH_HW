"""Модуль для создания базы данных и таблиц."""

import psycopg2
from psycopg2.extensions import connection
from typing import Optional
from config import Config


def create_database() -> None:
    """Создает базу данных, если она не существует."""
    params = Config.get_db_connection_params()
    db_name = params.pop('dbname')

    # Подключаемся к базе postgres для создания новой БД
    conn = None
    try:
        conn = psycopg2.connect(**params)
        conn.autocommit = True
        cursor = conn.cursor()

        # Проверяем существование базы данных
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE {db_name}")
            print(f"База данных {db_name} создана")
        else:
            print(f"База данных {db_name} уже существует")

    except psycopg2.Error as e:
        print(f"Ошибка при создании базы данных: {e}")
    finally:
        if conn:
            conn.close()


def create_tables(conn: connection) -> None:
    """
    Создает таблицы в базе данных.

    Args:
        conn: Подключение к базе данных
    """
    with conn.cursor() as cur:
        # Создание таблицы компаний
        cur.execute("""
            CREATE TABLE IF NOT EXISTS employers (
                employer_id INTEGER PRIMARY KEY,
                employer_name VARCHAR(255) NOT NULL,
                employer_url VARCHAR(500),
                description TEXT,
                site_url VARCHAR(500),
                area VARCHAR(100)
            )
        """)

        # Создание таблицы вакансий
        cur.execute("""
            CREATE TABLE IF NOT EXISTS vacancies (
                vacancy_id INTEGER PRIMARY KEY,
                employer_id INTEGER REFERENCES employers(employer_id) ON DELETE CASCADE,
                vacancy_name VARCHAR(500) NOT NULL,
                salary_from INTEGER,
                salary_to INTEGER,
                salary_currency VARCHAR(3),
                url VARCHAR(500),
                requirement TEXT,
                responsibility TEXT
            )
        """)

        # Создание индексов для ускорения запросов
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_vacancies_employer 
            ON vacancies(employer_id)
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_vacancies_name 
            ON vacancies(vacancy_name)
        """)

        conn.commit()
        print("Таблицы успешно созданы")


def save_employers(conn: connection, employers_data: list) -> None:
    """
    Сохраняет данные о работодателях в базу данных.

    Args:
        conn: Подключение к базе данных
        employers_data: Список словарей с данными о работодателях
    """
    with conn.cursor() as cur:
        for employer in employers_data:
            cur.execute("""
                INSERT INTO employers (employer_id, employer_name, employer_url, 
                                       description, site_url, area)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (employer_id) DO UPDATE SET
                    employer_name = EXCLUDED.employer_name,
                    employer_url = EXCLUDED.employer_url,
                    description = EXCLUDED.description,
                    site_url = EXCLUDED.site_url,
                    area = EXCLUDED.area
            """, (
                employer['employer_id'],
                employer['employer_name'],
                employer.get('employer_url'),
                employer.get('description'),
                employer.get('site_url'),
                employer.get('area')
            ))
        conn.commit()
        print(f"Сохранено {len(employers_data)} работодателей")


def save_vacancies(conn: connection, vacancies_data: list) -> None:
    """
    Сохраняет данные о вакансиях в базу данных.

    Args:
        conn: Подключение к базе данных
        vacancies_data: Список словарей с данными о вакансиях
    """
    with conn.cursor() as cur:
        for vacancy in vacancies_data:
            cur.execute("""
                INSERT INTO vacancies (vacancy_id, employer_id, vacancy_name, 
                                       salary_from, salary_to, salary_currency, 
                                       url, requirement, responsibility)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (vacancy_id) DO UPDATE SET
                    vacancy_name = EXCLUDED.vacancy_name,
                    salary_from = EXCLUDED.salary_from,
                    salary_to = EXCLUDED.salary_to,
                    salary_currency = EXCLUDED.salary_currency,
                    url = EXCLUDED.url,
                    requirement = EXCLUDED.requirement,
                    responsibility = EXCLUDED.responsibility
            """, (
                vacancy['vacancy_id'],
                vacancy['employer_id'],
                vacancy['vacancy_name'],
                vacancy.get('salary_from'),
                vacancy.get('salary_to'),
                vacancy.get('salary_currency'),
                vacancy.get('url'),
                vacancy.get('requirement'),
                vacancy.get('responsibility')
            ))
        conn.commit()
        print(f"Сохранено {len(vacancies_data)} вакансий")