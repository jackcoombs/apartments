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

def get_soup(url,driver):

    driver.get(url) #open webpage

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

    return soup

def get_listings(soup,num,city_side):

    listings = soup.find_all('li',class_='mortar-wrapper')

    apartments = []

    #start number to assign listings ids
    id = 0

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
            link = i.find('a',class_='property-link').get('href')
        except:
            link = np.NaN

        #create data dictionary, append to list
        data = {
            'date':date.today(),
            'address':address,
            'link':link,
            'page_num':num,
            'id':city_side + '-' + str(num) + str(id), #include city side for north and south jobs

        }
        apartments.append(data)

        id = id + 1

    #create dataframe from list of dictionaries
    df = pd.DataFrame(apartments)

    return df


def get_listing_info(soup,id):
    ## create df of key, value pairs with each id ##

    info = []

    #main info under listing photos
    main_info = soup.find_all('div','priceBedRangeInfoInnerContainer')
    for i in main_info:
        label = i.find('p','rentInfoLabel').text.strip()
        detail = i.find('p','rentInfoDetail').text.strip()
        data = {
            'id':id,
            'label':label,
            'detail':detail
        }
        info.append(data)
    
    #scorecards near bottom of page
    scores = soup.find('div',id='transportationScoreCard').find_all('div','component-frame')
    for i in scores:
        try:
            label = i.find('div','title scoreDescription').text.strip()
            detail = i.find('div','score').text.strip()
            data = {
                'id':id,
                'label':label,
                'detail':detail
            }
            info.append(data)
        except:
            continue #unable to get noise level. ignore it by continuing
    
    #neighborhood at top of page
    nbhd = {'id':id,'label':'Neighborhood','detail':soup.find('a','neighborhood').text.strip()}
    info.append(nbhd)

    df = pd.DataFrame(info)
    df = df.loc[df['label']!='None']

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

def create_dataframes(main_url, url_params, city_side):
    ## loop through the page numbers, extract the data, and create dataframe ##

    listings = pd.DataFrame()
    num = 1
    chrome_options = Options()
    #chrome_options.add_argument("--headless") #gets the javascript without opening the browser
    driver = webdriver.Chrome(service=Service(config.chromedriver),options=chrome_options)

    ## Get all of the listings in one dataframe ##
    url = main_url + url_params
    soup = get_soup(url,driver)
    info = get_listings(soup,num,city_side)
    listings = pd.concat([listings,info],axis=0)
    num = num + 1

    page_number = extract_page_number(soup.find('span',class_='pageRange').text.strip()) + 1

    while num < page_number:
        url = main_url + str(num) + '/' + url_params
        soup = get_soup(url,driver)
        info = get_listings(soup,num,city_side)
        listings = pd.concat([listings,info],axis=0)
        num = num + 1

    ## Open each listing and extract info ##
    listing_info = pd.DataFrame()

    for link,id in zip(listings['link'],listings['id']):
        soup = get_soup(link,driver)
        info = get_listing_info(soup,id)
        listing_info = pd.concat([listing_info,info],axis=0)


    driver.close()

    #return two dfs, the listings and info
    return listings,listing_info

#run once for north side and south side to maximize listings returned
north_listings, north_listing_info = create_dataframes(main_url='https://www.apartments.com/chicago-il/',url_params='?bb=tut6lj08yJ_klggsD', city_side='north')
south_listings, south_listing_info = create_dataframes(main_url='https://www.apartments.com/chicago-il/',url_params='?bb=3u0uls72yJqxxpqvN', city_side='south')

#join north and south into two dfs
listings = pd.concat([north_listings,south_listings],axis=0)
listing_info = pd.concat([north_listing_info,south_listing_info],axis=0)

write_to_big_query(listings,'apartments','chicago_listings')
write_to_big_query(listing_info,'apartments','chicago_listing_info')