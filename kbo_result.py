import requests
from bs4 import BeautifulSoup
import pandas as pd

def get_kbo_results(year, month):
    url = f"https://statiz.sporki.com/schedule/?year={year}&month={month}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    results = []
    td_elements = soup.select('td')

    for td in td_elements:
        # 경기 정보가 있는 td 요소 찾기
        if td.select_one('div.game_schedule_m'):
            day = td.select_one('span.day').text
            print(f"{year}-{month}-{day}")

            games = td.select('div.games ul li a')

            for game in games:

                teams = game.select('span.team')
                scores = game.select('span.score')
                if len(teams) == 0 or len(scores) == 0:
                    continue

                response = requests.get(f"https://statiz.sporki.com{game['href']}")
                detail_soup = BeautifulSoup(response.content, "html.parser")

                team1_name = teams[0].text
                team1_score = scores[0].text
                team2_score = scores[1].text
                team2_name = teams[1].text
                location_date = detail_soup.select_one('div.score div.txt').text.strip()
                location = location_date.split(", ")[0]

                # Best 5에서 첫 번째 선수 추출
                best_5_table = detail_soup.select('div.box_type_boared div.item_box div.inner div.sh_box div.box_cont '
                                                  'div.table_type03 table')[1]
                mvp_element = best_5_table.select('tbody tr td a')[0]
                mvp_player = mvp_element.text.strip() if mvp_element else 'N/A'

                # print(location)
                # print(f"{team1_name} {team1_score} - {team2_score} {team2_name}")
                # print(mvp_player)
                game_info = {
                    "year": year,
                    "month": month,
                    "day": day,
                    "team_1": team1_name,
                    "team_2": team2_name,
                    "score_1": team1_score,
                    "score_2": team2_score,
                    "location": location,
                    "mvp_player": mvp_player,
                }
                review1, review2 = generate_game_review(game_info)
                game_info["review1"] = review1
                game_info["review2"] = review2
                results.append(game_info);
            # print("\n")
    return results

def generate_game_review(game_data):
    winning_team = game_data['team_1'] if int(game_data['score_1']) > int(game_data['score_2']) else game_data['team_2']
    losing_team = game_data['team_2'] if winning_team == game_data['team_1'] else game_data['team_1']
    winning_score = game_data['score_1'] if winning_team == game_data['team_1'] else game_data['score_2']
    losing_score = game_data['score_2'] if winning_team == game_data['team_1'] else game_data['score_1']
    mvp_player = game_data['mvp_player']
    location = game_data['location']
    date = f'{game_data["year"]}-{game_data["month"]}-{game_data["day"]}'

    winning_team_review = f"""
    {date}에 {location}에서 열린 경기에서 {winning_team}가 {losing_team}를 상대로 {winning_score} 대 {losing_score}로 승리를 거두었습니다. {winning_team}는 경기 내내 뛰어난 활약을 펼쳤으며, 특히 {mvp_player}가 MVP로 선정되었습니다. 이번 승리로 {winning_team}는 다음 경기에서도 좋은 성적을 기대할 수 있을 것으로 보입니다.
    """

    losing_team_review = f"""
    {date}에 {location}에서 열린 경기에서 {losing_team}는 {winning_team}를 상대로 {losing_score} 대 {winning_score}로 아쉽게 패배하였습니다. {losing_team}는 경기 초반에 좋은 출발을 보였으나, 후반에 접어들며 {winning_team}의 공세를 막지 못했습니다. 이번 패배로 {losing_team}는 다음 경기에서 더 나은 성적을 기대하고 있습니다.
    """

    return winning_team_review, losing_team_review

def save_results_to_csv(results, filename):
    df = pd.DataFrame(results)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print("Saved results to csv file.")


# 예시 실행
season_year = 2024
kbo_results = []
for season_month in range(3, 8):
    kbo_results += get_kbo_results(season_year, season_month)
print(f"Fetched {len(kbo_results)} match results")

# 파일 저장
csv_filename = "kbo_results_2024.csv"
save_results_to_csv(kbo_results, csv_filename)

# 결과 출력
for result in kbo_results:
    print(result)
