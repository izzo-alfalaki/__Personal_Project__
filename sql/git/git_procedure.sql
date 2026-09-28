create or replace procedure Git.aggregate( N int64 )
begin

declare max_date date default ( 
    select date( max( retrived_date ) ) from Git.Actions 
    );

declare min_date date default 
    date(
        date_sub(max_date, INTERVAL N day)
    );

create temp function lambda_case(field float64, treshold_field float64 ) as (
 case when field < treshold_field then 1 
 else 0 end
);

create or replace table Git_table.ActionsAggregate as 
with a as(  
  
  select 
    *, 
    avg(run_duration_ms) over ( partition by name) average_run, 
    lambda_case( run_duration_ms, avg(run_duration_ms) over (partition by name)  ) below_average 
    
  from 
    Git.Actions
  where
    date(cast(retrived_date as datetime)) between min_date and max_date
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