#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для установки зависимостей
"""
import subprocess
import sys
import os


def install_packages():
    """Устанавливает необходимые пакеты"""
    packages = [
        "selenium==4.15.0",
        "webdriver-manager==4.0.1",
        "curl-cffi==0.5.10",
        "beautifulsoup4==4.12.2",
        "pandas==2.1.0",
        "openpyxl==3.1.2",
        "schedule==1.2.0",
        "colorama==0.4.6",
        "lxml==4.9.3",
        "requests==2.31.0",
    ]

    print("Установка зависимостей...")

    for package in packages:
        print(f"Установка {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ {package} установлен")
        except subprocess.CalledProcessError as e:
            print(f"✗ Ошибка при установке {package}: {e}")

    print("\nВсе зависимости установлены!")


def check_google_chrome():
    """Проверяет наличие Google Chrome"""
    print("\nПроверка наличия Google Chrome...")

    chrome_paths = [
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe"),
    ]

    chrome_found = False
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✓ Google Chrome найден: {path}")
            chrome_found = True
            break

    if not chrome_found:
        print("✗ Google Chrome не найден!")
        print("Пожалуйста, установите Google Chrome:")
        print("https://www.google.com/chrome/")


if __name__ == "__main__":
    print("=" * 60)
    print("Установщик зависимостей для мониторинга цен Ozon")
    print("=" * 60)

    install_packages()
    check_google_chrome()

    print("\n" + "=" * 60)
    print("Установка завершена!")
    print("Для запуска программы выполните: python main.py")
    print("=" * 60)