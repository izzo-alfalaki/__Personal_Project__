WITH ranked_events AS (
    SELECT
        record_id,
        updated_at,
        ROW_NUMBER() OVER (
            PARTITION BY record_id
            ORDER BY updated_at DESC
        ) AS rn
    FROM staging_events
)
SELECT
    record_id,
    updated_at
FROM ranked_events
WHERE rn = 1;