import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


driver = webdriver.Edge(executable_path='./MicrosoftWebDriver.exe')
url = "https://e-hentai.org/g/1328244/c654cbd9f2/"
driver.get(url)
print(driver.current_url)
#element = WebDriverWait(driver, 240).until( lambda driver: driver.current_url != url )
element = WebDriverWait(driver, 240).until( EC.presence_of_element_located((By.ID, "lst-ib") ))

print(element)
driver.close()
