# Chicago Apartments

## Overview

Common questions when apartment hunting are "How much should I expect to pay?", "What's the average rent for this area?", or "How much space can I afford?". This project aims to help renters in the Chicago area answer those questions by providing a simple dashboard that can filtered by neighborhood, # beds, # bathrooms, and square footage. Also, analysis is included on what factors primarily drive rent higher.

## Features
This project does the following:

1. Scrapes Chicago apartment data from Apartments.com
2. Transforms and writes the data to BigQuery
3. Powers a dashboard in Looker Studio
4. Models the relationship between the extracted data and monthly rent, and creates a predictive model

## Extract

Python and the Selenium library are used to open many pages of Apartments.com search results, saving the address and listing link from all the results. The script then opens each listing and extracts key data points listed below. See `etl.py` for code.

1. Neighborhood
2. Bedrooms
3. Bathrooms
4. Monthly Rent
5. Square Feet
6. Walking Score
7. Biking Score
8. Transit Score

## Transform and Load

The extract process is repeated for listings on the north and south sides of the city, and the data is saved into two pandas dataframes. The dataframes are then written to two BigQuery tables named chicago_listings and chicago_listing_info. The first contains the listing addresses and links, and the second contains the listing info in key/value pairings (see screenshots). See `etl.py` for code.

<p align="center">
  <img src="images/chicago_listings.png" alt="chicago_listings" width="500"/>
</p>

<p align="center">
  <img src="images/chicago_listing_info.png" alt="chicago_listing_info" width="500"/>
</p>

## Dashboard

A sql query is used to bring together data from the tables so each row is one listing and the corresponding data. See `query.sql`.

This dashboard in Looker Studio looks at all the scraped listings, and shows the results based on the filters: https://lookerstudio.google.com/reporting/c21e28f4-b9f1-4e9e-a101-e06b9a4da893

Additionally, here are two Tableau visualizations:

Monthly Rent Heat Map: https://public.tableau.com/views/apartmentsmap/ChicagoApartments?:language=en-US&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link

Neighborhood Clusters: https://public.tableau.com/views/ChicagoApartments/Clusters?:language=en-US&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link

## Analysis and Modeling

`analysis.ipynb` contains exploratory data analysis and builds a predictive model for monthly rent. A function to predict rent based on inputs is included at the end.

Main analysis points
1. The collected data is statistically significant in predicting monthly rent
2. Square footage and transit availability have the highest impact on monthly rent, though all variables carry some importance
3. The model explains 68% of the data's variance (R2 = .68), and can be used to predict monthly rent

<p align="center">
  <img src="images/model_features.png" alt="model_features" width="300"/>
</p>

<p align="center">
  <img src="images/wicker_park_prediction.png" alt="wicker_park_prediction" width="300"/>
</p>

## Future Improvements

1. Running the ETL on an automated basis so the data stays up to date
2. Scraping more granular sections of the city on Apartments.com to maximize the amount of results
3. Gathering more data points to improve model accuracy