#!/usr/bin/env python3

import json
import os
import sys

import mdt

__VERSION__ = '1.0.0'

OPTIONS = {
    'install': {
        'arg': {'type': str, 'required': True, 'store-to': 'package', 'help-keyword': 'package'},
        'options': [
            {'keys': ['-v', '--version'], 'arg': True, 'store-to': 'version', 'type': str, 'help': 'version to install'},
            {'keys': ['-r', '--reinstall'], 'arg': False, 'store-to': 'reinstall', 'type': None, 'help': 'reinstall program'}
        ]
    },
    'remove': {
        'arg': {'type': str, 'required': True, 'store-to': 'package', 'help-keyword': 'package'},
        'options': [
            {'keys': ['-v', '--version'], 'arg': True, 'store-to': 'version', 'type': str, 'help': 'version to uninstall'}
        ]
    },
    'list': {
        'arg': None,
        'options': []
    },
    'run': {
        'arg': {'type': str, 'required': True, 'store-to': 'package', 'help-keyword': 'package'},
        'options': [
            {'keys': ['-v', '--version'], 'arg': True, 'store-to': 'version', 'type': str, 'help': 'version to run'}
        ]
    },
    'show': {
        'arg': {'type': str, 'required': True, 'store-to': 'package', 'help-keyword': 'package'},
        'options': [
            {'keys': ['-v', '--version'], 'arg': True, 'store-to': 'version', 'type': str, 'help': 'version to show'}
        ]
    },
    'repo': {
        'arg': None,
        'options': [
            {'keys': ['-u', '--update'], 'arg': True, 'store-to': 'update_dir', 'type': str, 'help': 'directory to update from'},
            {'keys': ['-c', '--clear'], 'arg': False, 'store-to': 'clear', 'type': None, 'help': 'clear current repository before updating'},
            {'keys': ['-e', '--export'], 'arg': True, 'store-to': 'export_dir', 'type': str, 'help': 'directory to export to'}
        ]
    },
    'config': {
        'arg': {'type': str, 'required': True, 'store-to': 'package', 'help-keyword': 'package'},
        'options': []
    },
    'search': {
        'arg': {'type': str, 'required': True, 'store-to': 'search_string', 'help-keyword': 'search-string'},
        'options': []
    },
    'update': {
        'arg': {'type': str, 'required': False, 'store-to': 'update_url', 'help-keyword': 'url'},
        'options': [
            {'keys': ['-c', '--clear'], 'arg': False, 'store-to': 'clear', 'type': None, 'help': 'clear current repository before updating'}
        ]
    }
}
HELP = f'''
Commands. COMMAND [arg] <OPTIONAL> [flags]

install [package] <install package>:
    -v, --version [version] | version of package to install
    -r, --reinstall | reinstall if already installed

remove [package] <uninstall package>:
    -v, --version [version] | version of package to uninstall
    
list <list installed>

run [package] <execute package>:
    -v, --version [version] | version of package to run
    
show [package] <show package details>:
    -v, --version [version] | version of package to show
    
repo <update and export package repository>:
    -u, --update [directory] | directory to update from
    -c, --clear | if updating, clear repository first
    -e, --export [directory] | directory to export to
    
config [package] <configure default version for package>

search [search-string] <search repository for packages>

update [update-url] <update repository from url>
    -c, --clear | clear repository before updating

'''
VERSION = f' - Mod Development Tool -\n   Version: {__VERSION__} Beta'
with open(os.path.join(os.path.abspath(os.path.split(__file__)[0]), 'config.json'), 'r') as f:
    CONFIG = json.load(f)


class InputProcessor:

    def __init__(self, commands, api: mdt.api.Api, root: bool):
        self._commands = commands
        self._api = api
        self._root = root

    def run(self):
        if self._commands.install:
            if os.geteuid() != 0 and self._root is True:
                print('You must be root to run this command')
                sys.exit(0)
            if self._commands.install.version:
                self._api.install(self._commands.install.package, self._commands.install.version)
            else:
                self._api.install(self._commands.install.package)
        elif self._commands.remove:
            if os.geteuid() != 0 and self._root is True:
                print('You must be root to run this command')
                sys.exit(0)
            if self._commands.remove.version:
                self._api.uninstall(self._commands.remove.package, self._commands.remove.version)
            else:
                self._api.uninstall(self._commands.remove.package)
        elif self._commands.list:
            self._api.list_installed()
        elif self._commands.run:
            if self._commands.run.version:
                self._api.run(self._commands.run.package, self._commands.run.version)
            else:
                self._api.run(self._commands.run.package)
        elif self._commands.show:
            if self._commands.show.version:
                self._api.show(self._commands.show.package, self._commands.show.version)
            else:
                self._api.show(self._commands.show.package)
        elif self._commands.repo:
            if type(self._commands.repo) is bool:
                sys.exit(0)
            if self._commands.repo.update_dir:
                if os.geteuid() != 0 and self._root is True:
                    print('You must be root to run this command')
                    sys.exit(0)
                if self._commands.repo.clear:
                    self._api.update(self._commands.repo.update_dir, clear=True)
                else:
                    self._api.update(self._commands.repo.update_dir, clear=False)
            if self._commands.repo.export_dir:
                self._api.export(self._commands.repo.export_dir)
        elif self._commands.config:
            if os.geteuid() != 0 and self._root is True:
                print('You must be root to run this command')
                sys.exit(0)
            self._api.configure(self._commands.config.package)
        elif self._commands.search:
            self._api.search_packages(self._commands.search.search_string)
        elif self._commands.update:
            if os.geteuid() != 0 and self._root is True:
                print('You must be root to run this command')
                sys.exit(0)
            url = CONFIG['url']
            if type(self._commands.update) is mdt.argument_parser.Namespace:
                url = self._commands.update.update_url
                if self._commands.update.clear:
                    self._api.update_from_url(url, clear=True)
                else:
                    self._api.update_from_url(url, clear=False)
            else:
                self._api.update_from_url(url, clear=False)


if __name__ == '__main__':
    package_api = mdt.api.Api(os.path.abspath(os.path.split(__file__)[0]), verbose=True)
    command_list = mdt.argument_parser.Parser(OPTIONS, VERSION, HELP).get_parsed()
    processor = InputProcessor(command_list, package_api, root=CONFIG['root'])
    processor.run()



