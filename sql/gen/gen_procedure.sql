create or replace procedure Gen.model() begin

declare target_string array<string> ;

CREATE OR REPLACE TABLE `Gen.ConfirmedTrip` AS
SELECT
  t.transaction_id,
  t.date AS purchased_at,
  EXTRACT(HOUR FROM t.date) AS purchase_hour,
  CASE
    WHEN EXTRACT(HOUR FROM t.date) BETWEEN 6 AND 11 THEN 'morning'
    WHEN EXTRACT(HOUR FROM t.date) BETWEEN 12 AND 16 THEN 'midday'
    WHEN EXTRACT(HOUR FROM t.date) BETWEEN 17 AND 21 THEN 'evening_peak'
    ELSE 'off_peak_night'
  END AS time_slot,
  NULLIF(TRIM(t.membership_id), '') AS membership_id,
  NULLIF(TRIM(t.membership_id), '') IS NOT NULL AS has_membership,
  t.total AS trip_total,
  pos AS line_idx,
  item_id,
  t.confirmed_item_quantity[SAFE_OFFSET(pos)] AS qty,
  t.confirmed_item_price[SAFE_OFFSET(pos)] AS unit_price,
  t.confirmed_item_quantity[SAFE_OFFSET(pos)] * t.confirmed_item_price[SAFE_OFFSET(pos)] AS line_gross_amount,
  COALESCE(a.name, CONCAT('UNKNOWN_ITEM_', CAST(item_id AS STRING))) AS item,
  COALESCE(a.category, 'Uncategorized') AS category
FROM `Gen.TransactionData` AS t,
UNNEST(t.confirmed_item) AS item_id WITH OFFSET AS pos
LEFT JOIN `Gen.Appendix` AS a
  ON item_id = a.id;


set target_string = [ 'item', 'category' ];

for x in ( select INITCAP(string_) as string_ from unnest( target_string ) as string_ ) 
do

  execute immediate format( """ 
  create or replace table Gen.%sLift as
  with %s_per_trip as(
    select distinct 
      transaction_id, %s
    from Gen.ConfirmedTrip

  )
  , sum_trip as (
    select count( distinct(transaction_id) ) as total_trip from %s_per_trip # see total trip
  )
  --select count( distinct(%s) ) as total_trip from a; # see total %st

  , support_per_%s as (
    select 
      %s, count( distinct transaction_id ) as %s_trip,
      safe_divide(count( distinct transaction_id ), total_trip) %s_support

    from %s_per_trip cross join sum_trip 
    group by %s, total_trip
  )

  , support_per_pair as(
    # use %s in %s_per_trip, as 2 columns, pair1 and pair2, 
    # find support per transaction_id, not group per %s
  select 
    x.%s as %s_pair1, y.%s as %s_pair2,
    count( distinct x.transaction_id ) as pair_trip,
    safe_divide( count( distinct x.transaction_id ) , total_trip ) pair_support
  from 
    %s_per_trip x cross join sum_trip
    
    join %s_per_trip y 
    on x.transaction_id = y.transaction_id
    and x.%s <> y.%s  

    group by x.%s, y.%s, total_trip
  )
  # 
  select 

  spp.%s_pair1, spp.%s_pair2, spp.pair_trip, spp.pair_support,

  spi1.%s_support %s_support1, spi2.%s_support %s_support2, 

  safe_divide( 
    spp.pair_support, ( spi1.%s_support * spi2.%s_support ) ) as lift

  from support_per_pair spp 

  join support_per_%s spi1 on spp.%s_pair1 = spi1.%s
  join support_per_%s spi2 on spp.%s_pair2 = spi2.%s;
  """,  x.string_, x.string_, x.string_, x.string_, x.string_, x.string_, x.string_, x.string_, x.string_, x.string_, x.string_, x.string_, x.string_, x.string_, x.string_, 
        x.string_, # 16
        x.string_, x.string_, x.string_, x.string_, x.string_, x.string_, x.string_, x.string_, x.string_, x.string_, x.string_, x.string_, x.string_, x.string_, x.string_, 
        x.string_,  
        x.string_, x.string_, x.string_, x.string_, x.string_, x.string_, x.string_  # 7
        );
end for;

end;