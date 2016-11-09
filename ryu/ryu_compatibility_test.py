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
    fatal_error:
    Outputs error then terminates program.
    msg: Message to output
"""
def fatal_error(msg):
    print 'ERROR: {}'.format(msg)
    # TODO consider changing from exit to raising a custom exception (RyuCompError?)
    sys.exit(1)

verbose = False

"""
    verbose_msg:
    Outputs message when verbose option is on.
    msg: Message to output
"""
def verbose_msg(msg):
    global verbose
    if verbose:
        print msg

"""
    load_config:
    Load a config file (JSON formatted).
    config_path: 'path/to/config'
    return: config dictionary object
"""
def load_config(config_path):
    # default config dictionary object
    config = {
        'directory': '{}/ryu_results'.format(os.environ['HOME']),
    }

    # if doesn't exist, create the default config file
    if not os.path.exists(config_path):
        verbose_msg('Config: Config file {} not found. Generating default config at location.'.format(config_path))
        with open(config_path, 'w') as config_file:
            json.dump(config, config_file, sort_keys=True)

    verbose_msg('Config: Loading config file {}.'.format(config_path))
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)

    # TODO check if any missing, if so, use default settings for missing keys
    # TODO update as less/more keys are used for config

    verbose_msg('Config: {} loaded successfully.'.format(config_path))
    return config

"""
   load_profile:
   Load a profile file (JSON formatted).
   profile_path: 'path/to/profile'
   return: profile dictionary object
"""
def load_profile(profile_path):
    if not os.path.exists(profile_path):
        fatal_error('Profile file {} not found.'.format(profile_path))

    verbose_msg('Profile: Loading profile file {}.'.format(profile_path))
    with open(profile_path, 'r') as profile_file:
        profile = json.load(profile_file)

    # TODO: update as less/more keys are used for profile
    profile_keys = ['model', 'of_version', 'compatibility']
    missing_keys = []
    for key in profile_keys:
        if key not in profile:
            missing_keys.append(key)
    if len(missing_keys) > 0:
        msg = 'Profile file {} is missing necessary keys.'.format(profile_path)
        for key in missing_keys:
            msg += '\nMissing {}'.format(key)
        fatal_error(msg)

    verbose_msg('Profile: {} loaded successfully'.format(profile_path))
    return profile
        

"""
    create_dir:
    Function to create a directory if it doesn't exist.
    Throws OSError or crashes on failure.
    dir_to_create: 'path/to/directory'
"""
def create_dir(dir_to_create):
    if not os.path.exists(dir_to_create):
        verbose_msg('Misc: Creating directory {}'.format(dir_to_create))
        os.makedirs(dir_to_create)
    elif not os.path.isdir(dir_to_create):
        fatal_error('{} already exists, but is not a directory.'\
                .format(dir_to_create))

"""
    get_results:
    Check if test results already exist for the model,
      and if not, get results by running tests.
    config: Configuration dictionary object
    profile: Profile dictionary object
    backup: Backup old result files (optional)
    force_test: Run Ryu tests regardless of existing results (optional)
    NOTE: Does not catch exceptions. Failure is desired.
    NOTE: Can also end program should Ryu testing run into errors.
"""
def get_results(config, profile, backup=False, force_test=False,
                tester_dpid=1, target_dpid=2):
    switch_model = profile['model']
    of_version = profile['of_version']

    create_dir(config['directory'])
    switch_dir = '{}/{}'.format(config['directory'], switch_model)
    create_dir(switch_dir)

    switch_json = '{}/{}_{}.json'.format(switch_dir, switch_model, of_version)
    switch_csv = '{}/{}_{}.csv'.format(switch_dir, switch_model, of_version)
    if backup:
        if os.path.exists(switch_json):
            os.rename(switch_json, '{}.bak'.format(switch_json))
            verbose_msg('Misc: Backed up {0} as {0}.bak.'.format(switch_json))
        if os.path.exists(switch_csv):
            os.rename(switch_csv, '{}.bak'.format(switch_csv))
            verbose_msg('Misc: Backed up {0} as {0}.bak.'.format(switch_csv))

    if force_test or not os.path.exists(switch_json) or not os.path.exists(switch_csv):
        if force_test or not os.path.exists(switch_json):
            verbose_msg('Main: Testing {} with Ryu for {}.'\
                        .format(switch_model, of_version))

            """
                FOR TESTING WITHOUT RUNNING FULL RYU TESTS
            with open('{}/ryu_switch_test.result'.format(os.environ['HOME']), 'r') as f:
                results = f.read()
            error = []

            """
            # TODO: add some customizability options from config file
            # run tests and convert to json
            ryu_switch_test_dir = 'ryu/ryu/tests/switch'
            ryu_command = 'ryu-manager --test-switch-dir {0}/{1} --test-switch-tester {2} --test-switch-target {3} {0}/tester.py'\
                            .format(ryu_switch_test_dir, of_version, tester_dpid, target_dpid)
            ryu_test = subprocess.Popen(ryu_command.split(),\
                                        shell=True,\
                                        stdout=subprocess.PIPE,\
                                        stderr=subprocess.PIPE)
            results, error = ryu_test.communicate()
            
            # TODO: actually write output to file

            verbose_msg('Main: Testing complete.')

            if len(error) > 0:
                fatal_error('Ryu testing encountered error(s) when running:\
                             \n{}'.format(error))

            results = results.split('\n')
            ryu_to_json(results, switch_json)
    
        json_to_csv(switch_json, switch_csv)

"""
    ryu_to_json:
    With the results, converts them to the detailed
      JSON format for engineers to look at and use.
    ryu_results: Array of lines representing the output of Ryu test
    json_path: path/to/json/file
"""
def ryu_to_json(ryu_results, json_path):
    verbose_msg('Main: Saving detailed results to {}.'.format(json_path))

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

    verbose_msg('Main: {} written successfully.'.format(json_path))

"""
    json_to_csv:
    With JSON results, simplify results further to a
      simple CSV file with simple results for easy exporting.
    json_path: path/to/json/file
    csv_path: path/to/csv/file
"""
def json_to_csv(json_path, csv_path):
    verbose_msg('Main: Converting detailed {} to simplified CSV file {}.'\
                .format(json_path, csv_path))
    with open(json_path, 'r') as json_file:
        switch_json = json.load(json_file)
        with open(csv_path, 'wb') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            for test_general in sorted(switch_json):
                result = None
                for test_specific in switch_json[test_general]:
                    test_result = switch_json[test_general][test_specific]['result']
                    if not result:
                        result = test_result
                    elif result != test_result:
                        result = 'DIFF'
                csv_writer.writerow([test_general, result])
    verbose_msg('Main: {} written successfully'.format(csv_path))


"""
    judge_results:
    Judges results and outputs PASS or FAIL based on
      results of tests specified in profile. (goes to STDOUT)
    config: Configuration dictionary object
    prfile: Profile dictionary object
"""
def judge_results(config, profile):
    switch_model = profile['model']
    of_version = profile['of_version']
    switch_dir = '{}/{}'.format(config['directory'], switch_model)
    csv_path = '{}/{}_{}.csv'.format(switch_dir, switch_model, of_version)

    if not os.path.exists(csv_path):
        fatal_error('Cannot find CSV result file {}.'.format(csv_path))

    verbose_msg('Main: Beginning judging.')
    failures = []
    comp_list = profile['compatibility'][:]
    with open(csv_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        for name, result in csv_reader:
            if name in comp_list:
                if result != 'OK':
                    failures.append( (name, result) )
                comp_list.remove(name)
    if len(failures) > 0 or len(comp_list) > 0:
        print '{} FAILED'.format(profile['model'])
        for name, result in failures:
            verbose_msg('FAILED TESTS: {},{}'.format(name, result))
        for name in comp_list:
            verbose_msg('NOT FOUND: {}'.format(name))
    else:
        print '{} PASSED'.format(profile['model'])

if __name__ == '__main__':

    config_path = '{}/.ryu_testing.conf'.format(os.environ['HOME'])
    profile_path = None

    backup = False
    force_test = False

    # go through args
    # TODO: port definitions? or is that in config?
    args = iter(sys.argv[1:])
    for arg in args:
        if arg == '-b':
            backup = True
        elif arg == '-c':
            config_path = next(args)
        elif arg == '-p':
            profile_path = next(args) 
        elif arg == '-t':
            force_test = True
        elif arg == '-v':
            verbose = True
        elif arg == '-tester':
            tester_dp = next(args)
        elif arg == '-target':
            target_dp = next(args)
        else:
            fatal_error('Unknown argument encountered: {}'.format(arg))

    # TODO expand and/or replace to make sure everything needed it here
    if not profile_path:
        fatal_error('Missing arguments: {}'.format('Profile location'))

    config = load_config(config_path)
    profile = load_profile(profile_path)
    get_results(config, profile, backup=backup, force_test=force_test,
                tester_dpid=tester_dp, target_dpid=target_dp)
    judge_results(config, profile)
