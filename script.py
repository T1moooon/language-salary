import requests
import statistics
import time
import os
from dotenv import load_dotenv
from terminaltables import AsciiTable


HH_AREA = 1
HH_PERIOD = 30
HH_SALARY = 100
HH_PER_PAGE = 50
SJ_TOWN = 4
SJ_COUNT = 50


def predict_salary(salary_from, salary_to):
    """Рассчитывает среднюю зарплату"""
    if salary_from and salary_to:
        return int((salary_from + salary_to) / 2)
    elif salary_from:
        return int(salary_from * 1.2)
    elif salary_to:
        return int(salary_to * 0.8)
    return None


def fetch_vacancies_sj(programming_language, page, api_key_sj):
    """Получает вакансии с SuperJob"""
    url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {'X-Api-App-Id': api_key_sj}
    params = {
        'keywords': f'программист {programming_language}',
        'town': SJ_TOWN,
        'page': page,
        'count': SJ_COUNT,
    }
    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def predict_rub_salary_sj(programming_language, api_key_sj):
    """Зарплаты для SuperJob"""
    total_salaries = []
    page = 0
    vacancies_found = 0
    while True:
        vacancies = fetch_vacancies_sj(programming_language, page, api_key_sj)
        if not vacancies:
            break
        vacancies_found = vacancies.get('total', 0)
        for vacancy in vacancies.get('objects', []):
            salary = predict_salary(
                vacancy.get('payment_from'),
                vacancy.get('payment_to')
            )
            if salary:
                total_salaries.append(salary)
        if not vacancies.get('more', False):
            break
        page += 1
        time.sleep(0.5)
    vacancies_processed = len(total_salaries)
    avg_salary = int(statistics.mean(total_salaries)) if total_salaries else 0
    return avg_salary, vacancies_found, vacancies_processed


def fetch_vacancies_hh(programming_language, page):
    """Получает вакансии с HeadHunter"""
    params = {
        'text': f'программист {programming_language}',
        'area': HH_AREA,
        'period': HH_PERIOD,
        'salary': HH_SALARY,
        'page': page,
        'per_page': HH_PER_PAGE,
    }
    response = requests.get('https://api.hh.ru/vacancies', params=params)
    response.raise_for_status()
    return response.json()


def predict_rub_salary_hh(programming_language):
    """Зарплаты для HeadHunter"""
    total_salaries = []
    page = 0
    vacancies_found = 0
    while True:
        vacancies = fetch_vacancies_hh(programming_language, page)
        if not vacancies:
            break
        vacancies_found = vacancies.get('found', 0)
        for vacancy in vacancies.get('items', []):
            salary_data = vacancy.get('salary')
            if salary_data and salary_data.get('currency') in ('RUR', 'RUB'):
                salary = predict_salary(
                    salary_data.get('from'),
                    salary_data.get('to')
                )
                if salary:
                    total_salaries.append(salary)
        pages = vacancies.get('pages', 0)
        if page >= pages - 1:
            break
        page += 1
        time.sleep(0.2)
    vacancies_processed = len(total_salaries)
    avg_salary = int(statistics.mean(total_salaries)) if total_salaries else 0
    return avg_salary, vacancies_found, vacancies_processed


def create_table(statistics, title):
    """Создает таблицу для вывода"""
    table_data = [
        ["Язык", "Вакансий", "Обработано", "Средняя зарплата"]
    ]
    for lang, data in statistics.items():
        table_data.append([
            lang,
            data["vacancies_found"],
            data["vacancies_processed"],
            f"{data['average_salary']:,} руб.".replace(",", " "),
        ])
    return AsciiTable(table_data, title).table


def main():
    load_dotenv()
    api_key_sj = os.getenv('API_KEY_SJ')
    languages = ['Python', 'Java', 'JavaScript', 'C#', 'C++', 'PHP', 'Go', 'Swift']
    results = {'hh': {}, 'sj': {}}
    for lang in languages:
        avg, found, processed = predict_rub_salary_hh(lang)
        results['hh'][lang] = {
            'vacancies_found': found,
            'vacancies_processed': processed,
            'average_salary': avg
        }
    if api_key_sj:
        for lang in languages:
            avg, found, processed = predict_rub_salary_sj(lang, api_key_sj)
            results['sj'][lang] = {
                'vacancies_found': found,
                'vacancies_processed': processed,
                'average_salary': avg
            }
    print(create_table(results['hh'], "HeadHunter Москва"))
    if api_key_sj:
        print(create_table(results['sj'], "SuperJob Москва"))


if __name__ == "__main__":
    main()
