from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import re
from google.cloud import bigquery
from google.oauth2 import service_account
import config
from datetime import date

def get_soup(url):

    chrome_options = Options()
    #chrome_options.add_argument("--headless") #gets the javascript without opening the browser

    driver = webdriver.Chrome(service=Service(config.chromedriver),options=chrome_options)
    driver.get(url)

    #scroll to bottom
    SCROLL_PAUSE_TIME = 0.5

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    #save to beautiful soup object
    html = driver.page_source
    soup = BeautifulSoup(html,'html.parser')

    driver.close()

    return soup

def get_info(soup,num):

    listings = soup.find_all('li',class_='mortar-wrapper')

    apartments = []

    #loop through listings, trying several elements where needed. extract needed data
    for i in listings:
        try:
            address = i.find('div',class_='property-address js-url').text.strip()
        except:
            try:
                address = i.find('p',class_='property-address js-url').text.strip()
            except:
                try:
                    address = i.find('span',class_='js-placardTitle title').text.strip()
                except:
                    address = i.find('div',class_='property-title js-placardTitle').text.strip() 
        try:
            price = i.find('p',class_='property-pricing').text.strip()
        except:
            try:
                price = i.find('div',class_='price-range').text.strip()
            except:
                price = i.find('p',class_='property-rents').text.strip()
        try:
            info = i.find('p',class_='property-beds').text.strip()
        except:
            info = i.find('div',class_='bed-range').text.strip()
        try:
            link = i.find('a',class_='property-link').get('href')
        except:
            link = np.NaN

        #create data dictionary, append to list
        data = {
            'date':date.today(),
            'address':address,
            'price':price,
            'info':info,
            'link':link,
            'page_num':num
        }
        apartments.append(data)
        
    #create dataframe from list of dictionaries
    df = pd.DataFrame(apartments)

    return df

def extract_page_number(page_string):
    # Define regex pattern to match the number in the string "Page x of y"
    pattern = r'Page (\d+) of (\d+)'
    
    # Use regex to search for the pattern in the page_string
    match = re.match(pattern, page_string)
    
    # If match found, extract the second group (y)
    if match:
        return int(match.group(2))
    else:
        return None
    
def extract_and_split(text):
    # Split the text using the hyphen as the delimiter
    numbers = text.split("-")
    
    # Extract the two numbers
    if len(numbers) == 2:
        num1 = numbers[0].strip()  # Remove leading/trailing whitespaces
        num2 = numbers[1].strip()  # Remove leading/trailing whitespaces
    else:
        num1 = 0
        num2 = numbers[0]
    
    return num1, num2

def write_to_big_query(df,dataset,table):
    credentials = service_account.Credentials.from_service_account_file(config.credentials)

    client = bigquery.Client(credentials=credentials, project=credentials.project_id)

    #append data to bigquery
    job_config = bigquery.LoadJobConfig()
    job_config.create_disposition = "CREATE_IF_NEEDED"
    job_config.write_disposition = "WRITE_TRUNCATE" #overwrite the table data
    table_id = f"{dataset}.{table}"
    job = client.load_table_from_dataframe(dataframe=df,
                                                destination=table_id, 
                                                job_config=job_config)
    return print(f"{table} created with " + str(len(df)) + " rows"), job.result()

def create_dataframe(main_url, url_params):
## loop through the page numbers, extract the data, and create dataframe ##

    df = pd.DataFrame()
    num = 1

    #set initial url
    url = main_url + url_params
    soup = get_soup(url)
    info = get_info(soup,num)
    df = pd.concat([df,info],axis=0)
    print('page 1 extracted')
    num = num + 1

    #find the max page number from the bottom of the main_url
    page_number = extract_page_number(soup.find('span',class_='pageRange').text.strip()) + 1

    #loop through rest of pages using page number
    while num < page_number:
        url = main_url + str(num) + '/' + url_params
        soup = get_soup(url)
        info = get_info(soup,num)
        df = pd.concat([df,info],axis=0)
        print(f'page {num} extracted') #keep track of progress
        num = num + 1

    ## Clean Data ##

    df['price'] = df['price'].str.replace('$','').str.replace(',','')

    #Apply the extract_and_split function to the 'price' column
    df['price_low'], df['price_high'] = zip(*df['price'].apply(extract_and_split))

    #create a flag column if the price returns 'Call for Rent'
    df['call_for_rent'] = df['price_high'].apply(lambda x: 'y' if 'Call for Rent' in x else '')

    df['price_low'] = df['price_low'].astype(int)
    df['price_high'] = df['price_high'].str.replace("Call for Rent", '0').astype(int) #replace call for rent with 0

    df['beds'] = df['info'].str.extract('([0-9]+) Bed').fillna(0).astype(int)
    df['bathrooms'] = df['info'].str.extract('([0-9]+) Bath').fillna(0).astype(int)
    df['sq_ft'] = df['info'].str.extract('([0-9]+) sq ft').fillna(0).astype(int)
    df['zip_code'] = df['address'].str.extract('IL ([0-9]+)').fillna(0).astype(int)

    return df

#run once for north side and south side to maximize listings returned
north = create_dataframe(main_url='https://www.apartments.com/chicago-il/',url_params='?bb=tut6lj08yJ_klggsD')
south = create_dataframe(main_url='https://www.apartments.com/chicago-il/',url_params='?bb=3u0uls72yJqxxpqvN')

df = pd.concat([north,south],axis=0)

print(df.head())
write_to_big_query(df,'apartments','chicago')