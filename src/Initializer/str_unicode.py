import sys

IS_PY3 = sys.version_info >= (3, 0)

if IS_PY3:
    unicode = str