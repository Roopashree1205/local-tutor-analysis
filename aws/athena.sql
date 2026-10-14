-- Replace YOUR_BUCKET with your actual bucket name before running.
CREATE DATABASE IF NOT EXISTS tutor_analytics;
CREATE EXTERNAL TABLE IF NOT EXISTS tutor_analytics.tutor_data (
 tutor_id string,
 student_id string,
 subject string,
 session_completed string,
 rating string,
 price string,
 location string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ('separatorChar' = ',', 'quoteChar' = '"', 'escapeChar' = '\\')
STORED AS TEXTFILE
LOCATION 's3://YOUR_BUCKET/raw/'
TBLPROPERTIES ('skip.header.line.count'='1');

SELECT trim(subject) AS subject,
 count(DISTINCT nullif(trim(student_id), '')) AS demand,
 count(DISTINCT nullif(trim(tutor_id), '')) AS supply,
 CAST(count(DISTINCT nullif(trim(student_id), '')) AS double)
 / nullif(count(DISTINCT nullif(trim(tutor_id), '')), 0) AS ratio
FROM tutor_analytics.tutor_data GROUP BY trim(subject);
