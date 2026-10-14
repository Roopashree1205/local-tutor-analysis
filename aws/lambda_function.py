"""S3 test event -> Athena aggregation -> DynamoDB results.
Deploy this file and analytics.py at the ZIP root.
"""
import json
import os
import time
import logging
from decimal import Decimal
from urllib.parse import unquote_plus
import boto3
from analytics import parse_csv, analyze

log = logging.getLogger()
log.setLevel(logging.INFO)

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    athena = boto3.client('athena')
    table = boto3.resource('dynamodb').Table(os.environ['RESULTS_TABLE'])
    record = event['Records'][0]['s3']
    bucket, key = record['bucket']['name'], unquote_plus(record['object']['key'])
    if bucket != os.environ['DATA_BUCKET'] or key != 'raw/tutor_data.csv':
        raise ValueError('Only the configured raw/tutor_data.csv is accepted.')
    obj = s3.get_object(Bucket=bucket, Key=key)
    if obj['ContentLength'] > 2_000_000:
        raise ValueError('Dataset exceeds 2 MB demo limit.')
    data = analyze(parse_csv(obj['Body'].read().decode('utf-8-sig')))
    # Athena independently verifies the demand/supply metrics before results are saved.
    query = "SELECT trim(subject) AS subject, count(DISTINCT nullif(trim(student_id), '')) AS demand, count(DISTINCT nullif(trim(tutor_id), '')) AS supply FROM tutor_data GROUP BY trim(subject)"
    qid = athena.start_query_execution(QueryString=query, QueryExecutionContext={'Database':os.environ['ATHENA_DATABASE']}, ResultConfiguration={'OutputLocation':os.environ['ATHENA_OUTPUT']}, WorkGroup=os.environ.get('ATHENA_WORKGROUP','primary'))['QueryExecutionId']
    deadline = time.monotonic() + 90
    while True:
        execution = athena.get_query_execution(QueryExecutionId=qid)['QueryExecution']['Status']
        state = execution['State']
        if state == 'SUCCEEDED':
            break
        if state in ('FAILED', 'CANCELLED'):
            raise RuntimeError(execution.get('StateChangeReason', state))
        if time.monotonic() >= deadline:
            athena.stop_query_execution(QueryExecutionId=qid)
            raise TimeoutError('Athena exceeded 90 seconds.')
        time.sleep(1)
    aggregates = {}
    first = True
    for page in athena.get_paginator('get_query_results').paginate(QueryExecutionId=qid):
        for row in page['ResultSet']['Rows']:
            if first:
                first = False
                continue
            values = [cell.get('VarCharValue','') for cell in row['Data']]
            aggregates[values[0]] = (int(values[1]),int(values[2]))
    expected = {s['subject']:(s['demand'],s['supply']) for s in data['subjects']}
    if aggregates != expected:
        raise ValueError('Athena and CSV results differ. Keep only one CSV in raw/ and retry after uploads finish.')
    # Immutable per-invocation snapshots avoid stale subjects and cross-run mixing.
    run_id = context.aws_request_id
    with table.batch_writer() as writer:
        for subject in data['subjects']:
            item = dict(run_id=run_id, subject=subject['subject'], analysis=subject, query_id=qid)
            writer.put_item(Item=json.loads(json.dumps(item), parse_float=Decimal))
    log.info('Analysis complete: run=%s subjects=%s records=%s', run_id, len(data['subjects']), data['records'])
    return {'statusCode':200,'run_id':run_id,'query_id':qid,'subjects':data['subjects']}
