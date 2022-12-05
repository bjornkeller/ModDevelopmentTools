#!/usr/bin/env python3

import json
import os
import shutil


class InvalidManifestError(Exception):
    pass


class MissingFileError(Exception):
    pass


class Repository:

    def __init__(self, path: str = None):
        self._path = path or os.path.join('/opt', 'mdt', 'repository')
        self._repo = self._load_repo()

    def get(self, package_name: str = None, version: str = None):
        if not package_name and not version:
            return self._repo.copy()
        elif not package_name and version is not None:
            ret = []
            for r in self._repo:
                if version in r['versions']:
                    ret.append(r)
            return ret
        elif package_name is not None and not version:
            for r in self._repo:
                if r['name'] == package_name:
                    return r.copy()
        elif package_name is not None and version is not None:
            for r in self._repo:
                if r['name'] == package_name and version in r['versions']:
                    return r.copy()

    def add(self, package: str, pack_name: str):
        self.verify_pack(package)
        shutil.copytree(package, os.path.join(self._path, pack_name))

    def update(self, path: str, clear: bool = False):
        path = os.path.abspath(path)
        dirs = []
        for d in os.listdir(path):
            dirs.append(os.path.join(path, d))
        for d in dirs:
            self.verify_pack(d)
        if clear:
            for di in os.listdir(self._path):
                shutil.rmtree(os.path.join(self._path, di))
        for d in os.listdir(self._path):
            with open(os.path.join(self._path, d, 'manifest.json'), 'r') as f:
                s_name = json.load(f)['name']
            for nd in dirs:
                with open(os.path.join(nd, 'manifest.json'), 'r') as f:
                    if json.load(f)['name'] == s_name:
                        shutil.rmtree(os.path.join(self._path, d))
                        break
        for pack in os.listdir(path):
            shutil.copytree(os.path.join(path, pack), os.path.join(self._path, pack))

    def export(self, path: str):
        shutil.copytree(self._path, os.path.join(os.path.abspath(path), 'repository'))

    def _load_repo(self):
        dirs = []
        repo = []
        for d in os.listdir(self._path):
            if os.path.isdir(os.path.join(self._path, d)):
                dirs.append(os.path.join(self._path, d))
        for di in dirs:
            with open(os.path.join(di, 'manifest.json'), 'r') as f:
                j = json.load(f)
            j['install-script'] = os.path.join(di, j['install-script'])
            j['remove-script'] = os.path.join(di, j['remove-script'])
            j['start-script'] = os.path.join(di, j['start-script'])
            repo.append(j)
        return repo

    @staticmethod
    def verify_pack(d: str):
        try:
            with open(os.path.join(d, 'manifest.json'), 'r') as f:
                p = json.load(f)
        except Exception:
            raise InvalidManifestError
        try:
            if not type(p['name']) is str:
                raise InvalidManifestError
            if not type(p['default-version']) is str:
                raise InvalidManifestError
            if type(p['icon']) is not str and p['icon'] is not None:
                raise InvalidManifestError
            if not type(p['install-script']) is str:
                raise InvalidManifestError
            if not type(p['remove-script']) is str:
                raise InvalidManifestError
            if not type(p['start-script']) is str:
                raise InvalidManifestError
            if not type(p['add-launcher']) is bool:
                raise InvalidManifestError
            if not type(p['versions']) is list:
                raise InvalidManifestError
            for entry in p['versions']:
                if not type(entry) is str:
                    raise InvalidManifestError
        except Exception:
            raise InvalidManifestError
        if not os.path.isfile(os.path.join(d, p['install-script'])):
            raise MissingFileError('no install script found')
        if not os.path.isfile(os.path.join(d, p['remove-script'])):
            raise MissingFileError('no remove script found')
        if not os.path.isfile(os.path.join(d, p['start-script'])):
            raise MissingFileError('no start script found')
        if type(p['icon']) is str and not os.path.isfile(os.path.join(d, p['icon'])):
            raise MissingFileError('icon file is missing')

