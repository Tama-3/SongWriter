import openai
import time
import requests
import re
import jaconv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager


# Twitterトレンドの抽出
def get_trendword():
    trend_url = 'https://twittrend.jp/'
    res = requests.get(trend_url)
    soup = BeautifulSoup(res.text, 'html.parser')
    element = soup.select(
        '#now > div:nth-child(1) > div:nth-child(2) > ul:nth-child(1) > li:nth-child(1) > p:nth-child(1) > a:nth-child(2)'
    )[0]
    return element.contents[0][1:] if element.contents[0][0] == '#' else element.contents[0]


def write_lyric(title, api_key):
    openai.api_key = api_key
    prompt = f'「{title}」をタイトルとした日本語の歌詞を考えてください。'
    lyric = openai.Completion.create(
        engine='text-davinci-003', prompt=prompt, max_tokens=1024, temperature=0.8)['choices'][0]['text']
    return lyric


def make_song(title, lyric, **manual):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    driver.implicitly_wait(7)
    driver.get('https://creevo-music.com/project')
    time.sleep(3)
    # 歌詞変換
    processed_lyric = jaconv.kata2hira(re.sub('Verse ?\d?|Chorus|Bridge', "", lyric).lstrip())
    driver.find_element_by_xpath('/html/body/div[1]/div/div[2]/div/div/textarea').send_keys(processed_lyric)
    driver.find_element_by_xpath('/html/body/div[1]/div/div[3]/button/span[1]').click()
    time.sleep(3)
    # 12小節まで削減
    yomigana = driver.find_element_by_xpath(
        '/html/body/div[1]/div/div[5]/div/div/textarea').text.replace('\n', '').replace(' ', '　')
    if len(yomigana.split('　')) > 12:
        yomigana = '　'.join(yomigana.split('　')[:12])
        driver.find_element_by_xpath(
            'html/body/div[1]/div/div[5]/div/div/textarea').send_keys((Keys.CONTROL + 'a'))
        driver.find_element_by_xpath('html/body/div[1]/div/div[5]/div/div/textarea').send_keys(Keys.DELETE)
        driver.find_element_by_xpath('/html/body/div[1]/div/div[5]/div/div/textarea').send_keys(yomigana)
    driver.find_element_by_xpath('/html/body/div[1]/div/button/span[1]').click()  # 読み仮名確定

    # 作曲
    if not manual:
        driver.find_element_by_xpath('/html/body/div[1]/div/div[8]/button/span[1]').click()  # 全自動作曲 確定
    else:
        driver.find_element_by_xpath(
            '/html/body/div[1]/div/div[7]/fieldset/div/label[2]/span[1]/span[1]/input').click()
        # マニュアル楽曲作成設定
        Select(driver.find_element_by_xpath(
            '/html/body/div[1]/div/div[8]/div/div')).select_by_value(manual['コード進行'])
        Select(driver.find_element_by_id('mui-component-select-key')).select_by_value(manual['曲調'])
        Select(driver.find_element_by_xpath(
            '/html/body/div[1]/div/div[10]/div/div')).select_by_value(manual['メロディーのスタイル'])
        Select(driver.find_element_by_xpath(
            '/html/body/div[1]/div/div[11]/div/span/input')).select_by_value(manual['テンポ'])
        Select(driver.find_element_by_id(
            'mui-component-select-instrument')).select_by_value(manual['メロディー楽器'])
        Select(driver.find_element_by_xpath(
            '/html/body/div[1]/div/div[14]/div/div')).select_by_value(manual['伴奏パターン①'])
        Select(driver.find_element_by_xpath(
            '/html/body/div[1]/div/div[15]/div/div')).select_by_value(manual['伴奏楽器①'])
        Select(driver.find_element_by_xpath(
            '/html/body/div[1]/div/div[16]/div/div')).select_by_value(manual['伴奏パターン②'])
        Select(driver.find_element_by_xpath(
            '/html/body/div[1]/div/div[17]/div/div')).select_by_value(manual['伴奏楽器②'])
        Select(driver.find_element_by_xpath(
            '/html/body/div[1]/div/div[18]/div/div')).select_by_value(manual['ドラムパターン'])
        driver.find_element_by_xpath('/html/body/div[1]/div/button[2]/span[1]').click()  # 確定
        time.sleep(5)

    driver.find_element_by_xpath('/html/body/div[3]/div[3]/div/div[2]/div/div/div/input').clear()
    driver.find_element_by_xpath(
        '/html/body/div[3]/div[3]/div/div[2]/div/div/div/input').send_keys(title)  # タイトル入力
    driver.find_element_by_xpath('/html/body/div[3]/div[3]/div/div[3]/button[3]/span[1]').click()
    time.sleep(7)
    driver.find_element_by_xpath('/html/body/div[3]/div[3]/div/div/div[2]/a/span[1]').click()
    time.sleep(2)
    handle_array = driver.window_handles
    driver.switch_to.window(handle_array[1])
    time.sleep(3)

    if not any(manual):
        WebDriverWait(driver, 300).until(EC.visibility_of_element_located(
            (By.XPATH, '/html/body/div[1]/div/div/div[4]/div/div[1]/div/div[2]/button[2]/span[1]'))).click()

    time.sleep(5)
    # song_id = driver.current_url[driver.current_url.rfind('/')+1:driver.current_url.find('?')]
    # mp3_url = 'https://creevo-music.com/api/static/project_' + song_id + '.mp3'
    try:
        WebDriverWait(driver, 300).until(EC.visibility_of_element_located(
            (By.XPATH, '/html/body/div[1]/div/header/div/div/div[1]/div/div[1]/span/label[10]'))).click()
    except:
        pass
    mp3_url = driver.find_element_by_tag_name('audio').get_attribute("src")
    driver.quit()

    return mp3_url
