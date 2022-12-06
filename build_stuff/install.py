#!/usr/bin/env python3

import json
import os
import sys
import shutil

INVALID_PLATFORM_MESSAGE = f'Mod Development Tools is a linux program and should ' \
                           f'not be installed on {sys.platform}. To override this, run with --force'

ROOT_MESSAGE = f'Permission denied. Are you root? If not, try installing to a local directory'

INSTALL_DIR = '/opt'
FORCE_INSTALL = False
ROOT_NEEDED = True


def get_input():
    global FORCE_INSTALL, INSTALL_DIR, ROOT_NEEDED
    install_dir = input('install directory (default /opt): ')
    if len(sys.argv) > 1:
        if sys.argv[1] == '--force':
            FORCE_INSTALL = True
    if sys.platform not in ['linux', 'linux1', 'linux2'] and FORCE_INSTALL is False:
        print(INVALID_PLATFORM_MESSAGE)
        sys.exit(0)
    if install_dir != '':
        if os.path.isdir(os.path.abspath(install_dir)):
            INSTALL_DIR = os.path.abspath(install_dir)
        else:
            print(f'{os.path.abspath(install_dir)} is not a directory.')
            sys.exit(0)
    if os.geteuid() == 0:
        pass
    elif os.access(INSTALL_DIR, os.W_OK) and os.access(INSTALL_DIR, os.R_OK) and os.access(INSTALL_DIR, os.X_OK) and os.access(INSTALL_DIR, os.X_OK | os.W_OK):
        ROOT_NEEDED = False
    else:
        print(ROOT_MESSAGE)
        sys.exit(0)


def install():
    stage_dir = os.path.abspath(os.path.split(__file__)[0])
    shutil.copytree(os.path.join(stage_dir, 'mdt'), os.path.join(INSTALL_DIR, 'mdt'))
    if ROOT_NEEDED is True:
        with open(os.path.join(INSTALL_DIR, 'mdt', 'config.json'), 'r') as f:
            config = json.load(f)
        config['root'] = ROOT_NEEDED
        with open(os.path.join(INSTALL_DIR, 'mdt', 'config.json'), 'w') as f:
            json.dump(config, f, indent=2)
        os.symlink(os.path.join(INSTALL_DIR, 'mdt', 'main'), os.path.join('/usr', 'bin', 'mdt'))


def cleanup():
    pass


if __name__ == '__main__':
    get_input()
    install()
    cleanup()

