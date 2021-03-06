import os
from typing import List, Tuple

from .core import open_file, spawn, isolate_root_cmd
from .version import get_package_name_and_version_matcher_from_depend_line, VersionMatcher


class SrcInfo():

    _common_lines: List[str] = None
    _package_lines: List[str] = None
    path: str = None
    repo_path: str = None
    package_name: str = None

    def load_config(self) -> None:
        self._common_lines = []
        self._package_lines = []
        destination = self._common_lines
        with open_file(self.path) as srcinfo_file:
            for line in srcinfo_file.readlines():
                if line.startswith('pkgname ='):
                    if line.split('=')[1].strip() == self.package_name:
                        destination = self._package_lines
                    else:
                        destination = []
                else:
                    destination.append(line)

    def __init__(self, repo_path: str, package_name: str = None) -> None:
        self.path = os.path.join(
            repo_path,
            '.SRCINFO'
        )
        self.repo_path = repo_path
        self.package_name = package_name
        self.load_config()

    def get_values(self, field: str, lines: List[str] = None) -> List[str]:
        prefix = field + ' = '
        values = []
        if lines is None:
            lines = self._common_lines + self._package_lines
        for line in lines:
            if line.strip().startswith(prefix):
                values.append(line.strip().split(prefix)[1])
        return values

    def get_pkgbase_values(self, field: str) -> List[str]:
        return self.get_values(field, self._common_lines)

    def get_value(self, field: str) -> str:
        return self.get_values(field)[0]

    def get_install_script(self) -> str:
        values = self.get_values('install')
        if values:
            return values[0]
        return None

    def _get_depends(self, field: str) -> List[Tuple[str, VersionMatcher]]:
        dependencies = []
        for dep in self.get_pkgbase_values(field):
            pkg_name, version_matcher = get_package_name_and_version_matcher_from_depend_line(dep)
            dependencies.append((pkg_name, version_matcher))
        return dependencies

    def get_makedepends(self) -> List[Tuple[str, VersionMatcher]]:
        return self._get_depends('makedepends')

    def get_depends(self) -> List[Tuple[str, VersionMatcher]]:
        return self._get_depends('depends')

    def regenerate(self) -> None:
        with open_file(self.path, 'w') as srcinfo_file:
            result = spawn(
                isolate_root_cmd(
                    ['makepkg', '--printsrcinfo'],
                    cwd=self.repo_path
                ), cwd=self.repo_path
            )
            srcinfo_file.write(result.stdout_text)
        self.load_config()
