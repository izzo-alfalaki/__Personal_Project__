create temp function convert_num( field string)
returns float64 as (
    safe_cast(
        replace( 
          replace( field, ' ', ''), ',', '' 
        ) as float64 )  
) ;

create temp function time_indit( field string)
returns int64 as (

  safe_cast( format_datetime('%Y%m', safe_cast(
      left(field, 19) as datetime ) )
    as int64)

);

create or replace table Lark_table.modeled_employee as
with a as(
  select 

  employee_id, department, qualification, position, is_leaving,
  age, date_join, 
  
  avg(convert_num(base_pay)) base_pay, 
  avg(convert_num(latest_bonus_payout)) bonus_payout, 
  avg(loyalty_payout) loyalty_payout, 
  avg( cummulative_performance ) cummulative_performance,  
  
  format_datetime('%Y%m', cast(
      left(unique_timestamp, 19) as datetime ) )  timeindicator
  
from `Lark.Employee`
  
  group by 
  employee_id, department, qualification, position, is_leaving,
  age, date_join,
  format_datetime('%Y%m', cast(
      left(unique_timestamp, 19) as datetime ) )
)

select 

  employee_id, department, qualification, position, is_leaving,
  age, abs(datetime_diff(date_join, datetime(current_timestamp()), year )) serve_year, 
  lag ( base_pay)  over (
    order by cast(
      timeindicator as int64 ) ) base_pay_diff, 
  
  lag(bonus_payout)  over (
    order by cast(
      timeindicator as int64 ) ) bonus_pay_diff, 
  
  lag(loyalty_payout)  over (
    order by cast(
      timeindicator as int64 ) ) loyalty_pay_diff, 
  
  lag( cummulative_performance ) over (
    order by cast(
      timeindicator as int64 ) ) performance_increment
  
from a;


