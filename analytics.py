"""Shared, dependency-free analysis for the local app and AWS Lambda."""
import csv
import io
import math
from collections import defaultdict

COLUMNS = ['tutor_id', 'student_id', 'subject', 'session_completed', 'rating', 'price', 'location']

def parse_csv(text):
    reader = csv.DictReader(io.StringIO(text.lstrip('\ufeff')))
    if reader.fieldnames != COLUMNS:
        raise ValueError('CSV columns must be in this order: ' + ','.join(COLUMNS))
    rows, seen = [], set()
    for line, raw in enumerate(reader, 2):
        if None in raw or any(v is None for v in raw.values()):
            raise ValueError(f'Row {line}: wrong number of columns.')
        row = {k: v.strip() for k, v in raw.items()}
        if not row['subject'] or not row['location'] or not (row['tutor_id'] or row['student_id']):
            raise ValueError(f'Row {line}: subject, location and a tutor or student ID required.')
        try:
            for key in ['session_completed', 'rating', 'price']:
                row[key] = float(row[key]) if row[key] else None
                if row[key] is not None and (not math.isfinite(row[key]) or row[key] < 0):
                    raise ValueError()
            if row['rating'] is not None and row['rating'] > 5:
                raise ValueError()
            if row['session_completed'] is not None and not row['session_completed'].is_integer():
                raise ValueError()
            if not row['tutor_id'] and any(row[k] is not None for k in ['rating', 'price', 'session_completed']):
                raise ValueError()
        except ValueError:
            raise ValueError(f'Row {line}: use nonnegative numbers, integer sessions, ratings 0–5; leave tutor metrics blank for requests without a tutor.')
        signature = tuple(row.values())
        if signature in seen:
            continue
        seen.add(signature)
        rows.append(row)
    if not rows:
        raise ValueError('CSV has no records.')
    return rows

def classify(demand, supply):
    if not supply:
        return 'No supply' if demand else 'No activity'
    ratio = demand / supply
    return 'High demand' if ratio > 3 else 'Moderate demand' if ratio > 1 else 'Balanced' if ratio == 1 else 'Low demand'

def analyze(rows, location=''):
    rows = [r for r in rows if not location or r['location'] == location]
    groups = defaultdict(list)
    for row in rows:
        groups[row['subject']].append(row)
    results, tutors = [], []
    for subject, records in sorted(groups.items()):
        demand = len({r['student_id'] for r in records if r['student_id']})
        ids = {r['tutor_id'] for r in records if r['tutor_id']}
        supply = len(ids)
        category = classify(demand, supply)
        metrics = {}
        for key in ['rating', 'price', 'session_completed']:
            per_tutor = []
            for tutor_id in sorted(ids):
                values = [r[key] for r in records if r['tutor_id'] == tutor_id and r[key] is not None]
                if values:
                    per_tutor.append(max(values) if key == 'session_completed' else sum(values)/len(values))
            metrics[key] = round(sum(per_tutor)/len(per_tutor), 2) if per_tutor else None
        target = math.ceil(demand / 3)
        additional = max(0, target - supply)
        insight = f'{subject}: {demand} unique students and {supply} tutors. '
        insight += f'Add at least {additional} tutors to reach at most 3 students per tutor.' if additional else 'Monitor availability and allocate tutors according to student needs.'
        results.append(dict(subject=subject, demand=demand, supply=supply, ratio=round(demand/supply, 2) if supply else None, category=category, additional_tutors=additional, insight=insight, **metrics))
        for tutor_id in sorted(ids):
            own = [r for r in records if r['tutor_id'] == tutor_id]
            ratings = [r['rating'] for r in own if r['rating'] is not None]
            prices = [r['price'] for r in own if r['price'] is not None]
            tutors.append(dict(tutor_id=tutor_id, subject=subject, students=len({r['student_id'] for r in own if r['student_id']}), rating=round(sum(ratings)/len(ratings), 2) if ratings else None, price=round(sum(prices)/len(prices), 2) if prices else None, sessions=max((r['session_completed'] or 0 for r in own), default=0)))
    return dict(subjects=results, tutors=tutors, summary=dict(students=len({r['student_id'] for r in rows if r['student_id']}), tutors=len({r['tutor_id'] for r in rows if r['tutor_id']}), subjects=len(results), shortages=sum(r['category'] in ['High demand', 'No supply'] for r in results)), locations=sorted({r['location'] for r in rows}), records=len(rows))
