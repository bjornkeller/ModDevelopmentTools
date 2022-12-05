#!/usr/bin/env python3

import json
import os
import shutil
import subprocess
import sys
import requests
from zipfile import ZipFile

from . import repository
from . import packages


class Api:

    def __init__(self, path: str, verbose: bool = False):
        self._path = path
        self._verbose = verbose

    def install(self, name: str, version: str = None):
        packages.install(package_name=name, version=version, path=self._path, verbose=self._verbose)

    def uninstall(self, name: str, version: str = None):
        packages.uninstall(package_name=name, version=version, path=self._path, verbose=self._verbose)

    def show(self, package: str, version: str = None):
        packs = packages.Packages(os.path.join(self._path, 'installed-programs'))
        installed = packs.get_installations_of(package)
        for i in installed:
            if version:
                if i['version'] == version:
                    print(f'Name: {i["name"]}\nVersion: {i["version"]}\n')
            else:
                print(f'Name: {i["name"]}\nVersion: {i["version"]}\n')

    def list_installed(self):
        packs = packages.Packages(os.path.join(self._path, 'installed-programs'))
        installed = packs.get_all_installed()
        for i in installed:
            print(f'Name: {i["name"]}\nVersion: {i["version"]}\n')

    def search_packages(self, search_string: str):
        packs = packages.search(search_string, path=self._path)
        for p in packs:
            print(f'Name: {p["name"]}\nDefault Version: {p["default-version"]}\nOther Versions: {p["versions"]}')

    def configure(self, name: str):
        packs = packages.Packages(os.path.join(self._path, 'installed-programs'))
        installed = packs.get_installations_of(name)
        current_config = packs.get_config_of(name)
        versions = []
        index = 0
        print(f'Version config for {name}:')
        for i in installed:
            versions.append(i['version'])
            if current_config['version'] == i['version']:
                print(f'    {index},  {i["name"]}: {i["version"]} *')
            else:
                print(f'    {index},  {i["name"]}: {i["version"]}')
            index += 1
        print('')
        try:
            new_version = input('Enter the number for new default version: ')
        except KeyboardInterrupt:
            sys.exit(0)
        try:
            new_config_version = versions[int(new_version)]
        except Exception:
            print('Invalid entry.')
            sys.exit(0)
        packs.configure(name, new_config_version)

    def run(self, name: str, version: str = None):
        packs = packages.Packages(os.path.join(self._path, 'installed-programs'))
        if len(packs.get_installations_of(name)) == 0:
            print(f'Program \'{name}\' could not be found.')
            sys.exit(0)
        try:
            version = version or packs.get_config_of(name)['version']
        except TypeError or KeyError:
            print('No default version. please specify.')
            sys.exit(0)
        path_to_manifest = packs.is_installed(name, version)
        if path_to_manifest is None:
            print(f'{name} has no version {version}.')
            sys.exit(0)
        with open(os.path.join(path_to_manifest)) as f:
            manifest = json.load(f)
        subprocess.call(['python3', os.path.join(os.path.split(path_to_manifest)[0], manifest['start-script']), manifest['program-dir'], manifest['version']])

    def update_from_url(self, url: str, clear: bool):
        print(f'Downloading repository from {url}...')
        try:
            update_file = requests.get(url, allow_redirects=True)
            with open(os.path.join(self._path, '.tmp', 'repository-update.zip'), 'wb') as f:
                f.write(update_file.content)
        except Exception as e:
            if self._verbose:
                print(f'ERR error downloading {url}')
                sys.exit(0)
            else:
                raise e
        print(f'Extracting repository-update.zip...')
        with ZipFile(os.path.join(self._path, '.tmp', 'repository-update.zip'), 'r') as zipf:
            zipf.extractall(path=os.path.join(self._path, '.tmp'))
        print('Installing update...')
        self.update(os.path.join(self._path, '.tmp', 'repository'), clear=clear)
        print('Cleaning up...')
        os.remove(os.path.join(self._path, '.tmp', 'repository-update.zip'))
        shutil.rmtree(os.path.join(self._path, '.tmp', 'repository'))
        print('Done!')

    def update(self, file: str, clear: bool):
        r = repository.Repository(os.path.join(self._path, 'repository'))
        r.update(file, clear=clear)

    def export(self, path: str):
        r = repository.Repository(os.path.join(self._path, 'repository'))
        r.export(path)

