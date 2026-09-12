"""Bundle runtime assets in wheels without maintaining a second source copy."""
from pathlib import Path
import shutil
from setuptools import setup
from setuptools.command.build_py import build_py

class BuildRuntime(build_py):
    def run(self):
        super().run()
        destination = Path(self.build_lib) / 'ocdeck' / 'runtime'
        for name in ('plugins', 'scripts'):
            shutil.copytree(name, destination / name, dirs_exist_ok=True)

setup(cmdclass={'build_py':BuildRuntime})
