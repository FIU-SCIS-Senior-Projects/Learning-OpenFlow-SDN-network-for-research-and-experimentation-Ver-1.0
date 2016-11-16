import CoreTester as Core

import json
import csv
import sys
import os
import subprocess

"""
    DESIGN DETAILS: 
    CLI command:
    python ryu_compatibility_test.py -p path/to/profile
    CLI arguments:
      -b backup old results
      -c path/to/config
      -p path/to/profile
      -t force testing
      -v verbose messages on

      Specific to Ryu testing
      -tester tester switch datapath ID
      -target target switch datapath ID 

    Configuration file at predetermined point or given as argument is:
      - default location - home directory as .ryu_testing.conf
      - JSON file containing:
        > working directory
        > ryu testing configurations

    Working directory contains directories for each switch model.
    Each switch model directory contains two files:
      model.json - Detailed test report
      model.csv - Simplified test report (for easy exporting and viewing)

    Profile is provided by the user in JSON file:
      - model name
      - OpenFlow version
      - required switch compatibility
        > NOTE: For name of features to test, see TODO

    NOTE: Please run this on c0 of Ryu mininet xterm so Ryu testing may run
          correctly.
    NOTE: During Ryu testing, default port values are used for sending and
          receiving ports.

    RESOURCES:
     - Python API Library
     - Ryu Test Tool Usage Examples:
        https://osrg.github.io/ryu-book/en/html/switch_test_tool.html
"""

"""
    get_results:
    Check if test results already exist for the model,
      and if not, get results by running tests.
    config: Configuration dictionary object
    profile: Profile dictionary object
    backup: Backup old result files (optional)
    force_test: Run Ryu tests regardless of existing results (optional)
    verbose: If True, output verbose messages.
    NOTE: Does not catch exceptions. Failure is desired.
    NOTE: Can also end program should Ryu testing run into errors.
"""
def get_results(config, profile, backup=False, force_test=False,
                tester_dpid=1, target_dpid=2, verbose=False):
    Core.check_config(config)
    Core.check_profile(profile)

    switch_model = profile['name']
    of_version = profile['of_version']

    switch_dir = '{}/{}'.format(config['directory'], switch_model)
    Core.create_dir(switch_dir)

    switch_json = '{}/{}_{}.json'.format(switch_dir, switch_model, of_version)
    switch_csv = '{}/{}_{}.csv'.format(switch_dir, switch_model, of_version)

    if backup:
        if os.path.exists(switch_json):
            os.rename(switch_json, '{}.bak'.format(switch_json))
            Core.verbose_msg('Misc: Backed up {0} as {0}.bak.'.format(switch_json), verbose)
        if os.path.exists(switch_csv):
            os.rename(switch_csv, '{}.bak'.format(switch_csv))
            Core.verbose_msg('Misc: Backed up {0} as {0}.bak.'.format(switch_csv), verbose)

    if force_test or not os.path.exists(switch_json) or not os.path.exists(switch_csv):
        if force_test or not os.path.exists(switch_json):
            Core.verbose_msg('Main: Testing {} with Ryu for {}.'\
                        .format(switch_model, of_version), verbose)

            """
                FOR TESTING WITHOUT RUNNING FULL RYU TESTS
            with open('{}/ryu_switch_test.result'.format(os.environ['HOME']), 'r') as f:
                results = f.read()
            error = []

            """
            ryu_switch_test_dir = 'ryu/ryu/tests/switch'
            ryu_command = 'ryu-manager --test-switch-dir {0}/{1} --test-switch-tester {2} --test-switch-target {3} {0}/tester.py'\
                            .format(ryu_switch_test_dir, of_version, tester_dpid, target_dpid)
            ryu_test = subprocess.Popen(ryu_command.split(),\
                                        shell=True,\
                                        stdout=subprocess.PIPE,\
                                        stderr=subprocess.PIPE)
            results, error = ryu_test.communicate()
            
            # TODO: actually write raw Ryu output to file?

            Core.verbose_msg('Main: Testing complete.', verbose)

            if len(error) > 0:
                Core.fatal_error('Ryu testing encountered error(s) when running:\
                             \n{}'.format(error))

            results = results.split('\n')
            ryu_to_json(results, switch_json, verbose)
   
        json_to_csv(switch_json, switch_csv, verbose)

"""
    ryu_to_json:
    With the results, converts them to the detailed
      JSON format for engineers to look at and use.
    ryu_results: Array of lines representing the output of Ryu test
    json_path: path/to/json/file
    verbose: If True, output verbose messages.
"""
def ryu_to_json(ryu_results, json_path, verbose=False):
    Core.verbose_msg('Main: Saving detailed results to {}.'.format(json_path), verbose)

    results = {}
    errors = []
    cur_test = None
    cur_test_results = {}
    i = -1
    while True:
        i += 1
        line = ryu_results[i]
        line = line.strip()
    
        if 'Test end' in line:
            break

        """
            TEST FORMAT
            type: 00_TESTNAME (optional)
        """
        type_tests = ['action: set_field:', 'action:', 'group:',
                       'match:', 'meter:']
        type_shorts = ['asf', 'act', 'grp', 'mat', 'mtr']
        if any([line.startswith(start) for start in type_tests]):
            if cur_test:
                results[cur_test] = cur_test_results
            for j, start in enumerate(type_tests):
                if line.startswith(start):
                    after_type = line[len(start):]
                    test_name = after_type[after_type.index('_')+1:]
                    cur_test = '{} {}'.format(type_shorts[j], test_name)
                    break
            cur_test_results = {}

        # a test result usually in the form of:
        # /loc/of(config=value)/test-->'response from switch' OK/ERROR
        elif '-->' in line:
            # get test location, save result and details
            test = line[:line.index('-->')].strip()
            if line[-2:] == 'OK':
                details = line[line.index('-->')+3:-2].strip("' ")
                cur_test_results[test] = { 'result':'OK', 'detail':details }
            elif line[-5:] == 'ERROR':
                details = line[line.index('-->')+3:-5].strip("' ")
                i += 1
                details = ryu_results[i].strip("' ") + '. ' + details
                cur_test_results[test] = { 'result':'ERROR', 'detail':details }

    # when exiting loop, last tested action is not in action results
    if cur_test:
        results[cur_test] = cur_test_results

    with open(json_path, 'w') as json_file:
        json.dump(results, json_file, sort_keys=True, ensure_ascii=True)

    Core.verbose_msg('Main: {} written successfully.'.format(json_path), verbose)

"""
    json_to_csv:
    With JSON results, simplify results further to a
      simple CSV file with simple results for easy exporting.
    json_path: path/to/json/file
    csv_path: path/to/csv/file
    verbose: If True, output verbose messages.
"""
def json_to_csv(json_path, csv_path, verbose=False):
    Core.verbose_msg('Main: Converting detailed {} to simplified CSV file {}.'\
                .format(json_path, csv_path), verbose)
    with open(json_path, 'r') as json_file,\
         open(csv_path, 'wb') as csv_file:
        switch_json = json.load(json_file)
        csv_writer = csv.writer(csv_file, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        for test_general in sorted(switch_json):
            # all specific tests need to have the same result to make a conclusion
            result = None
            for test_specific in switch_json[test_general]:
                test_result = switch_json[test_general][test_specific]['result']
                if not result:
                    result = test_result
                elif result != test_result:
                    result = 'DIFF'
            csv_writer.writerow([test_general, result])
    Core.verbose_msg('Main: {} written successfully'.format(csv_path), verbose)


"""
    judge_results:
    Judges results and outputs PASS or FAIL based on
      results of tests specified in profile. (goes to STDOUT)
    config: Configuration dictionary object
    prfile: Profile dictionary object
    verbose: If True, output verbose messages.
"""
def judge_results(config, profile, verbose=False):
    switch_model = profile['model']
    of_version = profile['of_version']
    switch_dir = '{}/{}'.format(config['directory'], switch_model)
    csv_path = '{}/{}_{}.csv'.format(switch_dir, switch_model, of_version)

    if not os.path.exists(csv_path):
        Core.fatal_error('Cannot find CSV result file {}.'.format(csv_path))

    Core.verbose_msg('Main: Beginning judging.', verbose)
    failures = []
    comp_list = profile['compatibility'][:]
    with open(csv_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        for name, result in csv_reader:
            if name in comp_list:
                if result != 'OK':
                    failures.append( (name, result) )
                comp_list.remove(name)
    # any compatibility failures or features without results are reported
    if len(failures) > 0 or len(comp_list) > 0:
        print '{} FAILED'.format(profile['model'])
        for name, result in failures:
            Core.verbose_msg('FAILED TESTS: {},{}'.format(name, result), verbose)
        for name in comp_list:
            Core.verbose_msg('NOT FOUND: {}'.format(name), verbose)
    else:
        print('{} PASSED'.format(profile['model']))
