# AWS Academy / AWS deployment guide

Architecture: CSV in S3 -> Athena queries -> Python Lambda validates/classifies -> DynamoDB snapshots. CloudWatch records execution metadata. You need an active AWS session and permission to use these services. Learner Lab permissions differ; use its existing LabRole if custom roles are prohibited. Never paste credentials into project files.

## 1. S3

Create a uniquely named private S3 bucket in your chosen AWS region. Enable Block Public Access, default encryption, and a policy denying requests with aws:SecureTransport=false. Create raw/ and athena-results/ prefixes. Upload data/tutor_data.csv to raw/tutor_data.csv. Keep exactly one CSV under raw/, with the expected column order and no embedded newlines in fields. Results belong outside raw/ so Athena cannot accidentally read them as input.

## 2. Athena

Set the Athena query result location to s3://YOUR_BUCKET/athena-results/. In athena.sql replace YOUR_BUCKET. Run CREATE DATABASE first, CREATE TABLE second, and SELECT third as separate queries. Verify the subject counts. Columns are strings to tolerate blank tutor metrics; OpenCSVSerde handles quoted CSV, and skip.header.line.count skips headers.

## 3. DynamoDB

Create TutorPerformance with partition key run_id (String) and sort key subject (String), using on-demand capacity. Use the default AWS-owned encryption key. Each invocation stores a separate complete snapshot; query by the run_id returned by Lambda. This uses subject-level records rather than the report's tutor_id key because the stored results describe subjects.

## 4. Lambda

Create DemandSupplyAlert using Python 3.12 and an authorized execution role. Upload ../lambda.zip. Set handler lambda_function.lambda_handler, timeout 120 seconds, memory 256 MB. Set these environment variables:

| Name | Value |
| --- | --- |
| DATA_BUCKET | Your bucket name |
| RESULTS_TABLE | TutorPerformance |
| ATHENA_DATABASE | tutor_analytics |
| ATHENA_OUTPUT | s3://YOUR_BUCKET/athena-results/ |
| ATHENA_WORKGROUP | primary, or your permitted workgroup |

The execution role needs CloudWatch log creation/writes; s3:GetObject for raw/tutor_data.csv; s3:ListBucket and GetBucketLocation for the bucket; GetObject/PutObject for athena-results/*; Athena StartQueryExecution/GetQueryExecution/GetQueryResults/StopQueryExecution for the selected workgroup; Glue GetDatabase/GetTable/GetPartitions for this catalog/database/table; dynamodb:BatchWriteItem for TutorPerformance. Scope resources to your account, region, bucket, workgroup, catalog, database, table and log group. If using a customer KMS key, add the appropriate key permissions. LabRole may already have the necessary access; verify rather than modifying restricted roles.

## 5. Test and verify

Replace YOUR_BUCKET in test-event.json and use it as a Lambda console test event. Ensure uploads are finished before invoking. The function reads and validates the CSV, waits for Athena, verifies Athena's unique counts against its local computation, and stores per-subject results. Check statusCode=200, run_id, query_id, and subjects. In DynamoDB query run_id to see the complete snapshot; in CloudWatch check the completion log. This is a console-driven workflow. After this works, optionally add an S3 ObjectCreated trigger filtered to raw/tutor_data.csv; never trigger on athena-results/.

Test high demand, ratio=3, ratio=1, zero supply, blank metrics, malformed CSV and repeated rows. Compare with the local dashboard. Zero supply should have ratio=null and category=No supply. Uploading invalid data should fail before storage. Avoid simultaneous overwrites while an analysis is running: this demo does not implement version-pinned input or transactionally publish a latest snapshot. If a batch write fails, inspect the run for partial records and rerun after fixing permissions.

## Operations

Set a short CloudWatch retention period, monitor lab credits, and use only small demonstration files. Athena polling is limited to 90 seconds; the overall Lambda timeout is 120. For larger files use an asynchronous orchestrator and partitioned data rather than extending this demonstration unboundedly. Lab resources may persist or be removed depending on your academy setup; verify them at each session. Delete resources you no longer need through the console after preserving your data.

Official references:
- https://docs.aws.amazon.com/athena/latest/ug/csv-serde.html
- https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html
- https://docs.aws.amazon.com/lambda/latest/dg/python-package.html

The ZIP uses boto3 supplied by the Lambda runtime for a small lab demonstration. For production, package and pin boto3 and its dependencies as recommended in AWS's deployment documentation. AWS deployment and account permissions still require verification in your own account.
