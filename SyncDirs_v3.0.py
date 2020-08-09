import os
import shutil
import pprint
import shelve
from time import time, sleep
from datetime import datetime


class SyncDirs:
    """
    Synchronizes source directory tree and contents to target
    with identical structure and contents. Uses checksum and
    existence of source in target to decide whether to copy
    or not.

    File or folder not in source is removed from target.
    """
    jobs = list()
    count = 0
    def __init__(self, name, src, tgt):
        self.name = name
        self.srcPath = src
        self.tgtPath = tgt
        self.srcFiles = dict()
        self.start = time()
        self.end = None
        self.jobs.append(self)
        self.size = None

    def __str__(self):
        return f"""
<{self.name}>
Source: {self.srcPath}
Target: {self.tgtPath}

Tasks:
{pprint.pformat(self.srcFiles)}
"""

    def sync(self):
        if self.checksum(self.srcPath, self.tgtPath, dir=True):
            print('No change detected.')
        else:
            tailList = list()
            for folder, subfolders, files in os.walk(self.srcPath):
                tail = self.getTail(folder, src=True)
                tailList.append(tail)
                self.updateSrc(tail, files)
                tgt = f'{self.tgtPath}{tail}'
                self.makeTgtDirs(tgt)
                for file in files:
                    self.copy(folder, tgt, file)
            self.clean(tailList)

    def getTail(self, folder, src=False, tgt=False):
        if src:
            return folder.replace(self.srcPath, '')
        if tgt:
            return folder.replace(self.tgtPath, '')

    def updateSrc(self, tail, files):
        self.srcFiles.update({tail: files})

    def clean(self, tailList):
        try:
            for folder, subfolders, files in os.walk(self.tgtPath):
                tail = self.getTail(folder, tgt=True)
                for file in files:
                    if file not in self.srcFiles[tail]:
                        tgtFile = f'{self.tgtPath}{tail}{os.path.sep}{file}'
                        print(self.tgtPath)
                        print(tgtFile)
                        print(f'removing "{file}" from "{os.path.dirname(tgtFile)}"')
                        os.remove(tgtFile)
            deList = list()
            for tail in self.srcFiles.keys():
                if tail not in tailList:
                    deList.append(tail)
            for tail in deList:
                del self.srcFiles[tail]
                tgtFolder = f'{self.tgtPath}{tail}'
                print(f'removing directory "{tgtFolder}"')
                shutil.rmtree(tgtFolder)
        except FileNotFoundError as err:
            print(err)

    def copy(self, folder, tgt, file):
        src = f'{folder}{os.path.sep}{file}'
        tgt = f'{tgt}{os.path.sep}{file}'
        if os.path.exists(tgt):
            if not self.checksum(src, tgt):
                print(f'copying "{file}"')
                shutil.copy(src, tgt)
        else:
            print(f'copying "{file}"')
            shutil.copy(src, tgt)

    def backUp(self):
        sep = os.path.sep
        basename = os.path.basename(self.tgtPath)
        backup = self.tgtPath+sep+'..'+sep+f'{basename}_backup'
        self.makeTgtDirs(backup)
        while len(os.listdir(backup)) > 5:
            a = sorted(os.listdir(backup)).pop(0)
            print('deleting oldest backup')
            shutil.rmtree(backup+sep+a)
        self.end = time()
        if int(self.end - self.start) > 600:
            print(f'creating backup for <{self.name}>')
            shutil.copytree(self.tgtPath, backup+sep+basename+' '+str(datetime.now()))
            self.start = time()

    @classmethod
    def saveJobs(cls):
        with shelve.open('SyncDirsData') as f:
            f['jobs'] = cls.jobs
    
    @classmethod
    def loadJobs(cls):
        with shelve.open('SyncDirsData') as f:
            cls.jobs = f['jobs']

    @classmethod
    def run(cls):
        while True:
            jobs = cls.jobs
            for job in jobs:
                print(job)
                job.sync()
                job.backUp()
                cls.saveJobs()
import os
import shutil
import pprint
import shelve
from time import time, sleep
from datetime import datetime


class SyncDirs:
    """
    Synchronizes source directory tree and contents to target
    with identical structure and contents. Uses checksum and
    existence of source in target to decide whether to copy
    or not.

    File or folder not in source is removed from target.
    """
    jobs = list()

    def __init__(self, name, src, tgt):
        """
        Initialize an instance of SyncDirs.

        Args:
            name (str): name attribute of a SyncDirs instance.
            src (str): Source directory.
            tgt (str): Target directory.
        """
        self.name = name
        self.srcPath = src
        self.tgtPath = tgt
        self.srcFiles = dict()
        self.start = time()
        self.end = None
        self.jobs.append(self)
        self.size = None

    def __str__(self):
        return f"""
<{self.name}>
Source: {self.srcPath}
Target: {self.tgtPath}

Tasks:
{pprint.pformat(self.srcFiles)}
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
            tailList = list()
            for folder, subfolders, files in os.walk(self.srcPath):
                tail = self.getTail(folder, src=True)
                tailList.append(tail)
                self.updateSrc(tail, files)
                tgt = f'{self.tgtPath}{tail}'
                self.makeTgtDirs(tgt)
                for file in files:
                    self.copy(folder, tgt, file)
            self.clean(tailList)

    def getTail(self, folder, src=False, tgt=False):
        """
        Returns tail path of source path or target path.
        
        example.srcPath = '/home/user/Desktop/buffer'
        example.tgtPath = '/home/user/Desktop/foo/bar'
        folder = '/home/user/Desktop/buffer/another'
        
        example.getTail(folder, src=True) --> '/buffer'
        
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

    def updateSrc(self, tail, files):
        """
        Updates dictionary of existing files in source directory.

        Args:
            tail (str): tail path returned from self.getTail()
            files (list): list of files in a folder.
        """
        self.srcFiles.update({tail: files})

    def clean(self, tailList):
        """
        Removes files and/or directories from target directory 
        that no longer exist in source directory.

        Args:
            tailList (list): list of tail paths existing in source directory.
        """
        try:
            for folder, subfolders, files in os.walk(self.tgtPath):
                tail = self.getTail(folder, tgt=True)
                for file in files:
                    if file not in self.srcFiles[tail]:
                        tgtFile = f'{self.tgtPath}{tail}{os.path.sep}{file}'
                        print(self.tgtPath)
                        print(tgtFile)
                        print(
                            f'removing "{file}" from "{os.path.dirname(tgtFile)}"')
                        os.remove(tgtFile)
            deList = list()
            for tail in self.srcFiles.keys():
                if tail not in tailList:
                    deList.append(tail)
            for tail in deList:
                del self.srcFiles[tail]
                tgtFolder = f'{self.tgtPath}{tail}'
                print(f'removing directory "{tgtFolder}"')
                shutil.rmtree(tgtFolder)
        except FileNotFoundError as err:
            print(err)

    def copy(self, folder, tgt, file):
        """uses self.checksum() and os.path.exists()
        to decide whether to copy source file/directory
        to target.

        Args:
            folder (str): current folder in os.walk() recursion.
            tgt (str): path to copy to.
            file (str): current file in os.walk() recursion.
        """
        src = f'{folder}{os.path.sep}{file}'
        tgt = f'{tgt}{os.path.sep}{file}'
        if os.path.exists(tgt):
            if not self.checksum(src, tgt):
                print(f'copying "{file}"')
                shutil.copy(src, tgt)
        else:
            print(f'copying "{file}"')
            shutil.copy(src, tgt)

    def backUp(self):
        """
        Makes clones of target directory at set interval
        """
        sep = os.path.sep
        basename = os.path.basename(self.tgtPath)
        backup = self.tgtPath+sep+'..'+sep+f'{basename}_backup'
        self.makeTgtDirs(backup)
        while len(os.listdir(backup)) > 5:
            a = sorted(os.listdir(backup)).pop(0)
            print('deleting oldest backup')
            shutil.rmtree(backup+sep+a)
        self.end = time()
        if int(self.end - self.start) > 600:
            print(f'creating backup for <{self.name}>')
            shutil.copytree(self.tgtPath, backup+sep +
                            basename+' '+str(datetime.now()))
            self.start = time()

    @classmethod
    def saveJobs(cls):
        """
        Save list of SyncDir instances using shelve module.
        """
        with shelve.open('SyncDirsData') as f:
            f['jobs'] = cls.jobs

    @classmethod
    def loadJobs(cls):
        """
        Load list of SyncDir instances using shelve module.
        """
        with shelve.open('SyncDirsData') as f:
            cls.jobs = f['jobs']

    @classmethod
    def run(cls):
        """
        Execute synchronizing process for each SyncDir instance
        in SyncDir.jobs.
        """
        while True:
            jobs = cls.jobs
            for job in jobs:
                print(job)
                job.sync()
                job.backUp()
                cls.saveJobs()
                print(datetime.now())
            sleep(10)

    @staticmethod
    def checksum(src, tgt, dir=False):
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
            for f, s, files in os.walk(src):
                for file in files:
                    path = f'{f}{os.path.sep}{file}'
                    srcSize += os.path.getsize(path)
            for f, s, files in os.walk(tgt):
                for file in files:
                    path = f'{f}{os.path.sep}{file}'
                    tgtSize += os.path.getsize(path)
            if srcSize == tgtSize:
                return True
            else:
                return False
        else:
            if os.path.getsize(src) == os.path.getsize(tgt):
                return True
            else:
                return False

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

        except FileExistsError:
            print('')


os.chdir(os.path.dirname(__file__))
if 'SyncDirsData' in os.listdir(os.getcwd()):
    SyncDirs.loadJobs()

job1 = SyncDirs('example_task', 'SOURCE DIRECTORY', 'TARGET DIRECTORY')

while True:
    SyncDirs.run()

    
