from . import CoreTester as Core

import json
import csv
import sys
import os
import subprocess

"""
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
    target: Target switch configuration dictionary object
    NOTE: Does not catch exceptions. Failure is desired.
    NOTE: Can also end program should Ryu testing run into errors.
"""
def get_results(config, target):
    Core.check_config(config)
    Core.check_switch(target)

    verbose = config['verbose']

    switch_model = target['model']
    of_version = target['of_version']

    switch_dir = '{}/{}'.format(config['directory'], switch_model)
    Core.create_dir(switch_dir)

    switch_ryu = '{}/{}.ryu'.format(switch_dir, switch_model)
    switch_json = '{}/{}.json'.format(switch_dir, switch_model)
    switch_csv = '{}/{}.csv'.format(switch_dir, switch_model)

    if config['backup']:
        if os.path.exists(switch_json):
            os.rename(switch_json, '{}.bak'.format(switch_json))
            Core.verbose_msg('Misc: Backed up {0} as {0}.bak.'.format(switch_json), verbose)
        if os.path.exists(switch_csv):
            os.rename(switch_csv, '{}.bak'.format(switch_csv))
            Core.verbose_msg('Misc: Backed up {0} as {0}.bak.'.format(switch_csv), verbose)

    if config['force-test'] \
            or not os.path.exists(switch_ryu) \
            or not os.path.exists(switch_json) \
            or not os.path.exists(switch_csv):
        if config['force-test'] \
                or not os.path.exists(switch_ryu) \
                or not os.path.exists(switch_json):
            if config['force-test'] \
                    or not os.path.exists(switch_ryu):
                Core.verbose_msg('Main: Testing {} with Ryu for {}.'\
                            .format(switch_model, of_version), verbose)
    
                tester_dpid = target['ryu']['tester-dpid']
                target_dpid = target['ryu']['target-dpid']
                ryu_switch_test_dir = '{}/ryu/ryu/tests/switch'.format(os.environ['HOME'])
                ryu_command = 'ryu-manager --test-switch-dir {0}/of13 --test-switch-tester {1} --test-switch-target {2} {0}/tester.py'\
                              .format(ryu_switch_test_dir, tester_dpid, target_dpid)
                Core.verbose_msg(ryu_command, verbose)
                # shell=True to not have any output from the thing
                with open(switch_ryu, 'wb') as ryu_file:
                    ryu_test = subprocess.Popen(ryu_command.split(),\
                                            stdout=subprocess.PIPE,\
                                            stderr=subprocess.PIPE)

                    results = ryu_test.communicate()[1]
                    ryu_file.write(results)
                
    
                Core.verbose_msg('Main: Testing complete.', verbose)
    
                """
                    TODO: ERROR CHECK INSUFFICIENT
                if len(error) > 0:
                    Core.fatal_error('Ryu testing encountered error(s) when running:\n{}'\
                                      .format(error))
                """
            with open(switch_ryu, 'r') as ryu_file:
                results = ryu_file.read()
                    
            results = results.split('\n')
            ryu_to_json(config, results, switch_json)
   
        json_to_csv(config, switch_json, switch_csv)

"""
    ryu_to_json:
    With the results, converts them to the detailed
      JSON format for engineers to look at and use.
    ryu_results: Array of lines representing the output of Ryu test
    json_path: path/to/json/file
    verbose: If True, output verbose messages.
"""
def ryu_to_json(config, ryu_results, json_path):
    verbose = config['verbose']

    Core.verbose_msg('Main: Saving detailed results to {}.'.format(json_path), verbose)

    results = {}
    errors = []
    cur_test = None
    cur_test_results = {}
    i = 0
    while i < len(ryu_results):
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
        i += 1

    # when exiting loop, last tested action is not in action results
    if cur_test:
        results[cur_test] = cur_test_results

    with open(json_path, 'w') as json_file:
        json.dump(results, json_file, sort_keys=True, ensure_ascii=True, indent=4)

    Core.verbose_msg('Main: {} written successfully.'.format(json_path), verbose)

"""
    json_to_csv:
    With JSON results, simplify results further to a
      simple CSV file with simple results for easy exporting.
    json_path: path/to/json/file
    csv_path: path/to/csv/file
    verbose: If True, output verbose messages.
"""
def json_to_csv(config, json_path, csv_path):
    verbose = config['verbose']

    Core.verbose_msg('Main: Converting detailed {} to simplified CSV file {}.'\
                .format(json_path, csv_path), verbose)
    with open(json_path, 'r') as json_file,\
         open(csv_path, 'w') as csv_file:
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
            csv_writer.writerow( (test_general, result) )
    Core.verbose_msg('Main: {} written successfully'.format(csv_path), verbose)


"""
    judge_results:
    Judges results and outputs PASS or FAIL based on
      results of tests specified in profile. (goes to STDOUT)
    config: Configuration dictionary object
    prfile: Profile dictionary object
    verbose: If True, output verbose messages.
"""
def judge_results(config, target, profile):
    verbose = config['verbose']

    switch_model = target['model']
    switch_dir = '{}/{}'.format(config['directory'], switch_model)
    csv_path = '{}/{}.csv'.format(switch_dir, switch_model)

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
        print('{}: {} FAILED'.format(profile['name'], target['model']))
        for name, result in failures:
            Core.verbose_msg('FAILED TESTS: {},{}'.format(name, result), verbose)
        for name in comp_list:
            Core.verbose_msg('NOT FOUND: {}'.format(name), verbose)
    else:
        print('{}: {} PASSED'.format(profile['name'], target['model']))
