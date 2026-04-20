"""Модуль с конфигурационными параметрами."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Класс для хранения конфигураций."""

    DB_NAME: str = os.getenv('DB_NAME', 'hh_parser')
    DB_USER: str = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', 'postgres')
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: str = os.getenv('DB_PORT', '5432')

    HH_API_URL: str = 'https://api.hh.ru'
    EMPLOYERS: list = [
        1740,      # Яндекс
        3529,      # Сбер
        80,        # ВК
        78638,     # Тинькофф
        2381,      # Ozon
        39305,     # Wildberries
        15478,     # VK Tech
        3776,      # МТС
        41862,     # Авито
        1057,      # Kaspersky
    ]

    @classmethod
    def get_db_connection_params(cls) -> dict:
        """
        Возвращает параметры подключения к БД.

        Returns:
            Словарь с параметрами подключения
        """
        return {
            'dbname': cls.DB_NAME,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD,
            'host': cls.DB_HOST,
            'port': cls.DB_PORT
        }

    @classmethod
    def get_db_connection_params_without_db(cls) -> dict:
        """
        Возвращает параметры подключения к PostgreSQL серверу (без указания БД).

        Returns:
            Словарь с параметрами подключения
        """
        return {
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD,
            'host': cls.DB_HOST,
            'port': cls.DB_PORT
        }