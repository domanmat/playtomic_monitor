-- Alert: indoor double slots on weekends
SELECT ROW_NUMBER() OVER (ORDER BY date, start_time) AS No, * FROM new_slots
WHERE court_type='indoor'
AND court_size='double'
AND (weekday='Sunday' OR weekday='Saturday')
AND venue IN ('Interpadel Warszawa', 'Warsaw Padel Club')
AND start_time BETWEEN '09:00:00' AND '21:00:00'
ORDER BY date, start_time
LIMIT 100;
