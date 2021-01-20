import os
import sys

from setuptools import find_packages, setup

sys.path.insert(0, os.path.abspath('.'))  # isort:skip
from qa_tina_tests import version  # isort:skip


def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]


VERSION = version.__version__
NAME = "osc-qa-tina-tests"
if version.__branch__:
    NAME = "{}-{}".format(NAME, version.__branch__)

INSTALL_REQUIRES = parse_requirements('requirements.txt')


DEPS = {
    'qa_common_tools': None,
    'qa_test_tools': None,
    'qa_tina_tools': None,
    'qa_sdks': ['qa_sdk_common', 'qa_sdk_priv', 'qa_sdk_as', 'qa_sdk_pub', 'qa_sdks', 'specs'],
}
PACKAGES = []
PKG_DIR = {}

for DEP in DEPS:
    print('dep = {}'.format(DEP))
    if DEPS[DEP]:
        for SUB_DEP in DEPS[DEP]:
            PKG_DIR[SUB_DEP] = './{}/{}'.format(DEP, SUB_DEP)
        PACKAGES += [p for p in find_packages(where='./{}'.format(DEP)) if p in DEPS[DEP] or p.split('.')[0] in DEPS[DEP]]
    else:
        PKG_DIR[DEP] = './{}/{}'.format(DEP, DEP)
        tmp_pkgs = find_packages(where='./{}'.format(DEP))
        if tmp_pkgs:
            PACKAGES += [p for p in find_packages(where='./{}'.format(DEP)) if p == DEP or p.startswith('{}.'.format(DEP))]
        else:
            PACKAGES.append(DEP)

PACKAGES += find_packages(exclude=['tests'])

setup(
    name=NAME,
    version=VERSION,
    url='http://www.outscale.com',
    author="3DS Outscale QA Team",
    author_email="qa@outscale.com",
    description="3DS Outscale TINA tests",
    packages=PACKAGES,
    package_dir=PKG_DIR,
    package_data={
        'qa_test_tools.config': ['*.cfg'],
        'specs.yaml': ['*.yaml']
        #'qa_tools.specs.oapi': ['*.yaml']
    },
    # data_files = [('etc/osc-qa-tina-redwires', ['qa_tina_redwires/config/osc_credentials', 'qa_tina_redwires/config/osc_regions'])],
    classifiers=["Programming Language :: Python :: 3", "License :: OSI Approved :: MIT License", "Operating System :: OS Independent",],
    python_requires='>=3.6',
    # scripts=['qa_tina_redwires/bin/osc-qa-tina-redwires'],
    install_requires=INSTALL_REQUIRES,
)
