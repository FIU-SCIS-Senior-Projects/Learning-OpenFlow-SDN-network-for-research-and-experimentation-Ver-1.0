import lib.RyuTester as RyuTester
import lib.CoreTester as Core

import os
import sys

"""
    SwitchTester:
    DESCRIPTION

    ARGUMENTS
"""

if __name__ == '__main__':

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
        elif arg == '-i':
            interactive = True
        elif arg == '-p':
            profile_path = next(args) 
        elif arg == '-t':
            force_test = True
        elif arg == '-v':
            verbose = True
        elif arg == '-target':
            target_path = next(args)
        else:
            Core.fatal_error('Unknown argument encountered: {}'.format(arg))

    config = Core.load_config(config_path, verbose)

    # arguments that override a loaded config setup
    if backup:
        config['backup'] = backup
    if force_test:
        config['force-test'] = force_test
    if verbose:
        config['verbose'] = verbose

    # need a target switch
    if target_path:
        # load target switch
        pass
    else:
        if not interactive:
            Core.fatal_error('Missing arguments: {}'.format('Target switch location'))
        else:
            target = {}
            # ask for each necessary piece of info about target switch

    if profile_path:
        profile = Core.load_profile(profile_path, verbose)

    # if of_version == 1.0: OFTester, elif of_version == 1.3: RyuTester
    tester = RyuTester

    tester.get_results(config, profile, backup=backup, force_test=force_test,
                tester_dpid=tester_dp, target_dpid=target_dp, verbose=verbose)

    # only judging results if application profile loaded
    if profile_path:
        tester.judge_results(config, profile, verbose)
