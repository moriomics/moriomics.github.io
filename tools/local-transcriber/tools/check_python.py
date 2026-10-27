"""Reject mismatched interpreters before setup/build. Standard library only."""
import struct
import sys
import sysconfig

if sys.version_info[:2] != (3, 14):
    raise SystemExit('Python 3.14 is required. Install it and rerun setup_windows.bat.')
if struct.calcsize('P') * 8 != 64:
    raise SystemExit('64-bit Python is required.')
if sysconfig.get_config_var('Py_GIL_DISABLED'):
    raise SystemExit('Use standard CPython 3.14 with GIL, not the free-threaded 3.14t build.')
print('Python 3.14 x64 (standard GIL build): OK')
