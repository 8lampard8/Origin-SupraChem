"""Origin embedded Python: inspect_project.py <output.json>. Read-only."""
import json
import math
from pathlib import Path
import sys
import originpro as op


def main():
    target = Path(sys.argv[1]); target.parent.mkdir(parents=True, exist_ok=True)
    books = []
    for book in op.pages('w'):
        sheets = []
        for sheet in book:
            record = dict(name=sheet.name, rows=sheet.rows, cols=sheet.cols,
                          labels=sheet.get_labels('L'), units=sheet.get_labels('U'),
                          comments=sheet.get_labels('C'))
            if sheet.name.lower().startswith(('data', 'xyz')):
                record['columns'] = []
                for i in range(sheet.cols):
                    values = sheet.to_list(i)
                    finite = [v for v in values if isinstance(v, (int, float)) and math.isfinite(v)]
                    record['columns'].append(dict(length=len(values), finite_count=len(finite),
                        first_finite=finite[:3], last_finite=finite[-3:],
                        minimum=min(finite) if finite else None, maximum=max(finite) if finite else None))
            sheets.append(record)
        books.append(dict(name=book.name, long_name=book.lname, sheets=sheets))
    target.write_text(json.dumps(dict(project_name=op.get_lt_str('%G'),
        project_directory=op.get_lt_str('%X'), books=books), ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
