from lib import RyuTester
from lib import CoreTester as Core

import os
import sys

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
    # Defaults
    config_path = '{}/.ryu_testing.conf'.format(os.environ['HOME'])
    target_path = None
    profile_path = None

    backup = False
    force_test = False
    interactive = False
    verbose = False

    # go through args
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

    # load configuration at config_path
    config = Core.load_config(config_path, verbose)

    # arguments that override a loaded config setup
    if backup or 'backup' not in config:
        config['backup'] = backup
    if force_test or 'force-test' not in config:
        config['force-test'] = force_test
    if verbose or 'verbose' not in config:
        config['verbose'] = verbose

    if profile_path:
        profile = Core.load_profile(config, profile_path)

    # need a target switch
    if target_path:
        # load target switch
        target = Core.load_target(config, target_path)
    else:
        if not interactive:
            Core.fatal_error('Missing arguments: {}'.format('Target switch location'))
        else:
            target = {}
            # ask for each necessary piece of info about target switch
            # model (non-empty string)
            # description
            # of_version
            # if of_version == '1.3': ask for tester-dpid and target-dpid

    # if of_version == 1.0: OFTester
    if target['of_version'] == '1.3':
        tester = RyuTester
    else:
        fatal_error('Unknown OpenFlow version: {}'.format(target['of_version']))

    tester.get_results(config, target)

    # only judging results if application profile loaded
    if profile_path:
        tester.judge_results(config, target, profile)
