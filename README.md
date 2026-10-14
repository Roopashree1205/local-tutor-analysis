# Tutor Analysis

A working local dashboard and an AWS deployment kit based on your mini-project report. Local mode needs Python 3.10+ only; no pip install or internet connection is needed.

## Run on Windows

1. Extract the project ZIP.
2. Double-click `start.bat`, or open a terminal in this folder and run `python app.py`.
3. Open http://127.0.0.1:8000 in your browser.
4. Click **Load demo data**, or upload your own CSV. Filter by location and export the analysis as JSON.
5. Stop the server with Ctrl+C in its terminal.

The included data is synthetic. No real student information is supplied. The local server binds to this computer only; uploads are held in memory and are not saved. The interface has no login and is intended for local demonstrations.

## Dataset contract

Columns, in order: `tutor_id,student_id,subject,session_completed,rating,price,location`.
Each record describes a student–subject request associated with a tutor, or a tutor offering without a student. Leave tutor_id and all tutor metrics blank for an unassigned student request. Leave student_id blank for a tutor offering without demand. Subject and location are required. Sessions must be a nonnegative integer, prices nonnegative, ratings 0–5; missing tutor metrics may be blank. Use consistent subject labels and a consistent currency. Identical records are removed.

Demand is unique student IDs per subject. Supply is unique tutor IDs per subject. This is a count of available tutors in the dataset, not a measure of their hourly capacity. A student requesting multiple subjects counts once in each subject and once in the overall student total.

Ratios: >3 high, >1 to 3 moderate, exactly 1 balanced, <1 low; zero supply is separate. The report leaves the interval 1–3 undefined, so moderate is an explicit implementation decision. These thresholds are configurable in analytics.py. Recommended additions target no more than three students per tutor. Subject averages weight tutors equally: per-tutor ratings/prices are averaged first, then averaged across tutors. Session counts use the highest reported cumulative value per tutor, not the sum of repeated snapshots.

The classification is rule-based and recommendations use text templates. It does not train a model, forecast future demand, or call an LLM. The CSV does not contain dates suitable for a time-series forecast.

## Tests

Run `python -m unittest discover -s tests -v` from this folder.

## AWS deployment

Follow `aws/DEPLOYMENT.md`. `lambda.zip` contains the shared analysis engine and Lambda handler. No AWS resources have been created by this package. The local dashboard remains a local app; this kit deploys the report's AWS analytics pipeline, not a hosted dashboard.
