from wsgiref import headers

import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd


def get_concert_reviews():
    url = "http://ticket.interpark.com/Community/Play/Talk/CommunityList.asp"

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    time.sleep(2)

    reviews = []

    try:
        driver.execute_script("javascript:ChangeCategory('01003');")
        time.sleep(2)
        all_rows = []
        for page in range(1, 21):
            driver.execute_script(f'javascript:goPage({page})')
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            table = soup.select_one(
                "body > table > tbody > tr:nth-child(4) > td > table > tbody > tr > td:nth-child(1) > table > tbody > tr:nth-child(9) > td > table > tbody > tr:nth-child(2) > td > table > tbody")

            rows = table.select("table")
            all_rows.append(rows)

        for cur_rows in all_rows:
            for row in cur_rows:
                link = row.find_all("a")
                if len(link) < 2:
                    continue
                full_link = "https://ticket.interpark.com/Community/Play/Talk/" + link[1]["href"]

                response = requests.get(full_link)
                response.encoding = 'utf-8'
                detail_soup = BeautifulSoup(response.content, "html.parser")
                iframe = detail_soup.find('iframe', {'id': 'ContentFr'})
                if iframe is None:
                    continue
                print(full_link)
                iframe_src = iframe['src']
                iframe_url = f"https://ticket.interpark.com/Community/Play/Talk/{iframe_src}"
                print(iframe_url)
                print()

                iframe_response = requests.get(iframe_url)
                # iframe_response.encoding = 'utf-8'
                iframe_soup = BeautifulSoup(iframe_response.content.decode('euc-kr', 'replace'), 'html.parser')

                title = iframe_soup.find('td', class_='title03').text.strip()
                content = iframe_soup.find_all('td', class_='texts')[-1].text.strip()
                # print(title)
                # print(content)
                # print()
                reviews.append({
                    "title": title,
                    "content": content,
                })
    except:
        print("Error while trying to change category")
    driver.quit()

    return reviews


def save_reviews_to_csv(reviews, filename):
    df = pd.DataFrame(reviews)
    df.to_csv(filename, index=False, encoding='utf-8')
    print("Saved reviews to csv file.")


reviews = get_concert_reviews()
print(f"Fetched {len(reviews)} reviews")

# 파일 저장
csv_filename = "concert_reviews.csv"
save_reviews_to_csv(reviews, csv_filename)

# 결과 출력
for review in reviews:
    print(review)
