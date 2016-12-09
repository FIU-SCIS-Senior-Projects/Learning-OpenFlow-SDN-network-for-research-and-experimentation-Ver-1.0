from . import CoreTester as Core

import copy
import csv
import json
from multiprocessing import Process
import os
import shlex
import subprocess
import sys
import xml.etree.ElementTree as ET

"""
    PREREQUISITES:
    - Mininet and OFTest is installed (OFTest is installed automatically on
      Mininet virtual machines).
"""

def parse_oft_xml(xml_path):
    """Parses OFTest's XML files generated via the --xunit option. Returns a 
    dictionary where the keys are the protocol/test name and the values are the
    result of the test (OK, ERROR, FAIL) and the detail of the test such as an
    error description. If no error occurred, then the value of detail is "none".
    
    xml_path : string
        Path of directory containing OFTest's XML output files.
    """

    xml_tree = ET.parse(xml_path)

    # Retrieve test suite info.
    test_suite = xml_tree.getroot()
    num_errors = int(test_suite.get('errors'))
    num_failures = int(test_suite.get('failures'))

    result = 'OK'

    if(num_errors > 0):
        result = 'ERROR'

    if(num_failures > 0):
        result = 'FAIL'

    # Retrieve test cases info.
    test_cases = test_suite.findall('testcase')    
    results_dict = {}

    for test_case in test_cases:
        test_case_name = test_case.get('classname')
        error = test_case.find('error')  
        error_message = "none"

        if(error != None):
            error_message = error.get('message')            

        results_dict[test_case_name] = {'result':result, 'detail':error_message}

    return results_dict

def generate_json_log(oft_xml_dir, json_path, profile=None):
    """Reads and parses all OFTest-generated XML files specified by the OFTest
    XML directory and writes report to the specified JSON path.
    
    oft_xml_dir : string
        Path of OFTest directory where the XML output files are generated.
    
    json_path : string
        Path of the to-be-generated JSON report.
    
    Keyword arguments:
    profile : dict
        Application profile.
    """

    results_dict = {}

    # Build list of test case dictionaries by parsing every XML file in the 
    # given XML result directory.
    for (dirpath, dirnames, filenames) in os.walk(os.path.abspath(oft_xml_dir)):
        for filename in filenames:
            results_dict.update(parse_oft_xml(os.path.join(dirpath,filename)))

    # Validate profile?? Throw exception or ignore?

    # Prune test cases according to application profile.
    results_dict_temp = copy.deepcopy(results_dict)

    if(profile != None):
        for key in results_dict: 
            if(not key in profile['compatibility']):
                del results_dict_temp[key]
            
    results_dict = results_dict_temp

    # Write JSON log file.
    with open(json_path, 'w') as json_log_file:
        json_log = json.dumps(results_dict, indent=4, separators=(',', ':'))
        json_log_file.write(json_log)

def execute_subprocess(args, stdout_redirect=None, stderr_redirect=None,
                       stderr_to_stdout=False, check_return=False):
    """Executes a subprocess specified by a command line.
    
    args : string
        Command line that will be run.
    
    Keyword arguments:
    stdout_redirect : file, subprocess.PIPE
        STDOUT redirect of subprocess.
    
    stderr_redirect : file, subprocess.PIPE
        STDERR redirect of subprocess.
    
    stderr_to_stdout : bool
        Whether or not to redirect the subprocess's STDERR to the system's
        STDOUT.
    """

    subproc = subprocess.Popen(shlex.split(args), stdout=stdout_redirect,
        stderr=stderr_redirect, universal_newlines=True)
    stderr_data = ''

    try:

        if(stderr_to_stdout == True):
            stderr_lines = iter(subproc.stderr.readline, '')

            for line in stderr_lines:
                stderr_data += line
                sys.stdout.write(line)

        subproc.communicate()

        if(check_return == True and subproc.returncode != 0):
            raise subprocess.CalledProcessError(subproc.returncode, args)

    except subprocess.CalledProcessError as e:
        print('CalledProcessError')
        raise e
    except BaseException as e:
        print('BaseException')
        subproc.kill()
        raise e 

    return stderr_data

def run_switch(cmdline, stdout_redirect=None, stderr_redirect=None):
    """Executes run_switch.py script in OFTest.
    
    cmdline : string
        Command line that will be executed to run OFTest's run_switch.py.
    
    Keyword arguments:
    stdout_redirect : file, subprocess.PIPE
        STDOUT redirect of run_switch.py.
        
    stderr_redirect : file, subprocess.PIPE
        STDERR redirect of run_switch.py.
    """

    rs_stdout = None
    rs_stderr = None

    if(stdout_redirect):
        rs_stdout = open(stdout_redirect, 'w') 
    else:
        rs_stdout = subprocess.PIPE

    if(stderr_redirect):
        rs_stderr = open(stderr_redirect, 'w')
    else:
        rs_stderr = subprocess.PIPE

    error = None

    try:
        execute_subprocess(cmdline, stdout_redirect=rs_stdout,
                       stderr_redirect=rs_stderr)
    except BaseException as e:
        error = e

    if(stdout_redirect):
        rs_stdout.close()

    if(stderr_redirect):
        rs_stderr.close()

    if(error):
        sys.exit(1)

def run_oftest(cmdline, stderr_redirect=None, stderr_to_stdout=False):
    """Runs OFTest.
    
    cmdline : string
        Command line that will be executed to run OFTest.
    
    Keyword arguments:
    stderr_redirect : file, subprocess.PIPE
        STDERR redirect of OFTest.
        
    stderr_to_stdout : bool
        Whether or not to redirect OFTest's STDERR to the system's STDOUT.
    """

    oft_stderr = None

    if(stderr_redirect):
        oft_stderr = open(stderr_redirect, 'w')
    else:
        oft_stderr = subprocess.PIPE

    stderr_data = execute_subprocess(cmdline, stderr_redirect=subprocess.PIPE,
        stderr_to_stdout=stderr_to_stdout)    

    if(stderr_redirect):
        oft_stderr.write(stderr_data)
        oft_stderr.close()

def construct_if_args(if_str):
    """Returns interface command line arguments for OFTest.
    
    if_str : string
        String loaded from configuration that contains comma-delimited command
        line arguments that denote the port numbers and dataplane interfaces
        to use in OFTest. Example: ("1@veth1,2@veth3,...").
    """
    
    if_args = ' '
    interfaces = if_str.split(',')
    for interface in interfaces:
        if_args += '-i ' + interface + ' '     

    return if_args

def get_results(config, target, profile=None):
    """ Runs switch (if run_switch_script is true in configuration), OFTest,
    and produces JSON report.
    
    config : dict
        Application configuration.
    
    target : dict
        Target switch configuration.
    
    Keyword arguments:
    profile : dict
        Application profile.
    """

    Core.check_config(config)
    Core.check_switch(target)

    backup = config['backup']
    force_test = config['force-test']
    verbose = config['verbose']

    switch_model = target['model']
    of_version = target['of-version']
    interfaces = construct_if_args(target['oftest']['interfaces'])
    run_switch_script = target['oftest']['run-switch-script']

    switch_dir = '{}/{}'.format(config['directory'], switch_model)
    Core.create_dir(config, switch_dir)

    switch_json = '{}/{}.json'.format(switch_dir, switch_model)
    switch_csv = '{}/{}.csv'.format(switch_dir, switch_model)

    oft_dir = '{}/oftest'.format(os.environ['HOME'])
    oft_script = '{}/{}'.format(oft_dir, 'oft')
    oft_stderr = '{}/{}.txt'.format(switch_dir, 'stderr')
    oft_xml_dir = '{}/{}/{}'.format(switch_dir, switch_model, 'oftest-xml')
    Core.create_dir(config, oft_xml_dir)

    oft_cmdline = 'sudo {executable} {oft_script} basic {interfaces} --xunit --xunit-dir={xunit_dir}'.format(executable=sys.executable, oft_script=oft_script, interfaces=interfaces, xunit_dir=oft_xml_dir)

    switch_cmdline = 'sudo {executable} {oft_dir}/run_switch.py'.format(executable=sys.executable, oft_dir=oft_dir)

    oftest_process = Process(target=run_oftest, args=(oft_cmdline, oft_stderr, verbose))
    switch_process = None

    if(run_switch_script == True):
        switch_process = Process(target=run_switch, args=(switch_cmdline,))
        switch_process.start()

    oftest_process.start()

    if(run_switch_script == True):
        switch_process.join()
        if(switch_process.exitcode != 0):
            oftest_process.terminate()
            Core.fatal_error("Switch stopped abruptly. Terminating.")
            return

    oftest_process.join()

    generate_json_log(oft_xml_dir, switch_json, profile=profile)
    json_report_to_csv(switch_json, switch_csv)

def judge_results(config, target, profile):
	""" Judges CSV results against application profile's list of compatibility
	checks and outputs the judgement. Judgement is PASS/FAIL in regards to
	target switch and application profile.

        config : dict
            Configuration of program.
        target : dict
            Target switch configuration.
        profile : dict
            Application profile information.

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

        failures = []
        comp_list = profile['compatibility'][:]
        with open(csv_path, 'r') as csv_file:

            csv_reader = csv.reader(csv_file)

            for name, result in csv_reader:
                
                if name in comp_list:
                    
                    if result != 'OK':
                        failures.append( (name, result) )
       
                    comp_list.remove(name)

        if (len(failures) > 0 or len(comp_list) > 0):
            print('{}: {} FAILED'.format(profile['name'], target['model']))

            for name, result in failures:
                Core.verbose_msg('FAILED TESTS: {},{}'.format(name, result),\
                             verbose)

            for name in comp_list:
                Core.verbose_msg('NOT FOUND: {}'.format(name), verbose)
        else:
            print('{}: {} PASSED'.format(profile['name'], target['model']))

def json_report_to_csv(json_path, csv_path):
    """Generates CSV report from JSON report, outputting only rows of test case
    names, followed by the result of the test (OK, ERROR, FAIL).
    
    json_path : string
        Path of existing JSON report.
    csv_path : string
        Path of to-be-generated CSV report.
    """

    with open(json_path, 'r') as json_report, open(csv_path, 'w') as csv_report:
        report = json.loads(json_report.read())
     
        for key, value in report.iteritems():
            csv_report.write(key + ',' + value['result'] + '\n')
