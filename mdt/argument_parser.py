#!/usr/bin/env python3

import sys


class InvalidUsage(Exception):
    pass


class Namespace:

    def __init__(self, **kwargs):
        self.__dict__ = kwargs

    def __getitem__(self, item):
        return self.__dict__[item]

    def __setitem__(self, key, value):
        self.__dict__[key] = value


class Parser:

    def __init__(self, option_dict: dict, version: str, help_message: str, set_version_option: bool = True):
        self._options = option_dict
        self._command = sys.argv
        self._version = version
        self._set_version = set_version_option
        self._help = help_message
        del self._command[0]
        try:
            self._parsed = self._parse()
        except InvalidUsage:
            print('Invalid usage')
            print(self._help)
            sys.exit(0)

    def get_parsed(self):
        return self._parsed

    def _parse(self):
        if len(self._command) == 0:
            print(self._version)
            sys.exit(0)
        elif self._command[0] == '-v' or self._command[0] == '--version':
            print(self._version)
            sys.exit(0)
        elif self._command[0] == '-h' or self._command[0] == '--help':
            print(self._help)
            sys.exit(0)
        root_namespace = Namespace()
        found = False
        for opt, value in self._options.items():
            if self._command[0] == opt:
                found = True
                if len(self._command) == 1:
                    if self._options[opt]['arg'] is not None and self._options[opt]['arg']['required'] is True:
                        raise InvalidUsage
                    else:
                        root_namespace[opt] = True
                else:
                    root_namespace[opt] = self._make_nested_namespace(opt)
            else:
                root_namespace[opt] = None
        if found is False:
            raise InvalidUsage
        return root_namespace

    def _make_nested_namespace(self, opt: str):
        ret_namespace = Namespace()
        di = self._options[opt]

        def set_arg():
            ret = False
            if di['arg'] is None:
                pass
            elif di['arg']['required'] is True:
                ret_namespace[di['arg']['store-to']] = self._command[1]
                ret = True
            else:
                matches_flag = False
                for o in di['options']:
                    for k in o['keys']:
                        if k == self._command[1]:
                            matches_flag = True
                            break
                    if matches_flag is True:
                        break
                if matches_flag is False:
                    ret_namespace[di['arg']['store-to']] = self._command[1]
                    ret = True
                else:
                    ret_namespace[di['arg']['store-to']] = None
            return ret

        def set_flags(start_index: int):
            skip_next = False
            if start_index == len(self._command):
                for k in di['options']:
                    ret_namespace[k['store-to']] = False
            else:
                for num in range(start_index, len(self._command)):
                    if skip_next is True:
                        skip_next = False
                        continue
                    for k in di['options']:
                        found = False
                        for o in k['keys']:
                            if o == self._command[num]:
                                if k['arg'] is True:
                                    if not len(self._command) > num + 1:
                                        raise InvalidUsage
                                    ret_namespace[k['store-to']] = self._command[num + 1]
                                    skip_next = True
                                    found = True
                                else:
                                    ret_namespace[k['store-to']] = True
                                    found = True
                        if found is False:
                            try:
                                _ = ret_namespace[k['store-to']]
                            except KeyError:
                                ret_namespace[k['store-to']] = False

        is_arg = set_arg()
        if is_arg is True:
            set_flags(2)
        else:
            set_flags(1)
        return ret_namespace
