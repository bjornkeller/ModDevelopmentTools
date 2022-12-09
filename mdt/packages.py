#!/usr/bin/env python3

import os
import json
import shutil
import sys
import uuid
import subprocess

from .repository import Repository, MissingFileError, InvalidManifestError


class NoInstallCandidate(Exception):
    pass


class ErrorInInstallScript(Exception):
    pass


class AlreadyInstalledError(Exception):
    pass


class FailedToInstallError(Exception):
    pass


class FailedToUninstallError(Exception):
    pass


class PackageNotInstalled(Exception):
    pass


class VersionConfig:

    @staticmethod
    def get_config(path: str):
        try:
            with open(os.path.join(path, 'package-data', 'version-config.json'), 'r') as f:
                config = json.load(f)
            return config
        except Exception:
            return None

    @staticmethod
    def edit(path: str, d: dict):
        try:
            added = False
            new_config = []
            with open(os.path.join(path, 'package-data', 'version-config.json'), 'r') as f:
                config = json.load(f)
            for c in config:
                if c['name'] == d['name']:
                    new_config.append(d)
                    added = True
                else:
                    new_config.append(c)
            if added is False:
                new_config.append(d)
            with open(os.path.join(path, 'package-data', 'version-config.json'), 'w') as f:
                json.dump(new_config, f, indent=2)
        except Exception as e:
            raise e

    @staticmethod
    def remove(path: str, package_name: str):
        try:
            new_config = []
            with open(os.path.join(path, 'package-data', 'version-config.json'), 'r') as f:
                config = json.load(f)
            for c in config:
                if c['name'] != package_name:
                    new_config.append(c)
            with open(os.path.join(path, 'package-data', 'version-config.json'), 'w') as f:
                json.dump(new_config, f, indent=2)
        except Exception as e:
            raise e


class Packages:

    def __init__(self, package_path: str = None):
        self._package_path = package_path or os.path.join('/opt', 'mdt', 'installed-programs')
        self._pack_list = self._load_repo()

    def is_installed(self, package_name: str, package_version: str):
        for pack in os.listdir(os.path.join(self._package_path, 'package-data')):
            p = os.path.join(self._package_path, 'package-data', pack, 'manifest.json')
            if os.path.isfile(p):
                try:
                    with open(p, 'r') as f:
                        pm = json.load(f)
                    if pm['name'] == package_name and pm['version'] == package_version:
                        return p
                except Exception:
                    continue

    def get_installations_of(self, package_name: str):
        ret_li = []
        for pack in os.listdir(os.path.join(self._package_path, 'package-data')):
            p = os.path.join(self._package_path, 'package-data', pack, 'manifest.json')
            if os.path.isfile(p):
                try:
                    with open(p, 'r') as f:
                        pm = json.load(f)
                    if pm['name'] == package_name:
                        ret_li.append({'name': pm['name'], 'version': pm['version'], 'path': p})
                except Exception:
                    continue
        return ret_li

    def get_config_of(self, package_name: str):
        full_config = VersionConfig.get_config(self._package_path)
        for c in full_config:
            if c['name'] == package_name:
                return c

    def configure(self, package_name: str, version: str):
        for pack in self.get_all_installed():
            if pack['name'] == package_name and pack['version'] == version:
                VersionConfig.edit(self._package_path, {'name': package_name, 'version': version})
                return

    def get_all_installed(self):
        ret_li = []
        for pack in os.listdir(os.path.join(self._package_path, 'package-data')):
            p = os.path.join(self._package_path, 'package-data', pack, 'manifest.json')
            if os.path.isfile(p):
                try:
                    with open(p, 'r') as f:
                        pm = json.load(f)
                        ret_li.append({'name': pm['name'], 'version': pm['version'], 'path': p})
                except Exception:
                    continue
        return ret_li

    def _load_repo(self):
        dirs = []
        repo = []
        for d in os.listdir(os.path.join(self._package_path, 'package-data')):
            if os.path.isdir(os.path.join(self._package_path, 'package-data', d)):
                dirs.append(os.path.join(self._package_path, 'package-data', d))
        for di in dirs:
            with open(os.path.join(di, 'manifest.json'), 'r') as f:
                j = json.load(f)
            j['install-script'] = os.path.join(di, j['install-script'])
            j['remove-script'] = os.path.join(di, j['remove-script'])
            j['start-script'] = os.path.join(di, j['start-script'])
            repo.append(j)
        return repo

    @staticmethod
    def verify_installed_entry(d: str):
        try:
            with open(os.path.join(d, 'manifest.json'), 'r') as f:
                p = json.load(f)
        except Exception:
            raise InvalidManifestError
        try:
            if not type(p['name']) is str:
                raise InvalidManifestError
            if not type(p['version']) is str:
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
            if not type(p['program-dir']) is str:
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


def install(package_name: str, version: str = None, path: str = None, verbose: bool = False):

    # Install globals
    r = Repository(os.path.join(path, 'repository'))
    p = Packages(os.path.join(path, 'installed-programs'))
    package_path = os.path.join(path, 'installed-programs', 'package-data', str(uuid.uuid4()))
    dst_path = os.path.join(path, 'installed-programs', 'program-data', str(uuid.uuid4()))
    repo_package = r.get(package_name, version)

    def verify():
        if repo_package is None:
            raise NoInstallCandidate(f'{package_name} has no installation candidate')
        install_v = version or repo_package['default-version']
        if p.is_installed(package_name, install_v):
            raise AlreadyInstalledError
        return install_v

    def setup():
        os.mkdir(dst_path)
        shutil.copytree(scr_path, package_path)
        with open(os.path.join(package_path, 'manifest.json'), 'r') as f:
            package_manifest = json.load(f)
        package_manifest['program-dir'] = dst_path
        package_manifest['version'] = install_version
        del package_manifest['versions']
        del package_manifest['default-version']
        with open(os.path.join(package_path, 'manifest.json'), 'w') as f:
            json.dump(package_manifest, f, indent=2)
        return package_manifest, os.path.join(package_path, package_manifest['install-script'])

    def cleanup_broken():
        try:
            shutil.rmtree(dst_path)
        except Exception:
            pass
        try:
            shutil.rmtree(package_path)
        except Exception:
            pass

    def edit_version_config():
        config = VersionConfig.get_config(os.path.join(path, 'installed-programs'))
        for c in config:
            if c['name'] == repo_package['name']:
                return
        VersionConfig.edit(os.path.join(path, 'installed-programs'), {'name': repo_package['name'], 'version': install_version})

    try:
        # verify & get version
        install_version = verify()
        scr_path = os.path.split(repo_package['install-script'])[0]
        # setup & get manifest/install script
        manifest, install_script = setup()

        # run install script
        try:
            subprocess.call(['python3', install_script, manifest['program-dir'], manifest['version']], stderr=subprocess.PIPE)
        except Exception:
            raise ErrorInInstallScript
        # configure version
        edit_version_config()
    except AlreadyInstalledError as e:
        if verbose:
            print('ERR: package already installed')
            return
        else:
            raise e
    except NoInstallCandidate as e:
        if verbose:
            print('ERR: package has on installation candidate')
            return
        else:
            raise e
    except ErrorInInstallScript as e:
        cleanup_broken()
        if verbose:
            print('ERR: error in install script\nInstall failed!')
            return
        else:
            raise e
    except KeyboardInterrupt:
        cleanup_broken()
        sys.exit(0)
    except Exception as e:
        cleanup_broken()
        if verbose:
            print('ERR: unknown error occurred during install\nInstall failed!')
            return
        else:
            raise e


def uninstall(package_name: str, version: str = None, path: str = None, verbose: bool = False):

    # Install globals
    p = Packages(os.path.join(path, 'installed-programs'))

    def verify(pack_version):
        packages = p.get_installations_of(package_name)
        package = None
        if not len(packages) > 0:
            raise PackageNotInstalled
        if not pack_version:
            con = p.get_config_of(package_name)
            pack_version = con['version']
        for pack in packages:
            if pack['name'] == package_name and pack['version'] == pack_version:
                package = pack
        if package is None:
            raise PackageNotInstalled
        else:
            return package, pack_version

    def cleanup():
        exep_list = []
        try:
            shutil.rmtree(package_path)
        except Exception as e:
            exep_list.append(e)
        try:
            shutil.rmtree(program_date_path)
        except Exception as e:
            exep_list.append(e)
        if len(exep_list) > 0:
            if verbose:
                print('ERR: error in cleanup')
                return
            else:
                for ex in exep_list:
                    print(ex)
                raise FailedToUninstallError

    def configure_version():
        new_version = None
        con = p.get_config_of(package_name)
        if con['version'] != version:
            return
        versions = p.get_installations_of(package_name)
        for v in versions:
            if v['version'] != version:
                new_version = v
                break
        if new_version is None:
            VersionConfig.remove(os.path.join(path, 'installed-programs'), package_name)
        else:
            p.configure(package_name, new_version['version'])

    try:
        # verify package
        try:
            uninstall_pack, version = verify(version)
        except PackageNotInstalled as e:
            if verbose:
                print('ERR: package could not be found\nUninstall failed!')
                return
            else:
                raise e

        with open(uninstall_pack['path'], 'r') as f:
            manifest = json.load(f)
        package_path = os.path.split(uninstall_pack['path'])[0]
        program_date_path = manifest['program-dir']
        uninstall_script = os.path.join(package_path, manifest['remove-script'])
        try:
            subprocess.call(['python3', uninstall_script, program_date_path, version], stderr=subprocess.PIPE)
        except Exception as e:
            if verbose:
                print('ERR: error running uninstall script')
            else:
                raise e
        cleanup()
        configure_version()
        print('Uninstalled successfully!')
    except KeyboardInterrupt:
        cleanup()
        sys.exit(0)
    except Exception as e:
        if verbose:
            print('ERR: error in uninstall\nUninstall failed!')
            return
        else:
            raise e


def search(search_string: str, path: str = None):
    p = Repository(os.path.join(path, 'repository'))
    packs = p.get()
    ret = []
    for pack in packs:
        if search_string in pack['name']:
            ret.append(pack)
    return ret
