from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# Set up Chrome options
options = Options()
options.add_argument("--headless")  # Run headless Chrome

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)


# drive to a website 
driver.get("https://www.google.com")
print(driver.title)

driver.quit()
