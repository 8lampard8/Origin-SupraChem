"""Reusable spectrum helpers. No Origin import until smooth_column is called."""
import math
import statistics


def validate_xy(x, y):
    if len(x) != len(y) or len(x) < 3:
        raise ValueError('Need equal-length X/Y with at least three points')
    if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in list(x) + list(y)):
        raise ValueError('Non-numeric or missing values: decide explicitly how to handle them')
    if not all(x[i] < x[i+1] for i in range(len(x)-1)):
        raise ValueError('Wavelengths must be strictly increasing')


def highest_peak(x, y, threshold=420):
    """Highest interior local peak > threshold; flat tops use the first qualifying point.
    Returns a one-based source row. None means no local peak, never a zero substitute.
    """
    validate_xy(x, y)
    candidates = []
    i = 1
    while i < len(y)-1:
        end = i
        while end+1 < len(y) and y[end+1] == y[i]:
            end += 1
        if end < len(y)-1 and y[i] > y[i-1] and y[end] > y[end+1]:
            eligible = [k for k in range(i, end+1) if x[k] > threshold]
            if eligible:
                k = eligible[0]
                candidates.append(dict(intensity=y[k], wavelength=x[k], row=k+1))
        i = end+1
    return max(candidates, key=lambda p: p['intensity']) if candidates else None


def variance_summary(values):
    values = list(values)
    if len(values) < 2 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values):
        raise ValueError('At least two finite peak values are required for sample variance')
    mean = statistics.mean(values)
    sample, population = statistics.variance(values), statistics.pvariance(values)
    ss = math.fsum((v-mean)**2 for v in values)
    if not math.isclose(sample, ss/(len(values)-1), rel_tol=1e-10, abs_tol=1e-12):
        raise ArithmeticError('Independent variance check failed')
    return dict(n=len(values), mean=mean, sample_variance=sample,
                population_variance=population, sample_sd=math.sqrt(sample))


def verify_sg_interior(raw, smooth, window=25):
    """Verify order-2 unweighted SG interior only; Origin owns endpoint behavior."""
    if window < 3 or window % 2 != 1 or len(raw) < window or len(raw) != len(smooth):
        raise ValueError('Invalid SG window or data length')
    if not all(math.isfinite(v) for v in list(raw)+list(smooth)):
        raise ValueError('Nonfinite SG values')
    m = window//2
    weights = [3*(3*m*m+3*m-1-5*k*k)/((2*m+1)*(4*m*m+4*m-3)) for k in range(-m,m+1)]
    max_error = 0.0
    for i in range(m, len(raw)-m):
        expected = math.fsum(w*v for w,v in zip(weights,raw[i-m:i+m+1]))
        error = abs(smooth[i]-expected); max_error = max(max_error,error)
        if error > 1e-6 + abs(expected)*1e-9:
            raise ArithmeticError(f'SG mismatch at row {i+1}: {error}')
    return max_error


def smooth_column(sheet, xcol, ycol, window=25):
    """In-place Origin SG25/order2/None; zero-based column indexes. Call once per raw series."""
    import originpro as op
    x, raw = sheet.to_list(xcol), sheet.to_list(ycol)
    validate_xy(x, raw)
    if window < 3 or window % 2 != 1 or len(raw) < window:
        raise ValueError('Window must be odd, >=3, and no longer than data')
    labels = {t:sheet.get_label(ycol,t) for t in ['L','U','C']}
    book = sheet.get_book()
    # Expected sheets created by the task have simple identifiers, avoiding LT quoting issues.
    if not all(name.replace('_','').isalnum() for name in [book.name,sheet.name]):
        raise ValueError('Use a simple alphanumeric output book/sheet name for this helper')
    ref=f'[{book.name}]{sheet.name}!({xcol+1},{ycol+1})'
    sheet.activate()
    op.lt_exec(f'smooth -r 0 iy:={ref} method:=sg npts:={window} boundary:=none polyorder:=2 oy:={ref};')
    output=sheet.to_list(ycol)
    if sheet.to_list(xcol) != x:
        raise ArithmeticError('Smoothing unexpectedly changed X')
    verify_sg_interior(raw, output, window)
    for t,v in labels.items():sheet.set_label(ycol,v,t)
    sheet.set_label(ycol,labels['C']+f'; SG window={window}, order=2, boundary=None','C')
    return output
