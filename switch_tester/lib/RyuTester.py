from . import CoreTester as Core

import json
import csv
import sys
import os
import subprocess

"""
    PREREQUISITES:
     - Ryu is installed (ryu-manager in particular)
     - Ryu git repository is cloned at home directory.

    RESOURCES:
     - Python API Library
     - Ryu Test Tool Usage Examples:
        https://osrg.github.io/ryu-book/en/html/switch_test_tool.html
"""

def get_results(config, target):
    """ Check if Ryu test results already exist for the target switch,
        and if not, run tests to get results.

        config : dict
            Configuration of the program.
        target : dict
            Target switch configuration.
    """

    """ Be cautious and check that config and target are valid and usable """
    Core.check_config(config)
    Core.check_switch(target)

    backup = config['backup']
    force_test = config['force-test']
    verbose = config['verbose']

    switch_model = target['model']
    of_version = target['of-version']

    switch_dir = '{}/{}'.format(config['directory'], switch_model)
    Core.create_dir(config, switch_dir)

    switch_ryu = '{}/{}.ryu'.format(switch_dir, switch_model)
    switch_json = '{}/{}.json'.format(switch_dir, switch_model)
    switch_csv = '{}/{}.csv'.format(switch_dir, switch_model)

    """ Backup all relevant report files """
    if backup:
        if os.path.exists(switch_ryu):
            os.rename(switch_ryu, '{}.bak'.format(switch_ryu))
            Core.verbose_msg('Misc: Backed up {0} as {0}.bak.' \
                              .format(switch_ryu), \
                             verbose)
        if os.path.exists(switch_json):
            os.rename(switch_json, '{}.bak'.format(switch_json))
            Core.verbose_msg('Misc: Backed up {0} as {0}.bak.' \
                              .format(switch_json), \
                             verbose)
        if os.path.exists(switch_csv):
            os.rename(switch_csv, '{}.bak'.format(switch_csv))
            Core.verbose_msg('Misc: Backed up {0} as {0}.bak.' \
                              .format(switch_csv), \
                             verbose)

    """ Check for existance of reports.
        NOTE: Done after backup to have False when backup occurs.
    """
    ryu_exists = os.path.exists(switch_ryu)
    json_exists = os.path.exists(switch_json)
    csv_exists = os.path.exists(switch_csv)

    if force_test or not ryu_exists:
        """ Invalidate existing JSON and CSV reports (if any) since
            running new tests.
        """
        json_exists = False
        csv_exists = False

        Core.verbose_msg('Main: Testing {} with Ryu for {}.'\
                          .format(switch_model, of_version), \
                         verbose)

        tester_dpid = target['ryu']['tester-dpid']
        target_dpid = target['ryu']['target-dpid']
        """ ASSUMPTION: Ryu git cloned at home directory """
        ryu_switch_test_dir = '{}/ryu/ryu/tests/switch'.format(os.environ['HOME'])

        ryu_command = 'ryu-manager --test-switch-dir {0}/of13 --test-switch-tester {1} --test-switch-target {2} {0}/tester.py'\
                       .format(ryu_switch_test_dir, tester_dpid, target_dpid)

        ryu_test = subprocess.Popen(ryu_command.split(), \
                                    shell=True, \
                                    stdout=subprocess.PIPE, \
                                    stderr=subprocess.PIPE)
 
        """ Get output from Ryu as it's testing """
        results = []
        for line in iter(ryu_test.stderr.readline, ''):
            line = line.decode().rstrip()
            if line == '':
                break
            Core.verbose_msg(line, verbose)
            results.append(line)
        results = '\n'.join(results)

        """ Save Ryu raw test results """
        with open(switch_ryu, 'w') as ryu_file:
            ryu_file.write(results)

        Core.verbose_msg('Main: Testing complete.', verbose)

        """
            TODO: ERROR CHECK INSUFFICIENT
        if len(error) > 0:
            Core.fatal_error('Ryu testing encountered error(s) when running:\n{}'\
                              .format(error))
        """

    if not json_exists:
        """ Invalidate existing CSV report (if any) """
        csv_exists = False

        _ryu_to_json(config, switch_ryu, switch_json)

    if not csv_exists:
        _json_to_csv(config, switch_json, switch_csv)

def _ryu_to_json(config, ryu_path, json_path):
    """ Convert raw Ryu test results to a detailed JSON report
        that is saved in specified location.
        This is an internal function for RyuTester.

        config : dict
            Configuration for the program.
            Since this is an internal function, config should
            have been checked by the calling function in RyuTester.
        ryu_path : str
            path/to/ryu/results
        json_path : str
            where/to/save/json/results
    """
    verbose = config['verbose']

    Core.verbose_msg('Main: Saving detailed results to {}.' \
                      .format(json_path), \
                     verbose)

    results = {}
    errors = []
    line = ""

    with open(ryu_path, 'r') as ryu_file:
        ryu_results = iter(ryu_file.readlines())

    try:
        while True:
            """ Get test name, change to more human readable version.
                type: 00_TESTNAME (optional)
                         to 
                abv TESTNAME (optional)
            """

            """ Test results finished. We're done. """
            if 'Test end' in line:
                break

            """ Ryu test types and their abbreviations """
            test_types = ['action: set_field:', 'action:', 'group',
                          'match:', 'meter:']
            test_abbrv = ['asf', 'act', 'grp', 'mat', 'mtr']
            while not any(line.startswith(test) for test in test_types):
                line = next(ryu_results).strip()

            for test, abbv in zip(test_types, test_abbrv):
                if line.startswith(test):
                    after_test = line[len(test):].strip()
                    test_name = after_test[after_test.index('_')+1:].strip()
                    cur_test = '{} {}'.format(abbv, test_name)
                    results[cur_test] = {}
                    break

            """ Get more specific test results.
                /loc/of(config=value)/test-->'command to switch' OK/ERROR
                    Reason for error, if any.
                Don't accidentally include another test's results in
                current test. (Hence the while loop's condition)
                Other things, like reconnecting to the switches, can
                occur within the test that do not conform to testing
                patterns.
            """
            line = next(ryu_results).strip()
            while not any(line.startswith(test) for test in test_types):
                """ Test results finished. We're done. """
                if 'Test end' in line:
                    break

                if '-->' in line:
                    test_name = line[:line.index('-->')].strip()
                    after = line[line.index('-->')+3:].strip("' ")
                    if line.endswith('OK'):
                        result = 'OK'
                        details = after[:-len(result)]
                    elif line.endswith('ERROR'):
                        result = 'ERROR'
                        details = after[:-len(result)]
                        details = next(ryu_results).strip("' ") + '. ' \
                                  + details
                    else:
                        Core.fatal_error("Can't identify: {}".format(line))

                    results[cur_test][test_name] = {
                        'result':result,
                        'detail':details
                    }

                line = next(ryu_results).strip()
    except StopIteration:
        pass

    """ Save results to JSON file """
    with open(json_path, 'w') as json_file:
        json.dump(results, json_file, sort_keys=True, \
                  ensure_ascii=True, indent=4)

    Core.verbose_msg('Main: {} written successfully.'.format(json_path), \
                     verbose)

def _json_to_csv(config, json_path, csv_path):
    """ Using JSON results, simplify results for a
        CSV file containing just a test name and result.
        Internal function to RyuTester.

        config : dict
            Configuration of program.
            Since this is an internal function, config should
            have been checked by the calling function in RyuTester.
        json_path : str
            path/to/json/results
        csv_path : str
            where/to/save/csv/results
    """
    verbose = config['verbose']

    Core.verbose_msg('Main: Converting detailed {} to simplified CSV file {}.'\
                .format(json_path, csv_path), verbose)

    with open(json_path, 'r') as json_file,\
         open(csv_path, 'w') as csv_file:
        switch_json = json.load(json_file)
        csv_writer = csv.writer(csv_file, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        for test in sorted(switch_json):
            """ If all sub tests have the same outcome, use that,
                otherwise, report the difference. (OK/ERROR/DIFF)
            """
            sub_tests = list(switch_json[test].values())
            if all(sub_test['result'] == sub_tests[0]['result'] \
                   for sub_test in sub_tests):
                result = sub_tests[0]['result']
            else:
                result = 'DIFF'

            csv_writer.writerow( (test, result) )
    Core.verbose_msg('Main: {} written successfully'.format(csv_path), verbose)


def judge_results(config, target, profile):
    """ Judges CSV results against application profile's list
        of compatibility checks and outputs the judgement.
        Judgement is PASS/FAIL in regards to target switch
        and application profile.

        config : dict
            Configuration of program.
        target : dict
            Target switch configuration.
        profile : dict
            Application profile information.
    """
    """ Be cautious and check that config, target, and profile
        are all valid and usable, since this can be called from
        outside of RyuTester and usability isn't guaranteed.
    """
    Core.check_config(config)
    Core.check_switch(target)
    Core.check_profile(profile)

    verbose = config['verbose']

    switch_model = target['model']
    switch_dir = '{}/{}'.format(config['directory'], switch_model)
    csv_path = '{}/{}.csv'.format(switch_dir, switch_model)

    if not os.path.exists(csv_path):
        Core.fatal_error('Cannot find CSV result file {}.'.format(csv_path))

    Core.verbose_msg('Main: Beginning judging.', verbose)
    """ Collect ERRORs/DIFFs as failures and keep track of
        compatibility to also keep track of those not found.
    """
    failures = []
    comp_list = profile['compatibility'][:]
    with open(csv_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        for name, result in csv_reader:
            if name in comp_list:
                if result != 'OK':
                    failures.append( (name, result) )
                comp_list.remove(name)

    """ Any failures or unconfirmed compatibility checks results
        in a judgement of failure, with verbose reporting on the
        failed or not found checks.
        Otherwise, the judgement is the switch passed the application
        profile compatibility test.
    """
    if len(failures) > 0 or len(comp_list) > 0:
        print('{}: {} FAILED'.format(profile['name'], target['model']))
        for name, result in failures:
            Core.verbose_msg('FAILED TESTS: {},{}'.format(name, result),\
                             verbose)
        for name in comp_list:
            Core.verbose_msg('NOT FOUND: {}'.format(name), verbose)
    else:
        print('{}: {} PASSED'.format(profile['name'], target['model']))
