import sys
import os
import shutil

PWD = os.path.abspath(os.path.dirname(__file__))


def get_python_version():
    version_info = sys.version_info
    major, minor = version_info.major, version_info.minor

    if major == 3 and minor in (9, 10, 12):
        return f"{major}.{minor}"

    raise Exception('Unsupported Python version.')


version = get_python_version()

if not os.path.exists(f'{PWD}/api'):
    if '3.10' in version:
        shutil.copytree(f'{PWD}/_CB/api3_10', f'{PWD}/api')
    elif '3.9' in version:
        shutil.copytree(f'{PWD}/_CB/api3_9', f'{PWD}/api')
    else:
        print(f'Invalid python version: {version}')


if not os.path.exists(f'{PWD}/models'):
    if '3.10' in version:
        shutil.copytree(f'{PWD}/_CB/models3_10', f'{PWD}/models')
    elif '3.9' in version:
        shutil.copytree(f'{PWD}/_CB/models3_9', f'{PWD}/models')
    else:
        print(f'Invalid python version: {version}')


from . import models
