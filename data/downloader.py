import json
import os
import time
import tqdm
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

#テスト用　本番はipynbで実行すること
url_test = "https://takuto-sugawara.github.io/scraping_test/"
url = "https://ncs.io/"

class CheckpointManager:

    def __init__(self, checkpoint_file="checkpoint.json"):
        pass
        
class NCSDownloader:

    def __init__(self, url, checkpoint_file="checkpoint.json", limit=10, headless=False):
        self.url = url
        self.track_links = []
        self.checkpoint = checkpoint_file
        self.downloaded_files = []
        self.load_checkpoint()
        self.limit = limit

        options = Options()
        options.add_experimental_option("prefs", {
            "download.default_directory":os.getcwd()+"/data/downloads"
        })# ダウンロード先のディレクトリを指定 ipynbで実行することを想定している
        if headless:
            options.add_argument("--headless") # Run headless Chrome

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

    def load_checkpoint(self):
        pass #あとでやる
 
    def enter(self):
        self.driver.get(self.url)
        print("Successfully entered URL:", self.url)
        time.sleep(10) #念のため

    def search_download_links(self):
        pass #あとでやる
        #チェックポイントファイルを参照して、重複しているリンクはdownload_linksに追加しない

    def download_files(self):
        for i in range(self.limit):
            download = self.download_file(self.track_links[i])
            self.downloaded_files.append(download)
            print(f"Downloaded file {i+1}/{self.limit}: {download}")
            print("waiting for 300 seconds before next download...")
            time.sleep(300)

    def download_file(self, link):

        pass
        #　return download_file = {[title, genres, artists, url, publish_date]}
        # download_file


    def quit(self):
        self.driver.quit()
        print("Driver closed.")

"""
download_files = {[title, genres, artists, url, publish_date]}
この形式で
"""

