import os
import tarfile
import tempfile

from setuptools import setup
from setuptools.command import sdist

import pman.build_apps

CONFIG = pman.get_config()

APP_NAME = CONFIG['general']['name']

class SDistBuilt(sdist.sdist):
    def run(self):
        pman.core.build()
        with open('MANIFEST.in') as mfile:
            manifest = mfile.read()
        prev = manifest
        manifest +='\ngraft .built_assets'

        with open('MANIFEST.in', 'w') as mfile:
            mfile.write(manifest)

        super().run()

        with open('MANIFEST.in', 'w') as mfile:
            mfile.write(prev)

    # No way to change base_name from sub-class, so just copy/edit from base class
    def make_distribution(self):
        from distutils import dir_util
        # Don't warn about missing meta-data here -- should be (and is!)
        # done elsewhere.
        base_dir = self.distribution.get_fullname()+'-built'
        base_name = os.path.join(self.dist_dir, base_dir)

        self.make_release_tree(base_dir, self.filelist.files)
        archive_files = []              # remember names of files we create
        # tar archive must be created last to avoid overwrite and remove
        if 'tar' in self.formats:
            self.formats.append(self.formats.pop(self.formats.index('tar')))

        for fmt in self.formats:
            file = self.make_archive(base_name, fmt, base_dir=base_dir,
                                     owner=self.owner, group=self.group)
            archive_files.append(file)
            self.distribution.dist_files.append(('sdist', '', file))

        self.archive_files = archive_files

        if not self.keep_temp:
            dir_util.remove_tree(base_dir, dry_run=self.dry_run)


setup(
    name=APP_NAME,
    packages=['gamelib'],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
        'pylint~=2.6.0',
        'pytest-pylint',
    ],
    entry_points={
        'pman.converters': [
            'blend2bamex = buildtools:extended_blend2bam',
            'gen_asteroids = buildtools:gen_asteroids',
        ],
    },
    cmdclass={
        'build_apps': pman.build_apps.BuildApps,
        'sdist_built': SDistBuilt,
    },
    options={
        'build_apps': {
            'include_patterns': [
                CONFIG['build']['export_dir']+'/**',
                'settings.prc',
                'shaders/**',
            ],
            'rename_paths': {
                CONFIG['build']['export_dir']: 'assets/',
            },
            'gui_apps': {
                APP_NAME: CONFIG['run']['main_file'],
            },
            'exclude_modules': {
                '*': [
                    'limeade',
                ]
            },
            'plugins': [
                'pandagl',
                'p3openal_audio',
            ],
            'icons': {
                APP_NAME: [
                    'artResources/Icon/icon16.png',
                    'artResources/Icon/icon32.png',
                    'artResources/Icon/icon64.png',
                    'artResources/Icon/icon128.png',
                    'artResources/Icon/icon256.png',
                ],
            },
        },
    }
)
