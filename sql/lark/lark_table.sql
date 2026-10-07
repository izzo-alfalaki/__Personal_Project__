create temp function year_calc( date_field date, day bool)
returns int64 as (
case when day then
  date_diff( date( current_datetime() ), date(date_field), day )  
else 
  date_diff( date( current_datetime() ), date(date_field), year )
end
) ;

create or replace table Lark_table.lark as

with a as(

  select 
   record_id, `date`, text.text as given_name, null as download_link 
  from `Lark.Table_Izzo`

   union all 

  select 
   record_id, `date`, name.text as given_name, attachment.url as download_link 
  from `Lark.Table_Izzo_failappend`
  
)

select * replace(
  upper(given_name) as given_name,
  datetime( `date`, 'Asia/Kuala_Lumpur' ) as `date`
  ), 
  
  row_number() over ( partition by record_id ) as id,

  concat(
    
    year_calc(date(`date`), false), ' Year ',
    year_calc(date(`date`), true) - 365 * year_calc(date(`date`), false), ' Day'

  ) as age
    
from 
  a
qualify 
  id = 1
;