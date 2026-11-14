create temp function year_calc( date_field ANY TYPE, day bool)
returns int64 as (
case when day then
  date_diff( date( current_datetime() ), date(date_field), day )  
else 
  date_diff( date( current_datetime() ), date(date_field), year )
end
) ;

create temp function convert_num( field string)
returns float64 as (
    cast(
        replace( 
          field, ',', '' 
        ) as float64 )  
) ;

create or replace table Lark_table.modeled_salary as

with emp as (
  select * replace(
   convert_num( base_pay ) as base_pay,

   convert_num( latest_bonus_payout) as latest_bonus_payout

   # loyalty_payout

  ) from Lark.Employee
)

,b as ( 
select 
  a.employee_id, 
   upper(a.department) department, upper(a.qualification) qualification, upper(a.position) position,
   resign_notice_days_, cast(is_leaving as bool) as is_leaving, cummulative_performance, age, year_calc(date_join, False) as serve_year, 

   a.base_pay last_base_salary, a.latest_bonus_payout last_bonus, a.loyalty_payout last_loyalty, 
   ( a.base_pay + a.latest_bonus_payout + a.loyalty_payout )  as last_paid_salary,
   
   base_bonus_value,base_pay_value from emp a left join Lark.Salary x on 

   upper(a.department) = upper(x.department) and 
   upper(a.qualification) = upper(x.qualification) and
   upper(a.position) = upper(x.qualified_position)
   )
   
  select * except( base_bonus_value, base_pay_value ), 
    ( base_bonus_value + base_pay_value )  as system_payout,
    ( last_paid_salary - last_loyalty ) - ( base_bonus_value + base_pay_value ) as system_payout_drift, 
    case when base_bonus_value is null and base_pay_value is null then FALSE else TRUE end as under_schema 
    
  from b ;

SELECT
  event_date,
  daily_revenue,
  LAG(daily_revenue) OVER (ORDER BY event_date) AS previous_day_revenue,
  daily_revenue - LAG(daily_revenue) OVER (ORDER BY event_date) AS revenue_diff
FROM `project.dataset.daily_sales`;


