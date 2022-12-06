#!/usr/bin/env python3

import os
import subprocess
import shutil


__VERSION__ = '1.0.0_beta'


def setup():
    os.mkdir(f'mdt_{__VERSION__}')
    shutil.copy(os.path.join('build_stuff', 'install.py'), os.path.join(f'mdt_{__VERSION__}', 'install.py'))


def build():
    subprocess.call(['pyinstaller', 'main.py'])
    shutil.copytree(os.path.join('dist', 'main'), os.path.join(f'mdt_{__VERSION__}', 'mdt'))
    shutil.copy('config.json', os.path.join(f'mdt_{__VERSION__}', 'mdt', 'config.json'))
    shutil.make_archive(f'mdt_{__VERSION__}', 'zip', f'mdt_{__VERSION__}')
    shutil.rmtree(f'mdt_{__VERSION__}')


def cleanup():
    shutil.rmtree('build')
    shutil.rmtree('dist')
    os.remove('main.spec')


if __name__ == '__main__':
    print(f'Building Mod Development Tools version {__VERSION__}')
    print('Creating directory structure...')
    setup()
    print('Building with pyinstaller...\n')
    build()
    print('Cleaning up...')
    cleanup()
    print('Build successful!')

