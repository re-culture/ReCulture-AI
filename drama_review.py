import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd

def get_drama_reviews(movie_id):
    url = f"https://m.kinolights.com/title/{movie_id}?tab=review"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    movie_name = soup.find("h1", {"class": "movie-title"}).text.strip()
    print(movie_name)
    print (soup.find("h1", class_= "movie-title").text.strip())
    reviews = []
    review_items = soup.find_all("article", class_="review-item")
    for item in review_items:
        user_name = item.find("h5").text.strip()
        review_date = item.find("span", class_="title__watch-at").text.strip()
        rating = item.find("span", class_="user-star-score").text.strip()
        review_title = item.find("a", class_="contents__title").find("h5").text.strip()

        reviews.append({
            "user_name": user_name,
            "review_date": review_date,
            "rating": rating,
            "review_title": review_title,
            "movie_id": movie_id,
            "movie_name": movie_name
        })
    return reviews

def get_kinolights_reviews(drama_id):
    url = f"https://m.kinolights.com/title/{drama_id}?tab=review"

    options = Options()
    options.add_argument("--headless")  # 브라우저 창을 열지 않음
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)

    SCROLL_PAUSE_TIME = 2
    MAX_SCROLL_TIME = 30
    start_time = time.time()

    # 스크롤을 끝까지 내림
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height or (time.time() - start_time) > MAX_SCROLL_TIME:
            break
        last_height = new_height

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    drama_name = soup.find("h1", {"class": "movie-title"}).text.strip()
    reviews = []
    review_items = soup.find_all("article", class_="review-item")
    for item in review_items:
        try:
            user_name = item.find("h5").text.strip()
        except AttributeError:
            user_name = "Unknown"

        try:
            review_date = item.find("span", class_="title__watch-at").text.strip()
        except AttributeError:
            review_date = "Unknown"

        try:
            rating = item.find("span", class_="user-star-score").text.strip()
        except AttributeError:
            rating = "No rating"

        try:
            review_title = item.find("a", class_="contents__title").find("h5").text.strip()
        except AttributeError:
            review_title = "No title"


        reviews.append({
            "user_name": user_name,
            "review_date": review_date,
            "rating": rating,
            "review_title": review_title,
            "drama_id": drama_id,
            "drama_name": drama_name
        })

    return reviews

def save_reviews_to_csv(reviews, filename):
    df = pd.DataFrame(reviews)
    df.to_csv(filename, index=False, encoding='utf-8')
    print("Saved reviews to csv file.")

drama_ids = [130294, 130737, 80083, 79978]
all_reviews = []
for drama_id in drama_ids:
    reviews = get_kinolights_reviews(drama_id)
    print("Fetched movie reviews for", drama_id)
    all_reviews.extend(reviews)


# 파일 저장
csv_filename = "drama_reviews.csv"
save_reviews_to_csv(all_reviews, csv_filename)

# 결과 출력
for review in all_reviews:
    print(review)