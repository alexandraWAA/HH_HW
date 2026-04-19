"""Модуль для взаимодействия с API hh.ru."""

import time
from typing import List, Dict, Any, Optional
import requests


class HHAPI:
    """Класс для работы с API HeadHunter."""

    def __init__(self, base_url: str = 'https://api.hh.ru'):
        """
        Инициализация API клиента.

        Args:
            base_url: Базовый URL API hh.ru
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HH-API-Parser/1.0'
        })

    def get_employer(self, employer_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о работодателе по ID.

        Args:
            employer_id: ID работодателя

        Returns:
            Словарь с данными о работодателе или None при ошибке
        """
        try:
            url = f"{self.base_url}/employers/{employer_id}"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Ошибка при получении работодателя {employer_id}: {e}")
            return None

    def get_vacancies_by_employer(self, employer_id: int, per_page: int = 100) -> List[Dict[str, Any]]:
        """
        Получает вакансии работодателя.

        Args:
            employer_id: ID работодателя
            per_page: Количество вакансий на странице

        Returns:
            Список вакансий
        """
        vacancies = []
        page = 0

        try:
            while True:
                url = f"{self.base_url}/vacancies"
                params = {
                    'employer_id': employer_id,
                    'per_page': per_page,
                    'page': page,
                    'only_with_salary': False
                }

                response = self.session.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                vacancies.extend(data.get('items', []))

                if page >= data.get('pages', 1) - 1:
                    break

                page += 1
                time.sleep(0.1)  # Задержка для соблюдения лимитов API

        except requests.RequestException as e:
            print(f"Ошибка при получении вакансий для {employer_id}: {e}")

        return vacancies

    def get_employers_with_vacancies(self, employer_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        Получает данные о работодателях и их вакансиях.

        Args:
            employer_ids: Список ID работодателей

        Returns:
            Словарь с данными о работодателях и их вакансиях
        """
        result = {}

        for employer_id in employer_ids:
            print(f"Обработка работодателя {employer_id}...")

            employer_data = self.get_employer(employer_id)
            if employer_data:
                vacancies = self.get_vacancies_by_employer(employer_id)
                result[employer_id] = {
                    'employer': employer_data,
                    'vacancies': vacancies
                }
                print(f"  Получено {len(vacancies)} вакансий")
            else:
                print(f"  Не удалось получить данные о работодателе {employer_id}")

            time.sleep(0.2)

        return result