import os
from os import sep
import shutil
import pprint
import shelve
from time import time
from time import sleep
from datetime import datetime


class SyncDirs:
    """
    Synchronizes source directory tree and contents to target
    with identical structure and contents. Uses checksum and
    existence of source in target to decide whether to copy
    or not.

    File or folder not in source is removed from target.

    Returns:
        obj: instance of SyncDirs
    """

    def __init__(self, name, src, tgt):
        """
        Initialize an instance of SyncDirs.

        Args:
            name (str): name for SyncDirs instance.
            src (str): Source directory.
            tgt (str): Target directory.
        """
        self.__name = name
        self.srcPath = src
        self.tgtPath = tgt
        self.start = time()
        self.end = None
        while True:
            if os.path.exists(self.srcPath):
                break
            else:
                print('Invalid source directory: ', self.srcPath)
                self.srcPath = input('Re-enter path: ')

    def __str__(self):
        return f"""
<{self.__name}>
Source: {self.srcPath}
Target: {self.tgtPath}
"""

    def sync(self):
        """
        use os.walk() to find differences in source
        and target directory and then synchronize two
        paths.
        """
        if self.checksum(self.srcPath, self.tgtPath, dir=True):
            print('No change detected.')
        else:
            for folder, _, files in os.walk(self.srcPath):
                tail = self.getTail(folder, src=True)
                tgt = f'{self.tgtPath}{tail}'
                self.makeTgtDirs(tgt)
                for file in files:
                    self.copy(folder, tgt, file)
            self.clean()

    def getTail(self, folder, src=False, tgt=False):
        """
        Returns tail path of source path or target path.
        
        example.srcPath = '/home/user/Desktop/buffer'
        example.tgtPath = '/home/user/Desktop/foo/bar'
        folder = '/home/user/Desktop/buffer/another'
        
        example.getTail(folder, src=True) --> '/another'
        
        example.tgtPath + '/another'
        = 'home/user/Desktop/foo/bar/another'

        Args:
            folder (str): current folder in os.walk() recursion.
            src (bool, optional): set to True for source path. Defaults to False.
            tgt (bool, optional): set to True for target path. Defaults to False.

        Returns:
            str: tail path of current folder in os.walk() recursion.
        """
        if src:
            return folder.replace(self.srcPath, '')
        if tgt:
            return folder.replace(self.tgtPath, '')
        else:
            return None

    def clean(self):
        """
        Removes files and/or directories from target directory 
        that no longer exist in source directory.
        """
        try:
            for folder, _, files in os.walk(self.tgtPath):
                tail = self.getTail(folder, tgt=True)
                if not os.path.exists(self.srcPath+tail):
                    print(f'removing "{folder}"')
                    shutil.rmtree(folder)
                else:
                    for file in files:
                        if not os.path.exists(self.srcPath+tail+sep+file):
                            tgtFile = folder+sep+file
                            print(f'removing "{tgtFile}"')
                            os.remove(tgtFile)
                            
        except FileNotFoundError as err:
            print(err)
        except KeyError:
            pass

    def copy(self, folder, tgt, file):
        """uses self.checksum() and os.path.exists()
        to decide whether to copy source file/directory
        to target.

        Args:
            folder (str): current folder in os.walk() recursion.
            tgt (str): path to copy to.
            file (str): current file in os.walk() recursion.
        """
        src = f'{folder}{sep}{file}'
        tgt = f'{tgt}{sep}{file}'
        if os.path.exists(tgt):
            if not self.checksum(src, tgt):
                print(f'copying "{file}"')
                shutil.copy(src, tgt)
            elif self.checksum(src, tgt) is None:
                pass
        else:
            print(f'copying "{file}"')
            shutil.copy(src, tgt)

    def backUp(self):
        """
        Makes clones of target directory at set interval
        """
        basename = os.path.basename(self.tgtPath)
        backup = self.tgtPath+sep+'..'+sep+f'{basename}_backup'
        self.makeTgtDirs(backup)
        while len(os.listdir(backup)) > 5:
            a = sorted(os.listdir(backup)).pop(0)
            print('deleting oldest backup')
            shutil.rmtree(backup+sep+a)
        self.end = time()
        if int(self.end - self.start) > 600:
            print(f'creating backup for <{self.__name}>')
            shutil.copytree(self.tgtPath, backup + sep +
                            basename + ' ' + str(datetime.now()))
            self.start = time()

    def checksum(self, src, tgt, dir=False):
        """
        Compares parallel files or source and target directories
        of their size. 

        Args:
            src (str): absolute path of file or directory in source directory.
            tgt (str): absolute path of file or directory in target directory.
            dir (bool, optional): set to True if comparing folder sizes. Defaults to False.

        Returns:
            bool: size comparison of src and tgt.
        """
        if dir:
            srcSize = 0
            tgtSize = 0
            for folder, _, files in os.walk(src):
                for file in files:
                    file = f'{folder}{sep}{file}'
                    srcSize += os.path.getsize(file)
            for folder, _, files in os.walk(tgt):
                for file in files:
                    file = f'{folder}{sep}{file}'
                    tgtSize += os.path.getsize(file)
            if srcSize == tgtSize:
                return True
            else:
                return False
        else:
            if os.path.getsize(src) == os.path.getsize(tgt):
                return True
            else:
                return False

    @classmethod
    def run(cls):
        """
        Execute synchronizing process for each SyncDir instance
        in SyncDir.jobs.
        """
        global jobs
        while True:
            for job in jobs:
                print(job)
                job.sync()
                job.backUp()
                print(datetime.now())
                sleep(1)

    @staticmethod
    def makeTgtDirs(tgt):
        """
        Creates target directory (and intermediary directories).

        Args:
            tgt (str): absolute path of target directory.
        """
        try:
            os.makedirs(tgt)
            print(f'creating "{tgt}" because it does not exist.')

        except FileExistsError as e:
            pass
            

jobs = set()
jobs.add(SyncDirs('example', '/SOURCE/DIRECTORY', '/TARGET/DIRECTORY'))

while True:
    SyncDirs.run()
