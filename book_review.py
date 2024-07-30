import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
def get_yes24_reviews(book_id, max_pages=50):
    base_url = f"https://www.yes24.com/Product/communityModules/GoodsReviewList/{book_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    reviews = []
    for page in range(1, max_pages + 1):
        url = f"{base_url}?goodsSetYn=N&Sort=2&PageNumber={page}&DojungAfterBuy=1&Type=Purchase"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")

        review_items = soup.find_all("div", class_="reviewInfoGrp")

        for item in review_items:
            try:
                review_title = item.find("span", class_="txt").text.strip()
            except AttributeError:
                review_title = "No title"

            try:
                user_name = item.find("a", class_="lnk_id").text.strip()
            except AttributeError:
                user_name = "Unknown"

            try:
                review_date = item.find("em", class_="txt_date").text.strip()
            except AttributeError:
                review_date = "Unknown"

            try:
                rating = item.find("span", class_="total_rating").text.strip().replace("평점", "")
            except AttributeError:
                rating = "No rating"

            try:
                origin = item.find("div", class_="origin")
                review_text = origin.find("div", class_="review_cont").text.strip()
            except AttributeError:
                review_text = "No review text"

            reviews.append({
                "user_name": user_name,
                "review_date": review_date,
                "rating": rating,
                "review_title": review_title,
                "review_text": review_text,
                "book_id": book_id
            })

    return reviews

def save_reviews_to_csv(reviews, filename):
    df = pd.DataFrame(reviews)
    df.to_csv(filename, index=False, encoding='utf-8')
    print("Saved reviews to csv file.")

# 예시 실행
book_ids = ["2312211", "128266166", "117014613", "116599423"]
all_reviews = []
for book_id in book_ids:
    reviews = get_yes24_reviews(book_id)
    print("Fetched book reviews for", book_id)
    all_reviews.extend(reviews)

# 파일 저장
csv_filename = "book_reviews.csv"
save_reviews_to_csv(all_reviews, csv_filename)

# 결과 출력
for review in all_reviews:
    print(review)