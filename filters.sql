-- Alert: indoor slots, on weekends, excluding RQT Spot and singles courts
SELECT * FROM slots 
WHERE court_type='indoor' 
AND (weekday='Sunday' OR weekday='Saturday') 
AND venue IN ('Interpadel Warszawa', 'Warsaw Padel Club')
AND start_time BETWEEN '09:00:00' AND '21:00:00' -- evening slots
AND NOT (court LIKE '%singiel%' or court LIKE '%single%') -- excluding singles courts
ORDER BY date, start_time -- the newest up in the list 
LIMIT 100; 
