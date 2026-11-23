CREATE OR REPLACE PROCEDURE `izzo-472202.Git.aggregate`()
begin
CREATE OR REPLACE TABLE Git.GitActionsAgg as 
select 
 name, date(created_at) as `date`, repository_full_name, 
 count(id) as dispatch_count,

 max( run_number) as commulative_run_number,
 sum( run_number) as sum_run_number,    
 
 max( run_started_at ) as last_run, max( updated_at ) as last_update, 
 avg( run_duration_ms ) as avg_minutes_consumption 
  
from Git.GitActions 

group by 
  name, date(created_at), repository_full_name;

end;

CREATE OR REPLACE PROCEDURE `i
zzo-472202.Git.model`(N INT64)
begin

declare max_date date default ( 
    select date( max( 
      cast( left( unique_timestamp, 19 ) as datetime) 
      ) ) from Git.GitActions 
    );

declare min_date date default 
    date(
        date_sub(max_date, INTERVAL N day)
    );

create temp function lambda_case(field float64, treshold_field float64 ) as (
 case when field < treshold_field then 1 
 else 0 end
);

create temp function lambda_date(field string ) as (
 case when length( field ) > 19 then
 cast( left( field, 19  ) as datetime)
 else null end 
);

create or replace table Git.ActionsModel as 
with a as(  
  
  select 
    *, 
    avg(run_duration_ms) over ( partition by name) average_run, 
    lambda_case( run_duration_ms, avg(run_duration_ms) over (partition by name)  ) below_average 
    
  from 
    Git.GitActions
  where
    lambda_date( unique_timestamp ) between min_date and max_date
  )

select 
  name as workflow_name, 
  actor_type as triggering_actor,
  count(job_id) as total_run, 
  sum(below_average) as below_avg_count, 
  round(  (sum(below_average) / count(job_id)), 2) below_avg_rate, 
  --avg(run_duration_ms)
  safe_divide(
    sum(run_duration_ms), sum(run_attempt)) 
     as avg_run_time_minutes,
  max( run_started_at) as latest_run,
  min( run_started_at ) as first_run 

from 
  a 

group by 
  name, actor_type;

end;