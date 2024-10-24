with info as (
  select
    id,
    max(case when label = 'Neighborhood' then detail end) neighborhood,
    #clean data where applicable, taking high end of ranges and replacing commas and dollar signs
    max(case 
        when label = 'Bedrooms' and regexp_contains(detail,'-') then regexp_extract(detail,'- (.+) bd') 
        when label = 'Bedrooms' and regexp_contains(detail,'Studio') then '1' #mark studio as 1 bedroom
        when label = 'Bedrooms'  then regexp_extract(detail,'(.+) bd') 
        end) bedrooms,
    max(case 
        when label = 'Bathrooms' and regexp_contains(detail,'-') then regexp_extract(detail,'- (.+) ba') 
        when label = 'Bathrooms'  then regexp_extract(detail,'(.+) ba') 
        end) bathrooms,
    max(case 
        when label = 'Monthly Rent' and regexp_contains(detail,'-') then regexp_replace(regexp_extract(detail,'- \\$(.+)'),',','')
        when label = 'Monthly Rent' and detail = 'Call for Rent' then null
        when label = 'Monthly Rent' then regexp_replace(regexp_extract(detail,'\\$(.+)'),',','')
        end) monthly_rent,
    max(case 
        when label = 'Square Feet' and regexp_contains(detail,'-') then regexp_replace(regexp_extract(detail,'- (.+) sq') ,',','')
        when label = 'Square Feet' and detail = '' then null
        when label = 'Square Feet' then regexp_replace(regexp_extract(detail,'(.+) sq'),',','')
        end) square_feet,
    #group score labels into relavent categories
    max(case when regexp_contains(label,'Walk') or label = 'Car-Dependent' then detail end) walking_score,
    max(case when regexp_contains(label,'Bike') then detail end) bike_score,
    max(case when regexp_contains(label,'Transit|Rider') then detail end) transit_score,
  from `apartments-425401.apartments.chicago_listing_info`
  group by 1
),

listings as (
  select * from `apartments-425401.apartments.chicago_listings`
)

select
*
from listings
left join info using(id)