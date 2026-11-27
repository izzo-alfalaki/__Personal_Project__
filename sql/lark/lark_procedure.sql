create or replace procedure Lark.model()
begin

create or replace table Lark.ItemLiftPosition as
with a as(
select 
  category, item_name, rack_value, column_position, row_position, 
  
  upper(concat( rack_value, " ", column_position, "-", row_position )) as current_position  from `Lark.Rack`

)

select 
  item_pair1, x.current_position as pair1_pos, x.category as pair1_category,
  item_pair2, y.current_position as pair2_pos, y.category as pair2_category,

  z.* except(item_pair1, item_pair2 )
  
from `GenData.ItemLift` z
 left join a x on 
  Item_pair1 = x.item_name
 left join a y on
  item_pair2 = y.item_name

WHERE z.item_pair1 < z.item_pair2
;

create or replace table Lark.ItemDemographic as 

# item most likely to be return
with a as(
 select 
  transaction_id, `date`, returned_item_id,
  --count( distinct (returned_item_id)) var_count_return, 
  sum( total_item_return ) as return_qty 

from (
SELECT
    transaction_id, 
    `date`,
    returned_item_id,
    off,
    returned_item_quantity[ safe_offset(off )] as total_item_return

  FROM `GenData.TransactionData`, 

  unnest(  returned_item ) as returned_item_id with offset as off
)

group by transaction_id, `date`, returned_item_id
) 
, b as (
select a.*, x.name, x.category from a left join GenData.Appendix x on returned_item_id = id
)
,x as (
select 
  transaction_id, `date`, confirmed_item_id,
  --count( distinct (returned_item_id)) var_count_return, 
  sum( total_item_confirm ) as confirm_qty 

from (
  SELECT
    transaction_id, 
    `date`,
    confirmed_item_id,
    off,
    confirmed_item_quantity[ safe_offset(off )] as total_item_confirm

  FROM `GenData.TransactionData`, 

  unnest(  confirmed_item ) as confirmed_item_id with offset as off
)

group by transaction_id, `date`, confirmed_item_id

)
, y as (
select x.*, z.name, z.category from x left join GenData.Appendix z on confirmed_item_id = id
)

,final as(
select 
  y.transaction_id, y.date, y.confirmed_item_id as id, y.name, y.category, 
  y.confirm_qty, b.return_qty 
  
from y left join b on y.transaction_id = b.transaction_id and y.date = b.date
)


select 
  case when extract( hour from date ) > 15 then '15:00 to 23:00' else '08:00 to 15:00' end as shift,
  format_datetime( '%A', `date`) as day,
  
  name,
  final.category,

  rack.row_position,
  rack.column_position,

  sum( confirm_qty ) as sold_qty,
  sum( return_qty ) as return_qty


from final left join Lark.Rack rack on final.name = rack.item_name  

group by shift, day, name, final.category,   rack.row_position, rack.column_position ;

create or replace table Lark.ReturnPerStaff as
# return activity
# does defect of staff count in certain department make return trip more
with a as( 

select 
  date( `date` ) as `date`,
  format_datetime( '%A' , `date` ) as `day`, 
  case when extract( hour from `date`) > 15 then '15:00 to 23:00' else '08:00 to 15:00' end as shift, 

  count( distinct( transaction_id ) ) trip_with_return 
  
from (
  select transaction_id, `date`, returned_item from `GenData.TransactionData` 
  where array_length( returned_item ) > 0
  )
 group by `Date`, format_datetime( '%A' , `date` ), shift
 order by date desc 
 
)

, b as (
select
  date( `date` ) as `date`,
  format_datetime( '%A' , `date` ) as `day`, 
  case when extract( hour from `date`) > 15 then '15:00 to 23:00' else '08:00 to 15:00' end as shift, 

  count( distinct( transaction_id ) ) total_trip
from `GenData.TransactionData`
 group by `Date`, format_datetime( '%A' , `date` ), shift
 order by date desc 

)

select a.* 
  replace( trip_with_return / ( trip_with_return + b.total_trip)  as trip_with_return) 
  ,  
  array_length( cashier ) + array_length( supporting_cashier ) cashier_availability,
  array_length( receptionist ) + array_length( supporting_receptionist ) recep_availability,
  array_length( store_operator ) + array_length( supporting_store ) store_availability,
  array_length(all_on_duty) as total_availability
  
from a 
  left join Lark.Schedule x 
  on a.day = x.day 
  and trim(upper(a.shift)) = trim(upper(x.shift))
  
  left join b
    on a.day = b.day 
    and trim(upper(a.shift)) = trim(upper(b.shift))
    and a.date = b.date
;

end;


