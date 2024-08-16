import os
import subprocess
import shutil
from functools import wraps

class RepoManagerException(Exception):
    pass


class RepoManager:
    def __init__(self, repo_dir: str):
        repo_path = os.path.abspath(repo_dir)
        if not os.path.isdir(repo_path) or not os.path.exists(os.path.join(repo_path, '.git')):
            os.makedirs(repo_path, exist_ok=True)
            os.chdir(repo_path)
            try:
                subprocess.run(['git', 'init'], cwd=repo_path, check=True)
                subprocess.run(['git', 'lfs', 'install'],
                               cwd=repo_path, check=True)
                # subprocess.run(['git', 'lfs', 'track', '*.*'], cwd=repo_path, check=True)
                subprocess.run(['git', 'add', '.gitattributes'],
                               cwd=repo_path, check=True)
            except subprocess.CalledProcessError as e:
                raise RepoManagerException(f'git failure: {e}')
        self.repo_path = repo_path
    
    def path_exists_decorator(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not os.path.exists(self.path):
                raise FileNotFoundError(f"The path {self.path} does not exist.")
            return func(*args, **kwargs)
        return wrapper
    
    def copy_and_commit_file(self, source_file,  relative_path, commit_message):

        if not os.path.isdir(self.repo_path) or not os.path.exists(os.path.join(self.repo_path, '.git')):
            raise Exception("Invalid Repo")

        target_path = os.path.join(
            self.repo_path, os.path.dirname(relative_path))
        if not os.path.exists(target_path):
            os.makedirs(target_path, exist_ok=True)

        target_file_path = os.path.join(self.repo_path, relative_path)
        shutil.copy(source_file, target_file_path)
        os.chdir(self.repo_path)

        subprocess.run(['git', 'lfs', 'track', relative_path],
                       cwd=self.repo_path, check=True)
        subprocess.run(['git', 'add', relative_path],
                       cwd=self.repo_path, check=True)

        subprocess.run(['git', 'commit', '-m', commit_message],
                       cwd=self.repo_path, capture_output=True, text=True, check=True)

        result = subprocess.run(['git', 'log', '-1', '--format=%H', '--',
                                relative_path], capture_output=True, text=True, check=True)
        commit_hash = result.stdout.strip()
        return commit_hash
