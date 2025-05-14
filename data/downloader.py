import json
import os
import time
import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class Downloader:
    def __init__(self, urls, checkpoint_file="checkpoint.json"):
        self.urls = urls
        self.checkpoint = checkpoint_file
        self.downloaded = set()
        self.load_checkpoint()

        options = Options()
        options.add_argument("--headless") # Run headless Chrome

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)


# drive to a website 
driver.get("https://www.google.com")
print(driver.title)

driver.quit()