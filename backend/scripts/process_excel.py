"""Simple Excel processing tool for the project.

Usage:
  python process_excel.py input.xlsx mapping.json output.json

The script reads the Excel file, applies mapping, computes total and ranks using existing service logic,
and writes a normalized JSON file ready for backend ingestion or quick inspection.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def load_mapping(path: Path) -> dict:
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def main():
    if len(sys.argv) < 4:
        print('Usage: python process_excel.py input.xlsx mapping.json output.json')
        sys.exit(1)

    input_xlsx = Path(sys.argv[1])
    mapping_json = Path(sys.argv[2])
    output_json = Path(sys.argv[3])

    if not input_xlsx.exists():
        print('Input file not found:', input_xlsx)
        sys.exit(1)
    if not mapping_json.exists():
        print('Mapping file not found:', mapping_json)
        sys.exit(1)

    mapping = load_mapping(mapping_json)

    header_row_number = mapping.get('header_row_number')
    header_row_index = header_row_number - 1 if header_row_number else 0
    df = pd.read_excel(input_xlsx, header=header_row_index)

    # minimal validation
    required = [mapping['id_col'], mapping['name_col'], mapping['class_col']] + mapping['component_score_cols']
    missing = [c for c in required if c not in df.columns]
    if missing:
        print('Missing columns in Excel:', missing)
        sys.exit(1)

    df2 = pd.DataFrame()
    df2['student_id'] = df[mapping['id_col']].astype(str).str.strip()
    df2['full_name'] = df[mapping['name_col']].astype(str).str.strip()
    df2['class_name'] = df[mapping['class_col']].astype(str).str.strip()

    comp = df[mapping['component_score_cols']].apply(pd.to_numeric, errors='coerce').fillna(0)

    weights = mapping.get('weights')
    if weights:
        w = pd.Series(weights)
        w = w.reindex(mapping['component_score_cols']).fillna(0).astype(float)
        if w.sum() <= 0:
            print('Invalid weights, sum <= 0')
            sys.exit(1)
        w = w / w.sum()
        df2['total_score'] = comp.mul(w, axis=1).sum(axis=1)
    else:
        df2['total_score'] = comp.sum(axis=1)

    df2['component_scores'] = comp.to_dict(orient='records')

    df2 = df2[df2['student_id'] != ''].copy()
    df2.sort_values(by=['total_score', 'student_id'], ascending=[False, True], inplace=True)
    df2['global_rank'] = df2['total_score'].rank(method='min', ascending=False).astype(int)
    df2['class_rank'] = df2.groupby('class_name')['total_score'].rank(method='min', ascending=False).astype(int)

    total_students = len(df2)
    if total_students <= 1:
        df2['percentile'] = 100.0
    else:
        df2['percentile'] = ((total_students - df2['global_rank']) / (total_students - 1) * 100).round(2)

    df2['total_score'] = df2['total_score'].round(4)

    out = {
        'contest_name': mapping.get('contest_name', 'Unnamed Contest'),
        'participants': total_students,
        'benchmark_score': float(df2['total_score'].mean().round(4)) if total_students else 0.0,
        'rows': [],
    }

    for _, r in df2.iterrows():
        out['rows'].append({
            'student_id': r['student_id'],
            'full_name': r['full_name'],
            'class_name': r['class_name'],
            'component_scores': r['component_scores'],
            'total_score': float(r['total_score']),
            'global_rank': int(r['global_rank']),
            'class_rank': int(r['class_rank']),
            'percentile': float(r['percentile']),
        })

    with output_json.open('w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print('Wrote normalized JSON to', output_json)


if __name__ == '__main__':
    main()
