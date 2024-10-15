# Chicago Apartments

## Overview

Common questions when apartment hunting are "How much should I expect to pay?", "What's the average rent for this area?", or "How much space can I afford?". This project aims to help renters in the Chicago area answer those questions by providing a simple dashboard that can filtered by zip code, # beds, # bathrooms, and square footage.

## Features
This project does the following:

1. Scrapes Chicago apartment data from Apartments.com
2. Transforms and writes the data to BigQuery
3. Powers a dashboard in Looker Studio

## Webscraping

Python and the Selenium library are used to open many pages of Apartments.com search results, save the javascript, and extract key data from each apartment listing. See `etl.py`.

## BigQuery

Once the data is cleaned, it is written to a BigQuery table. This way, the data can be used to power dashboards in BI tools or be downloaded for further analysis. See `etl.py`.

## Dashboard

This dashboard in Looker Studio looks at all the scraped listings, and shows the average square feet and monthly rent based on the filters: https://lookerstudio.google.com/reporting/c21e28f4-b9f1-4e9e-a101-e06b9a4da893

Zip codes for specific neighborhoods can be looked up here: https://www.chicago.gov/content/dam/city/sites/covid/reports/2020-04-24/ChicagoCommunityAreaandZipcodeMap.pdf

## Future Improvements

1. Filtering data by Chicago Neighborhood and including this value as a filter in the dashboard
2. Running the ETL on an automated basis so the data stays up to date