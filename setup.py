import os
from setuptools import setup

setup(
    name = 'SwitchTester',
    version = '0.0.1',
    author = 'Jahkell Lazarre, Steven Lyons',
    author_email = 'jlaza020@fiu.edu, slyon001@fiu.edu',
    description = ('A switch validation software package that relies on OF '
                   'testing frameworks OFTest and Ryu.'),
    license = 'GPL',
    keywords = 'switch tester of open flow openflow ryu oftest',
    url = 'http://packages.python.org/switch_tester',
    packages = ['switch_tester'],
    install_requires=['xmlrunner'],
)
