import os
from os import sep
import shutil
from time import time, sleep
from datetime import datetime
from sys import exit


class SyncDirs:
    """
    Synchronizes source directory tree and contents to target
    with identical structure and contents. Uses size comparison
    and existence of source in target to decide whether to copy
    or not.

    File or folder not in source is removed from target.

    Returns:
        obj: instance of SyncDirs
    """
    jobs = set()
    def __init__(self, name, paths):
        """
        Initialize an instance of SyncDirs.

        Args:
            name (str): name for SyncDirs instance.
            src (str): Source directory.
            tgt (str): Target directory.
        """
        self.__name = name
        self.srcPath, self.tgtPath = paths
        self.start = time() 
        self.end = None
        while True:
            if os.path.exists(self.srcPath):
                break
            else:
                print('Invalid source directory: ', self.srcPath)
                self.srcPath = input('Re-enter path: ')
                if self.srcPath =='cancel':
                    exit()
        self.addJob(self)

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
        elif tgt:
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
                    print(f'\nremoving "{folder}"')
                    shutil.rmtree(folder)
                else:
                    for file in files:
                        if not os.path.exists(self.srcPath+tail+sep+file):
                            tgtFile = folder+sep+file
                            print(f'\nremoving "{tgtFile}"')
                            os.remove(tgtFile) 
                                 
        except FileNotFoundError:
            pass
            
        except KeyError:
            pass

    def copy(self, folder, tgt, file):
        """uses self.compareSize() and os.path.exists()
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
            if self.compareSize(src, tgt):
                pass
            elif not self.compareSize(src, tgt):
                print(f'\ncopying "{file}"')
                shutil.copy(src, tgt)
            else:
                pass
        else:
            print(f'\ncopying "{file}"')
            shutil.copy(src, tgt)

    def backUp(self):
        """
        Makes clones of target directory at set interval in
        its parent directory.
        
        example.tgtPath = 'home/user/Desktop/buffer/another'
        backup = 'home/user/Desktop/buffer/another_backup'
        
        in os.listdir(backup) = [
                                'another backup 2020-08-09 17:01:13.731190',
                                'another backup 2020-08-09 17:11:13.731190'
                                ]
        """
        basename = os.path.basename(self.tgtPath)
        backup = self.tgtPath+sep+'..'+sep+f'{basename}_backup'
        self.makeTgtDirs(backup)
        while len(os.listdir(backup)) > 12:
            a = sorted(os.listdir(backup)).pop(0)
            print('\ndeleting oldest backup')
            shutil.rmtree(backup+sep+a)
        self.end = time()
        if int(self.end - self.start) > 120:
            print(f'\ncreating backup for <{self.__name}>')
            shutil.copytree(self.tgtPath, backup + sep +
                            basename + ' ' + str(datetime.now()))
            self.start = time()

    def compareSize(self, src, tgt):
        """
        Compares parallel files or source and target directories
        of their size. 

        Args:
            src (str): absolute path of file or directory in source directory.
            tgt (str): absolute path of file or directory in target directory.

        Returns:
            bool: size comparison of src and tgt.
        """
        if os.path.getsize(src) == os.path.getsize(tgt):
            return True
        else:
            return False

    @classmethod
    def run(cls):
        """
        Execute synchronizing process for each SyncDirs instance
        in jobs set.
        """
        count = 0
        while True:
            for job in cls.jobs:
                print(job)
                job.sync()
                job.backUp()
                if count < 10:
                    print(f'{count}', end='', flush=True)
                    count += 1
                else:
                    count = 0
                sleep(1)
                
    @classmethod
    def addJob(cls, instance):
        cls.jobs.add(instance)
    @staticmethod
    def makeTgtDirs(tgt):
        """
        Creates target directory (and intermediary directories).

        Args:
            tgt (str): absolute path of target directory.
        """
        try:
            os.makedirs(tgt)
            print(f'\ncreating "{tgt}" because it does not exist.')

        except FileExistsError:
            pass
            

SyncDirs('example', ('/SOURCE/DIRECTORY', '/TARGET/DIRECTORY'))

while True:
    SyncDirs.run()
