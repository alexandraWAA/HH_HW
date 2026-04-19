"""Модуль с классом DBManager для работы с базой данных."""

import psycopg2
from typing import List, Tuple, Dict, Any, Optional
from config import Config


class DBManager:
    """Класс для управления данными в базе данных."""

    def __init__(self):
        """Инициализация подключения к базе данных."""
        self.conn = None
        self.connect()

    def connect(self) -> None:
        """Устанавливает соединение с базой данных."""
        params = Config.get_db_connection_params()
        try:
            self.conn = psycopg2.connect(**params)
            print("Подключение к базе данных установлено")
        except psycopg2.Error as e:
            print(f"Ошибка подключения к базе данных: {e}")
            raise

    def close(self) -> None:
        """Закрывает соединение с базой данных."""
        if self.conn:
            self.conn.close()
            print("Соединение с базой данных закрыто")

    def __enter__(self):
        """Контекстный менеджер для автоматического закрытия соединения."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Закрывает соединение при выходе из контекста."""
        self.close()

    def get_companies_and_vacancies_count(self) -> List[Tuple[str, int]]:
        """
        Получает список всех компаний и количество вакансий у каждой компании.

        Returns:
            Список кортежей (название_компании, количество_вакансий)
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT e.employer_name, COUNT(v.vacancy_id) as vacancies_count
                FROM employers e
                LEFT JOIN vacancies v ON e.employer_id = v.employer_id
                GROUP BY e.employer_id, e.employer_name
                ORDER BY vacancies_count DESC
            """)
            return cur.fetchall()

    def get_all_vacancies(self) -> List[Tuple[str, str, str, str, Optional[str]]]:
        """
        Получает список всех вакансий.

        Returns:
            Список кортежей (название_компании, название_вакансии,
                           зарплата, ссылка, валюта)
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT e.employer_name, v.vacancy_name,
                       COALESCE(v.salary_from, v.salary_to) as salary,
                       v.url, v.salary_currency
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.employer_id
                ORDER BY e.employer_name, v.vacancy_name
            """)
            return cur.fetchall()

    def get_avg_salary(self) -> float:
        """
        Получает среднюю зарплату по вакансиям.

        Returns:
            Средняя зарплата (среднее от salary_from и salary_to)
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT AVG(
                    CASE 
                        WHEN salary_from IS NOT NULL AND salary_to IS NOT NULL 
                        THEN (salary_from + salary_to) / 2.0
                        WHEN salary_from IS NOT NULL THEN salary_from
                        WHEN salary_to IS NOT NULL THEN salary_to
                        ELSE NULL
                    END
                ) as avg_salary
                FROM vacancies
                WHERE salary_from IS NOT NULL OR salary_to IS NOT NULL
            """)
            result = cur.fetchone()[0]
            return round(result, 2) if result else 0

    def get_vacancies_with_higher_salary(self) -> List[Tuple[str, str, str, str, Optional[str]]]:
        """
        Получает список вакансий с зарплатой выше средней.

        Returns:
            Список вакансий с зарплатой выше средней
        """
        avg_salary = self.get_avg_salary()

        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT e.employer_name, v.vacancy_name,
                       COALESCE(v.salary_from, v.salary_to) as salary,
                       v.url, v.salary_currency
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.employer_id
                WHERE (v.salary_from > %s OR v.salary_to > %s)
                ORDER BY salary DESC
            """, (avg_salary, avg_salary))
            return cur.fetchall()

    def get_vacancies_with_keyword(self, keyword: str) -> List[Tuple[str, str, str, str, Optional[str]]]:
        """
        Получает список вакансий, содержащих ключевое слово в названии.

        Args:
            keyword: Ключевое слово для поиска

        Returns:
            Список вакансий, содержащих ключевое слово
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT e.employer_name, v.vacancy_name,
                       COALESCE(v.salary_from, v.salary_to) as salary,
                       v.url, v.salary_currency
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.employer_id
                WHERE v.vacancy_name ILIKE %s
                ORDER BY e.employer_name, v.vacancy_name
            """, (f'%{keyword}%',))
            return cur.fetchall()