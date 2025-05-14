import os

import time

import pickle
from rich import print_json
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def remove_duplicates(text):
    lines = text.split('\n')
    seen = set()
    unique_lines = []
    for line in lines:
        if line.strip() and line not in seen:  # .strip() чтобы игнорировать пустые строки
            unique_lines.append(line)
            seen.add(line)
    return '\n'.join(unique_lines)


COOKIE_FILE = "linkedin_cookies.pkl"

options = webdriver.ChromeOptions()
options.add_argument("--disable-gpu")  # Отключить GPU
options.add_argument("--disable-software-rasterizer")  # Отключить софтверный рендеринг
options.add_argument("--no-sandbox")  # Иногда требуется на Linux
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-webrtc")  # Полезно для Docker/CI


driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def scrape_linkedin_profile(url, driver, cookie_file="linkedin_cookies.pkl", output_file="profile_data.json"):
    driver.get("https://www.linkedin.com")

    if os.path.exists(cookie_file):
        print("[+] Загружаем cookies...")
        with open(cookie_file, "rb") as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)
    else:
        print("[!] Войдите в аккаунт вручную...")
        print("Ожидание входа (3 минуты)...")
        try:
            WebDriverWait(driver, 1800).until(
                EC.presence_of_element_located((By.CLASS_NAME, "render-mode-BIGPIPE"))
            )
        except:
            print("[!] Вход не выполнен за отведённое время.")
            driver.quit()
            return None

        print("[+] Сохраняем cookies...")
        cookies = driver.get_cookies()
        with open(cookie_file, "wb") as file:
            pickle.dump(cookies, file)

        print("[✓] Cookies сохранены. Перезапустите программу.")
        driver.quit()
        return None

    print("[✓] Авторизация завершена. Выполняем сбор данных...")

    # Основная информация профиля
    driver.get(url)
    time.sleep(2)
    main_page = driver.find_element(By.TAG_NAME, "main")
    

    try:
        name = driver.find_element(By.CSS_SELECTOR, 'span.artdeco-hoverable-trigger.artdeco-hoverable-trigger--content-placed-bottom.artdeco-hoverable-trigger--is-hoverable.ember-view').text
    except:
        name = 'без имени'
    try:
        job = driver.find_element(By.CSS_SELECTOR, 'div.text-body-medium.break-words').text
    except:
        job = 'без работы'
    try:
        location = driver.find_element(By.CSS_SELECTOR, 'span.text-body-small.inline.t-black--light.break-words').text
    except:
        location = 'без местоположения'

    time.sleep(2)
    try:
        description = driver.find_element(By.CSS_SELECTOR, 'div.display-flex.ph5.pv3').text
        
    except:
        description = 'без описания'
    try:
        opit_work = main_page.find_elements(By.TAG_NAME, "section")[4]
        experience_section = opit_work.find_elements(By.CSS_SELECTOR, 'div.display-flex.flex-row.justify-space-between')
        experience_list = []
        for section in experience_section:
            exp = section.find_elements(By.CSS_SELECTOR, 'span.visually-hidden')
            for e in exp:
                experience_list.append(e.text)
            lines = [line.strip() for line in experience_list if line.strip()]  
            experience = ', '.join(lines)
    except:
        experience = 'без опыта работы'
    # Интересы
    driver.get(url + 'details/interests/?detailScreenTabIndex=0')
    time.sleep(2)
    tabs = driver.find_element(By.TAG_NAME, 'main').find_element(By.CLASS_NAME, 'artdeco-tablist').find_elements(By.TAG_NAME, 'button')
    button_list = []
    for button in tabs:
        button_clean = button.find_elements(By.CSS_SELECTOR, 'span.visually-hidden')
        for b in button_clean:
            button_list.append(b.text)
    
    button = 0
    
    
    # Топ эксперты
    try:
        if button_list[button] != 'Топ-эксперты':
            raise Exception
        
        tabs[button].click()
        time.sleep(1)
        experts_text = []
        for expert in driver.find_elements(By.CSS_SELECTOR, 'div.pvs-list__container'):
            for exp in expert.find_elements(By.CSS_SELECTOR, 'div.display-flex.flex-wrap.align-items-center.full-height'):
                experts_text.append(exp.text)
        experts = ', '.join([line.strip() for line in remove_duplicates("\n".join(experts_text)).split('\n') if line.strip()])
        
        button += 1
    except:
        experts = 'без экспертов'
    
    # Компании
    try:
        if button_list[button] != 'Компании':
            raise Exception
        
        tabs[button].click()
        time.sleep(1)
        companies_text = []
        for container in driver.find_elements(By.CSS_SELECTOR, 'div.pvs-list__container'):
            for company in container.find_elements(By.CSS_SELECTOR, 'div.display-flex.flex-wrap.align-items-center.full-height'):
                companies_text.append(company.text)
        companies = ', '.join([line.strip() for line in remove_duplicates("\n".join(companies_text)).split('\n') if line.strip()])
        button += 1
    except:
        companies = 'без компаний'
    
    # Группы
    try:
        if button_list[button] != 'Группы':
            raise Exception
        
        tabs[button].click()
        time.sleep(1)
        groups_text = []
        for container in driver.find_elements(By.CSS_SELECTOR, 'div.pvs-list__container'):
            for group in container.find_elements(By.CSS_SELECTOR, 'div.display-flex.flex-wrap.align-items-center.full-height'):
                groups_text.append(group.text)
        groups = ', '.join([line.strip() for line in remove_duplicates("\n".join(groups_text)).split('\n') if line.strip()])
        button += 1
    except:
        groups = 'без групп'
    
    # Рассылки
    try:
        if button_list[button] != 'Рассылки':
            raise Exception
        
        tabs[button].click()
        time.sleep(1)
        mails_text = []
        for container in driver.find_elements(By.CSS_SELECTOR, 'div.pvs-list__container'):
            for mail in container.find_elements(By.CSS_SELECTOR, 'div.display-flex.flex-wrap.align-items-center.full-height'):
                mails_text.append(mail.text)
        mails = ', '.join([line.strip() for line in remove_duplicates("\n".join(mails_text)).split('\n') if line.strip()])
        button += 1
    except:
        mails = 'без рассылок'
    
    # Уч. заведения
    try:
        if button_list[button] != 'Уч. заведения':
            raise Exception
        
        tabs[button].click()
        time.sleep(1)
        schools_text = []
        for container in driver.find_elements(By.CSS_SELECTOR, 'div.pvs-list__container'):
            for school in container.find_elements(By.CSS_SELECTOR, 'div.display-flex.flex-wrap.align-items-center.full-height'):
                schools_text.append(school.text)
        schools = ', '.join([line.strip() for line in remove_duplicates("\n".join(schools_text)).split('\n') if line.strip()])
    except:
        schools = 'без уч. заведений'
    button = 0
    # Формирование данных
    data = {
        'Имя': name,
        'Работа': job,
        'Местоположение': location,
        'Краткое описание': description,
        'Опыт работы': experience,
        'Интересы': {
            'Топ эксперты': experts,
            'Компании': companies,
            'Группы': groups,
            'Рассылки': mails,
            'Уч. заведения': schools
        }
    }

    # Сохранение
        # Загрузка существующих данных, если файл уже есть
    existing_data = {}
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                print("[!] Файл JSON повреждён или пустой. Начинаем заново.")

    # Ключ для новой записи (по URL или имени)
    profile_key = name if name else url

    # Добавление или обновление данных
    existing_data[profile_key] = data

    # Сохранение обратно
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)

    print(f"[✓] Данные профиля добавлены в {output_file}")
    return data




profile_urls = ['https://www.linkedin.com/in/irina-lubanets-691a5256/', 'https://www.linkedin.com/in/dhirendra-kumar-6217792b/','https://www.linkedin.com/in/ekaterina-tarasova-ba744279/','https://www.linkedin.com/in/aleksander-sergeevich-shvedov/']
for profile_url in profile_urls:
    try:
        data = scrape_linkedin_profile(profile_url, driver)
        print_json(data=data)
    except:
        print(f"[!] Ошибка при сборе данных с {profile_url}")
    
    time.sleep(5)
    
driver.quit()


