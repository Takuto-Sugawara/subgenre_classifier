import json
import os
import time
import tqdm
from bs4 import BeautifulSoup
import requests
from itertools import islice
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

#テスト用　本番はipynbで実行すること
url_test = "https://takuto-sugawara.github.io/scraping_test/"
url = "https://ncs.io/"

class CheckpointManager:

    def __init__(self, tracks_data="tracks_data.json"):
        pass
        
class NCSDownloader:

    def __init__(self, url, tracks_data="tracks_data.json", page_limit=1, track_limit=5, headless=False):
        self.url = url
        self.track_links = [] # ダウンロードリンクを格納するリスト
        self.tracks_database = tracks_data #曲の情報を管理するjsonファイル
        self.load_database()
        self.page_limit = page_limit
        self.track_limit = track_limit

        options = Options()
        options.add_experimental_option("prefs", {
            "download.default_directory":os.getcwd()+"/data/downloads"
        })# ダウンロード先のディレクトリを指定 ipynbで実行することを想定している
        if headless:
            options.add_argument("--headless") # Run headless Chrome

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

    def load_database(self):
        pass #あとでやる
 
    def enter(self):
        self.driver.get(self.url)
        print("Successfully entered URL:", self.url)
        time.sleep(1) #念のため

    def search_download_links(self):
        #ちょいちょいサイトの構造が変わるので都度変更
        """
        return links = [{url:str, title:str, artists:list[str]}, ...]
        information about genres is included in links
        it will be get from the track page in download_file method
        """

        for _ in range(self.page_limit): #1ページ内の曲詳細ページのリンク、アーティスト名、曲名、ジャンルを含むクラスを取得
            print("Searching for download links...")
            body = self.driver.find_element(By.TAG_NAME, "body")
            main = body.find_element(By.TAG_NAME, "main")
            module = main.find_element(By.CLASS_NAME, "module artists")
            container_fluid = main.find_element(By.CLASS_NAME, "container-fluid")
            row = container_fluid.find_element(By.CLASS_NAME, "row")
            items = row.find_elements(By.CLASS_NAME, "col-lg-2 item")

            for item in islice(items, self.track_limit):
                link = item.find_element(By.TAG_NAME, "a")
                
                #ジャンルが複数ある場合はカンマ区切りで書かれている
                genres = item.find_element(By.CLASS_NAME, "options").find_element(By.CLASS_NAME, "row align-items-center")
                genres = genres.find_element(By.CLASS_NAME, "col-6 col-lg-6").find_element(By.TAG_NAME, "span")
                genres = genres.find_elements(By.TAG_NAME, "strong").text

                
                





        return
        #チェックポイントファイルを参照して、重複しているリンクはdownload_linksに追加しない

    def download_files(self):
        for i in range(len(self.track_links)):
            download = self.download_file(self.track_links[i])
            self.downloaded_files.append(download)
            print(f"Downloaded file {i+1}/{self.limit}: {download}")
            print("waiting for 10 seconds before next download...")
            time.sleep(10)

    def download_file(self, link):

        pass
        #　return download_file = {[title, genres, artists]}
        # download_file


    def quit(self):
        self.driver.quit()
        print("Driver closed.")

"""
download_files = {[title, genres, artists]}
この形式で
"""

