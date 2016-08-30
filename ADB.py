#!/usr/bin/env python3

import os
import sys
import io
import re
import collections
from os import path
from subprocess import *


File = collections.namedtuple('File', 'name size modtime acl owner group')


class ADBException(Exception):

    def __init__(self, msg):
        self.msg = msg


class ADB:
    START = '===START==='
    END = '===END==='
    SEP = '===SEP==='
    DEV_NULL = '2>/dev/null'

    def __init__(self):
        pass
        
    @staticmethod
    def __getCmd(cmd):
        return cmd + ' 2>/dev/null'

    def ll(self, directory):
        """获取手机中指定目录的文件列表"""
        p = Popen(['adb', 'shell'], stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        sio = io.StringIO()
        sio.write('cd "%s" %s && ' % (directory, ADB.DEV_NULL))
        sio.write('echo %s && ' % (ADB.START, ))
        sio.write('ls -al %s && ' % (ADB.DEV_NULL, ))
        # sio.write('echo %s && ' % (ADB.SEP, ))
        # sio.write('ls -al %s && ' % (ADB.DEV_NULL, ))
        sio.write('echo %s &&' % (ADB.END, ))
        sio.write('exit || exit\n')
        
        cmd = sio.getvalue()
        # print(cmd)
        # return cmd, None
        output, err = p.communicate(cmd)
        p.terminate()
        # get values from output
        result = re.search(r'(?sm)^%s$(.*)^%s$' % (ADB.START, ADB.END), output)
        if not result:
            return None, None
        lines = list(filter(None, result.group(1).splitlines()))
        files = []
        directories = []
        for f in lines:
            'drwxrwx--- root     sdcard_r          2016-07-28 23:34 xunlei'
            '-rw-rw---- root     sdcard_r   584787 2016-08-26 19:47 wifi_config.log'
            fAcl, fOwn, fGroup, fElse = f.split(None, maxsplit=3)
            if fAcl[0] == 'd':
                fDate, fTime, fName = fElse.split(None, 2)
                fSize = None
                lst = directories
            else:
                fSize, fDate, fTime, fName = fElse.split(None, 3)
                lst = files
            fModtime = fDate + ' ' + fTime
            lst.append(File(name=fName, size=fSize, modtime=fModtime, 
                acl=fAcl, group=fGroup, owner=fOwn))

        return directories, files

    def ls(self, directory):
        """获取手机中指定目录的文件列表"""
        p = Popen(['adb', 'shell'], stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        sio = io.StringIO()
        sio.write('cd "%s" %s && ' % (directory, ADB.DEV_NULL))
        sio.write('echo %s && ' % (ADB.START,))
        sio.write('ls -aF %s && ' % (ADB.DEV_NULL,))
        sio.write('echo %s && ' % (ADB.SEP, ))
        sio.write('ls -al %s && ' % (ADB.DEV_NULL, ))
        sio.write('echo %s &&' % (ADB.END,))
        sio.write('exit || exit\n')

        cmd = sio.getvalue()
        # print(cmd)
        # return cmd, None
        try:
            output, err = p.communicate(cmd, timeout=3)
        except TimeoutExpired:
            raise ADBException("超时")
        finally:
            p.terminate()
        if not output and err:
            raise ADBException(err)

        # get values from output
        result = re.search(r'(?sm)^%s$(.*)^%s$(.*)^%s$' % (ADB.START, ADB.SEP, ADB.END), output)
        if not result:
            return None, None
        lines = list(filter(None, result.group(1).splitlines()))
        files = []
        directories = []
        for f in lines:
            '- unlock_key'
            'd var'
            'ld vendor'
            fType, fName = f.split(None, maxsplit=1)
            fName = fName.strip()
            if 'd' in fType:
                lst = directories
            else:
                lst = files
            lst.append(File(name=fName, size=None, modtime=None,
                            acl=None, group=None, owner=None))

        return directories, files

    def push(self, localFiles, remoteDir):
        args = ["adb", "push"] + localFiles + [remoteDir]
        print(args)
        return call(args)

    def pull(self, remoteFiles, localDir):
        args = ["adb", "pull"] + remoteFiles + [localDir]
        print(args)
        return call(args)


if __name__ == '__main__':
    from pprint import pprint as pp
    adb = ADB()
    l1, l2 = adb.ls('/sdcard')
    pp(l1)
    pp(l2)
