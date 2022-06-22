import requests
from selenium import webdriver as wd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
from tqdm.auto import tqdm, trange
import random
import pandas as pd
from konlpy.tag import Kkma
from wordcloud import WordCloud


def scroll(modal):
    try:
        # 스크롤 높이 받아오기
        last_height = driver.execute_script("return arguments[0].scrollHeight", modal)
        while True:
            pause_time = random.uniform(0.5, 0.8)
            # 최하단까지 스크롤
            driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", modal)
            # 페이지 로딩 대기
            time.sleep(pause_time)
            # 무한 스크롤 동작을 위해 살짝 위로 스크롤
            driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight-50);", modal)
            time.sleep(pause_time)
            # 스크롤 높이 새롭게 받아오기
            new_height = driver.execute_script("return arguments[0].scrollHeight", modal)
            try:
                # '더보기' 버튼 있을 경우 클릭
                all_review_button = driver.find_element_by_xpath('/html/body/div[1]/div[4]/c-wiz/div/div[2]/div/div/main/div/div[1]/div[2]/div[2]/div/span/span').click()
            except:
                # 스크롤 완료 경우
                if new_height == 1000:
                    print("스크롤 완료")
                    break


    except Exception as e:
        print("에러 발생: ", e)


url = 'https://play.google.com/store/apps/details?id=jp.naver.line.android&hl=ko&gl=US'

driver = wd.Chrome(ChromeDriverManager().install())
driver.get(url)
time.sleep(2)
for c in range(0, 3):
    driver.find_element_by_tag_name('body').send_keys(Keys.PAGE_DOWN)
    time.sleep(1)

driver.find_element_by_xpath('//*[@id="yDmH0d"]/c-wiz[2]/div/div/div[1]/div[2]/div/div[1]/c-wiz[4]/section/div/div/div[5]/div/div/button').click()


# 페이지 무한 스크롤 다운
modal = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.XPATH, "//div[@class='fysCi']")))
scroll(modal)

# html parsing하기
html_source = driver.page_source
soup_source = BeautifulSoup(html_source, 'html.parser')

# 리뷰 데이터 클래스 접근
review_source = soup_source.find_all(class_='RHo1pe')
# 리뷰 데이터 저장용 배열
dataset = []
# 데이터 넘버링을 위한 변수
review_num = 0
# 리뷰 1개씩 접근해 정보 추출
for review in tqdm(review_source):
    review_num += 1
    # 리뷰 등록일 데이터 추출
    date_full = review.find_all(class_='bp9Aid')[0].text
    date_year = date_full[0:4]  # 연도 데이터 추출
    # 해당 단어가 등장한 인덱스 추출
    year_index = date_full.find('년')
    month_index = date_full.find('월')
    day_index = date_full.find('일')

    date_month = str(int(date_full[year_index + 1:month_index]))  # 월(Month) 데이터 추출
    # 월 정보가 1자리의 경우 앞에 0 붙이기(e.g., 1월 -> 01월)
    if len(date_month) == 1:
        date_month = '0' + date_month

    date_day = str(int(date_full[month_index + 1:day_index]))  # 일(Day) 데이터 추출
    # 일 정보가 1자리의 경우 앞에 0 붙여줌(e.g., 7일 -> 07일)
    if len(date_day) == 1:
        date_day = '0' + date_day

    # 리뷰 등록일 full version은 최종적으로 yyyymmdd 형태로 저장
    date_full = date_year + date_month + date_day
    user_name = review.find_all(class_='X5PpBb')[0].text  # 닉네임 데이터 추출
    rating = review.find_all(class_="iXRFPc")[0]['aria-label'][10]  # 평점 데이터 추출
    content = review.find_all(class_='h3YV2d')[0].text  # 리뷰 데이터 추출

    data = {
        "id": review_num,
        "date": date_full,
        "dateYear": date_year,
        "dateMonth": date_month,
        "dateDay": date_day,
        "rating": rating,
        "userName": user_name,
        "content": content
    }
    dataset.append(data)

df = pd.DataFrame(dataset)
df.to_csv('line_review.csv', encoding='utf-8-sig') # csv 파일로 저장

df_new = df[['date', 'rating', 'content']]
para = list(df_new['content'])

# 2. 문단(문자열) -> 문장(list)
kkma = Kkma()

ex_sents = kkma.sentences(para)  # list 반환
len(ex_sents)  # 636

# 문단(문자열) -> 명사(list)
ex_nouns = kkma.nouns(para)  # 유일한 명사 추출
len(ex_nouns)  # 2709

# 3. 문장 -> 단어(명사) 추출
nouns = []  # 중복 명사 저장

for sent in ex_sents:  # 문단 -> 문장
    for noun in kkma.nouns(sent):  # 문장 -> 명사 추출
        nouns.append(noun)

len(nouns)  # 6303

# 4. 전처리 & 단어 카운트 : 1음절 제외 & 서수 제외
from re import match  # 서수 제외

wc = {}  # 단어 카운트

for noun in nouns:
    if len(noun) > 1 and not (match('^[0-9]', noun)):  # 전처리
        wc[noun] = wc.get(noun, 0) + 1  # 단어 카운트

print(wc)
len(wc)  # 1645

# 5. 단어구름 시각화

# 1) topN word 선정
from collections import Counter  # class

counter = Counter(wc)
top50_word = counter.most_common(50)
print(top50_word)

# 2) word cloud
wc = WordCloud(font_path='C:/Windows/Fonts/malgun.ttf',
               width=500, height=400,
               max_words=100, max_font_size=150,
               background_color='white')

wc_result = wc.generate_from_frequencies(dict(top50_word))

import matplotlib.pyplot as plt

plt.imshow(wc_result)
plt.axis('off')  # 축 눈금 감추기
plt.show()




