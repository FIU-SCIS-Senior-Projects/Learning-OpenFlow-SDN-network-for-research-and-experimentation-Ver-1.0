from lib import OFTTester as OFTTester
from lib import RyuTester as RyuTester
from lib import CoreTester as Core

import os
import sys

""" Keep Python 3 working with Python 2 """
if sys.version_info < (3,0):
    input = raw_input

"""
    SwitchTester:
    Utilizes the OFTTester and RyuTester to test target switches, and,
    if proided an application profile, can check if said application
    is fully compatible with the target switch, outputting either a
    PASS or FAIL in regards to compatibility.

    ARGUMENTS:
    -b       Backup latest test results.
    -c       path/to/SwitchTester/config
    -f       Force tester to run tests, regardless of existing results.
    -i       Interactive mode.
             (Currently, only used for target switch definition)
    -p       path/to/application/profile
    -target  path/to/target/switch/config
    -v       Turn verbose messages on.

    PREREQUISITES:
    Python 3
    Ryu (ryu-manager in particular)
    OFTest
"""

if __name__ == '__main__':
    """ Set defaults """
    config_path = '{}/.switch_tester.conf'.format(os.environ['HOME'])
    target_path = None
    profile_path = None

    backup = False
    force_test = False
    interactive = False
    verbose = False

    """ Go through command line arguments """
    args = iter(sys.argv[1:])
    for arg in args:
        if arg == '-b':
            backup = True
        elif arg == '-c':
            config_path = next(args)
        elif arg == '-f':
            force_test = True
        elif arg == '-i':
            interactive = True
        elif arg == '-p':
            profile_path = next(args) 
        elif arg == '-target':
            target_path = next(args)
        elif arg == '-v':
            verbose = True
        else:
            Core.fatal_error('Unknown argument encountered: {}'.format(arg))

    """ Load configuration at config_path """
    config = Core.load_config(config_path, verbose)

    """ Apply arguments that are missing or override a loaded config setup """
    if 'backup' not in config or backup:
        config['backup'] = backup
    if 'force-test' not in config or force_test:
        config['force-test'] = force_test
    if 'verbose' not in config or verbose:
        config['verbose'] = verbose

    if profile_path is not None:
        profile = Core.load_profile(config, profile_path)

    """ SwitchTester needs a target switch for testing """
    if target_path is not None:
        """ Load target switch configuration at target_path """
        target = Core.load_target(config, target_path)
    else:
        if not interactive:
            Core.fatal_error('Missing arguments: {}'.format('Target switch location'))
        else:
            """ If not target_path is provided, but interactive is on,
                we can ask user for information instead.
            """
            target = {}
            print('Please input target switch information:')
            print('> Model:', end='  ')
            target['model'] = input()
            print('> Description (one line):', end='  ')
            target['description'] = input()
            print('> OpenFlow version:', end='  ')
            target['of-version'] = input()

            # if of-version == 1.0: OFTester
            if target['of-version'] == '1.3':
                target['ryu'] = {}
                print('> Ryu Tester Switch DPID:', end='  ')
                target['ryu']['tester-dpid'] = input()
                print('> Ryu Target Switch DPID:', end='  ')
                target['ryu']['target-dpid'] = input()
            Core.check_switch(target)

    """ Select tester based on OpenFlow version supported by the switch """
    if target['of-version'] == '1.0':
        tester = OFTTester
    elif target['of-version'] == '1.3':
        tester = RyuTester
    else:
        fatal_error('Unknown OpenFlow version: {}'.format(target['of_version']))

    """ Get result of tests in raw output (oft or ryu file),
        a detailed JSON report, and a simple CSV report.
    """
    tester.get_results(config, target)

    """ Judge results against application profile, if provided """
    if profile_path is not None:
        tester.judge_results(config, target, profile)
