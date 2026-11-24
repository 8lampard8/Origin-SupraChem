"""Run a trusted task script inside a new, visible Origin instance."""
import argparse
import json
from pathlib import Path
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', help='Existing project to load. Omit for a new project.')
    parser.add_argument('--script', required=True)
    parser.add_argument('--work', required=True)
    parser.add_argument('args', nargs=argparse.REMAINDER)
    a = parser.parse_args()
    project = Path(a.project).resolve() if a.project else None
    script = Path(a.script).resolve()
    if not script.is_file() or (project is not None and not project.is_file()):
        parser.error('The script and any specified project must exist')
    work = Path(a.work).resolve(); work.mkdir(parents=True, exist_ok=True)
    tag = uuid.uuid4().hex[:12]
    status = work / ('status_' + tag + '.json')
    wrapper = work / ('run_' + tag + '.py')
    args = a.args[1:] if a.args[:1] == ['--'] else a.args
    code = '''import runpy, sys, json, traceback
from pathlib import Path
status = Path(STATUS)
try:
    sys.path.insert(0, SCRIPT_DIR)
    sys.argv = ARGV
    runpy.run_path(SCRIPT, run_name='__main__')
    status.write_text(json.dumps({'ok': True}), encoding='utf-8')
except BaseException:
    status.write_text(json.dumps({'ok': False, 'error': traceback.format_exc()}), encoding='utf-8')
'''
    code = code.replace('SCRIPT_DIR', repr(str(script.parent))).replace('STATUS', repr(str(status))).replace('ARGV', repr([str(script)] + args)).replace('SCRIPT,', repr(str(script)) + ',')
    wrapper.write_text(code, encoding='utf-8')
    import win32com.client
    origin = win32com.client.DispatchEx('Origin.Application')
    origin.Visible = 100
    if project is not None and not origin.Load(str(project)):
        raise RuntimeError('Origin failed to load project: ' + str(project))
    command = 'run -pyf "' + wrapper.as_posix() + '";'
    if not origin.Execute(command):
        raise RuntimeError('Origin rejected script command')
    if not status.exists():
        raise RuntimeError('Script returned without status; inspect Origin. Wrapper: ' + str(wrapper))
    result = json.loads(status.read_text(encoding='utf-8'))
    print(json.dumps(dict(status=str(status), **result), ensure_ascii=False))
    if not result['ok']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
