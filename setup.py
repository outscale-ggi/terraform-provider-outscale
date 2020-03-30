from setuptools import find_packages, setup

deps = ['qa_tools', 'osc_sdk_as', 'osc_sdk_priv', 'qa_sdk_pub', 'osc_common']
packages = []
pkg_dir = {}

for dep in deps:
    packages += [p for p in find_packages(where='./{}'.format(dep)) if p == dep or p.startswith('{}.'.format(dep))]
    pkg_dir[dep] = '{}/{}'.format(dep, dep)

pkg_name = 'qa_tina_redwires'
packages += [p for p in find_packages(where='.') if p == pkg_name or p.startswith('{}.'.format(pkg_name))]

setup(
    name="osc-qa-tina-redwires",
    version="0.1",
    author="3DS Outscale QA Team",
    author_email="product-qa@outscale.com",
    description="3DS Outscale Tina RedWires tests",
    #long_description="Supporting package",
    #long_description_content_type="text/markdown",
    url="http://www.outscale.com",
    packages=packages,
    package_dir = pkg_dir,
    package_data={
        'qa_tools.config': ['*.cfg'],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    scripts=['qa_tina_redwires/bin/osc-qa-tina-redwires'],
    install_requires=[
        'pytest==5.2.1',
        'requests==2.22.0',
        'paramiko==2.6.0',
        'pyOpenSSL==19.0.0',
        'cryptography==2.8',
        'PyYAML==5.1.2',
        # TODO: remove following dependancies
        'getip2==1.6',
        'boto==2.49.0',
        'botocore==1.12.250',
        'boto3==1.9.250',
    ]
)
