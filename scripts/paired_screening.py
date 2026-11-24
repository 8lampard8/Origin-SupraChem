"""Build editable Origin worksheets and linear response/EF charts from paired intensities."""

import argparse
from dataclasses import dataclass
import json
from math import ceil, floor, isclose, isfinite, isnan, log10, nan
from pathlib import Path


@dataclass(frozen=True)
class Condition:
    name: str
    shared_blank: float | None
    rows: list[tuple[str, float, float, float]]


def intensity(value, *, allow_missing=False):
    if value is None and allow_missing:
        return nan
    if type(value) not in (int, float) or not isfinite(value):
        raise ValueError('Intensity must be a finite number, or null for a missing sample reading.')
    return float(value)


def load_conditions(document):
    conditions = []
    for item in document['conditions']:
        name = item['name'].strip()
        shared = intensity(item['blank']) if 'blank' in item else None
        rows = []
        for row in item['rows']:
            if shared is None:
                label, blank, first, second = row
                blank = intensity(blank)
            else:
                label, first, second = row
                blank = shared
            rows.append((label.strip(), blank, intensity(first, allow_missing=True),
                         intensity(second, allow_missing=True)))
        if not name or not rows or any(not row[0] for row in rows):
            raise ValueError('Provide a condition name and at least one named sample row.')
        conditions.append(Condition(name, shared, rows))
    if not conditions:
        raise ValueError('Provide at least one condition.')
    return conditions


def response(blank, first, second):
    delta_first, delta_second = first - blank, second - blank
    mag_first, mag_second = abs(delta_first), abs(delta_second)
    ef = max(mag_first, mag_second) / min(mag_first, mag_second) if mag_first > 0 and mag_second > 0 else nan
    return delta_first, delta_second, mag_first, mag_second, ef


def stage_columns(condition):
    values = []
    for index, (label, blank, first, second) in enumerate(condition.rows, start=1):
        dl, dd, ml, md, ef = response(blank, first, second)
        values.append((label, blank, first, second, dl, dd, ml, md, ef, index,
                       index - 0.19, index + 0.19, max(dl, 0), max(-dl, 0),
                       max(dd, 0), max(-dd, 0)))
    return list(zip(*values))


def linear_limits(columns, indices):
    peak = max((value for table in columns for index in indices for value in table[index]
                if isfinite(value)), default=1)
    target = max(peak, 1) * 1.28
    decade = 10 ** floor(log10(target / 5))
    step = next(multiplier * decade for multiplier in (1, 2, 2.5, 5, 10)
                if multiplier * decade >= target / 5)
    ticks = [step * i for i in range(ceil(target / step) + 1)]
    return ticks[-1], step, ticks


def add_worksheets(book, condition, index, columns, unit, pair_labels):
    raw = book[0] if index == 1 else book.add_sheet()
    raw.name = f'Raw{index}'
    raw.cols = 4
    first_label, second_label = pair_labels
    raw_names = ['Sample', 'Matched blank', f'{first_label} intensity', f'{second_label} intensity']
    raw_values = [list(column) for column in columns[:4]]
    shared = condition.shared_blank is not None
    if shared:
        raw_values = [['Blank', *raw_values[0]], [condition.shared_blank] + [None] * len(condition.rows),
                      [None, *raw_values[2]], [None, *raw_values[3]]]
    for col, (name, values) in enumerate(zip(raw_names, raw_values)):
        raw.from_list(col, values, lname=name, units=unit if col else '', comments=condition.name)

    sheet = book.add_sheet(f'Calc{index}')
    names = raw_names + [
        f'{first_label} signed ΔI', f'{second_label} signed ΔI',
        f'{first_label} |ΔI|', f'{second_label} |ΔI|', 'EF',
        'Sample row', f'{first_label} bar row', f'{second_label} bar row',
        f'{first_label} increase', f'{first_label} decrease',
        f'{second_label} increase', f'{second_label} decrease',
    ]
    sheet.cols = len(names)
    for col, (name, values) in enumerate(zip(names, columns)):
        comment = 'Larger divided by smaller |ΔI|; undefined for zero or missing response.' if col == 8 else condition.name
        sheet.from_list(col, list(values), lname=name, comments=comment,
                        units=unit if 1 <= col <= 7 or col >= 12 else '',
                        axis='X' if 9 <= col <= 11 else 'Y')

    sheet.activate()
    count = len(condition.rows)
    source = f'[{book.name}]{raw.name}!'
    first_row = 2 if shared else 1
    for column in 'BCD':
        blank_cell = shared and column == 'B'
        selector = '' if blank_cell else f'[{first_row}:{first_row + count - 1}]'
        expression = 'rawInput[1]' if blank_cell else 'rawInput'
        sheet.lt_exec(f'csetvalue col:=col({column})[1:{count}] formula:="{expression}" '
                      f'script:="range rawInput={source}col({column}){selector};" recalculate:=auto;')

    formulas = {
        'E': 'col(C)-col(B)', 'F': 'col(D)-col(B)',
        'G': 'abs(col(E))', 'H': 'abs(col(F))',
        'I': '(col(G)+col(H)+abs(col(G)-col(H)))/(col(G)+col(H)-abs(col(G)-col(H)))',
        'K': 'col(J)-0.19', 'L': 'col(J)+0.19',
        'M': '(col(G)+col(E))/2', 'N': '(col(G)-col(E))/2',
        'O': '(col(H)+col(F))/2', 'P': '(col(H)-col(F))/2',
    }
    for col, expression in formulas.items():
        sheet.lt_exec(f'csetvalue col:=col({col})[1:{count}] formula:="{expression}" recalculate:=auto;')
    return sheet


def check_columns(sheet, expected):
    for col, values in enumerate(expected):
        actual = sheet.to_list(col)
        if len(actual) != len(values):
            raise ValueError(f'{sheet.name} column {col + 1} has an unexpected row count.')
        if col == 0:
            valid = tuple(actual) == values
        else:
            valid = all(isnan(a) if isnan(b) else isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)
                        for a, b in zip(actual, values))
        if not valid:
            raise ValueError(f'{sheet.name} column {col + 1} differs from the calculated values.')


def add_text(layer, name, value, x, y, size, color='color(34,34,34)', bold=False):
    layer.activate()
    layer.lt_exec(f'label -p 50 50 -n {name} Text;')
    label = layer.label(name)
    if label is None:
        raise RuntimeError(f'Origin could not create {name}.')
    label.text = fr'\b({value})' if bold else value
    layer.lt_exec(f'{name}.font=font(Arial); {name}.fsize={size}; {name}.color={color}; '
                  f'{name}.left=page.width*(layer.left+layer.width*({x}/100))/100; '
                  f'{name}.top=page.height*(layer.top+layer.height*({y}/100))/100;')


def format_layer(layer, left, width, count, limits, color, reverse=False):
    layer.lt_exec('layer.fixed=1; layer.factor=1; layer.exchangexy=1; layer.unit=1; '
                  f'layer.left={left}; layer.width={width}; layer.top=18.5; layer.height=67.5;')
    layer.set_xlim(count + 0.5, 0.5, 1)
    maximum, step, ticks = limits
    layer.axis('y').scale = 'linear'
    low, high = (maximum, 0) if reverse else (0, maximum)
    layer.set_ylim(low, high, step)
    marks = ' '.join(f'{value:g}' for value in (ticks if reverse else ticks[1:]))
    layer.lt_exec(f'layer.y.TicksByData$="{marks}"; layer.x.showAxes=3; layer.y.showAxes=3; '
                  'layer.x.showLabels=0; layer.y.showLabels=2; layer.x.ticks=0; layer.x2.ticks=0; '
                  'layer.y.ticks=0; layer.y2.ticks=2; layer.y2.ticklength=3.5; '
                  'layer.x.thickness=0.85; layer.x2.thickness=0.85; '
                  'layer.y.thickness=0.85; layer.y2.thickness=0.85; '
                  'layer.y2.label.type=1; layer.y2.label.pt=8.25; layer.y2.label.font=font(Arial); '
                  f'layer.y2.label.color={color}; layer.y2.label.numFormat=4;')
    if count > 1:
        dividers = ' '.join(f'{row + 0.5:g}' for row in range(1, count))
        layer.lt_exec(f'layer.x.TicksByData$="{dividers}"; layer.x.showGrids=1; '
                      'layer.x.grid.majorColor=color(207,207,207); '
                      'layer.x.grid.majorType=2; layer.x.grid.majorWidth=0.45;')
    layer.axis('x').title = ''
    layer.axis('y').title = ''
    legend = layer.label('Legend')
    if legend is not None:
        layer.remove_label(legend)


def add_figure(op, sheet, condition, columns, index, response_limits, ef_limits, unit,
               pair_labels, highlights):
    graph = op.new_graph(template='bar', lname=condition.name)
    graph.name = f'Screening{index}'
    graph.lt_exec(f'page.width={round(6.5 * graph.get_float("resx"))};')
    left = graph[0]
    right = graph.add_layer()
    colors = ('color(0,169,204)', 'color(189,116,228)', 'color(26,130,123)')
    for x, y, color, decrease in [(10, 12, colors[0], False), (10, 13, colors[0], True),
                                 (11, 14, colors[1], False), (11, 15, colors[1], True)]:
        plot = left.add_plot(sheet, colx=x, coly=y, type=215)
        if decrease:
            plot.set_cmd('-pfb color(255,255,255)', '-pfp 5', f'-pfc {color}', '-pfw 0.6')
        else:
            plot.set_cmd(f'-pfb {color}')
        plot.set_cmd(f'-pbc {color}', '-pbw 0.6', '-vg 73')
        indices = [str(i) for i, (label, v) in enumerate(zip(columns[0], columns[y]), start=1)
                   if label in highlights and v > 0]
        if indices:
            sign = '-' if decrease else '+'
            plot.set_cmd('-q 1', f'-qmi {" ".join(indices)}', '-qmie 1', '-qp 4', '-qx 21',
                         '-qb 1', '-qs 8', '-qm 5', f'-j -qms {sign}$(Y)')

    ratio = right.add_plot(sheet, colx=9, coly=8, type=215)
    ratio.set_cmd(f'-pfb {colors[2]}', f'-pbc {colors[2]}', '-pbw 0.6', '-vg 58',
                  '-q 1', '-qp 4', '-qx 20', '-qc color(186,20,106)', '-qs 8',
                  '-qm 5', '-j -qms $(Y,.2)')
    count = len(condition.rows)
    red = 'color(188,54,38)'
    format_layer(left, 13.6, 52.4, count, response_limits, red, reverse=True)
    format_layer(right, 66, 30, count, ef_limits, colors[2])
    for row, name in enumerate(columns[0], start=1):
        add_text(left, f'Sample{row}', name, -19.5, (row - 0.5) / count * 100 - 1.5,
                 8.5, bold=name in highlights)
    add_text(left, 'ChartTitle', condition.name, 0, -22.5, 11, bold=True)
    add_text(left, 'ResponseTitle', f'|ΔI| ({unit})' if unit else '|ΔI|', 42, -14, 10, red, True)
    add_text(right, 'EFTitle', 'EF', 46, -14, 10, colors[2], True)
    add_text(left, 'SeriesKey', fr'\l(1) {pair_labels[0]}    \l(3) {pair_labels[1]}    \l(2) Fluorescence decrease',
             29, 107, 8.5)
    return graph


def build(document, output, png_dir):
    import originpro as op

    conditions = load_conditions(document)
    pair_labels = document.get('pair_labels', ['First', 'Second'])
    if len(pair_labels) != 2 or not all(isinstance(label, str) and label.strip() for label in pair_labels):
        raise ValueError('pair_labels must contain two nonempty names in data column order.')
    unit = document.get('unit', '')
    highlights = set(document.get('highlight', []))
    columns = [stage_columns(condition) for condition in conditions]
    response_limits = linear_limits(columns, (6, 7))
    ef_limits = linear_limits(columns, (8,))

    book = op.new_book('w', lname='Paired fluorescence readings')
    book.name = 'PairedScreening'
    book_name = book.name
    graph_names = []
    for index, (condition, values) in enumerate(zip(conditions, columns), start=1):
        sheet = add_worksheets(book, condition, index, values, unit, pair_labels)
        check_columns(sheet, values)
        graph = add_figure(op, sheet, condition, values, index, response_limits, ef_limits,
                           unit, pair_labels, highlights)
        graph_names.append(graph.name)
    book[0].activate()
    op.save(str(output))
    if not output.is_file() or not op.open(str(output), readonly=True, asksave=False):
        raise RuntimeError(f'Origin could not reopen {output}.')
    reopened = op.find_book('w', book_name)
    for index, values in enumerate(columns):
        check_columns(reopened[2 * index + 1], values)
    for name in graph_names:
        graph = op.find_graph(name)
        if graph is None or [len(layer.plot_list()) for layer in graph] != [4, 1]:
            raise RuntimeError(f'Reopened graph {name} is missing its native bar plots.')
        if png_dir is not None:
            png_dir.mkdir(parents=True, exist_ok=True)
            png = png_dir / f'{name}.png'
            graph.save_fig(str(png), width=2600)
            if not png.is_file():
                raise RuntimeError(f'Origin could not export {png}.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='JSON containing matched blanks and paired intensities')
    parser.add_argument('output', type=Path, help='New .opju file')
    parser.add_argument('--png-dir', type=Path, help='Export one PNG per condition')
    args = parser.parse_args()
    output = args.output.resolve()
    if output.suffix.lower() != '.opju' or output.exists():
        parser.error('Specify a new .opju output path.')
    output.parent.mkdir(parents=True, exist_ok=True)
    document = json.loads(args.input.read_text(encoding='utf-8-sig'))
    build(document, output, args.png_dir.resolve() if args.png_dir else None)


if __name__ == '__main__':
    main()
