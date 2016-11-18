# for 2.7 print compatibility
from __future__ import print_function
import sys
import os
import json

"""
    fatal_error:
    Outputs error to STDERR then terminates program.
    msg: Message to output
"""
def fatal_error(msg):
    print('ERROR: {}'.format(msg), file=sys.stderr)
    # TODO consider changing from exit to raising a custom exception (RyuCompError?)
    sys.exit(1)

"""
    verbose_msg:
    Outputs message when verbose option is on.
    msg: Message to output.
    verbose: If True, output the message.
"""
def verbose_msg(msg, verbose):
    if verbose:
        print(msg)

"""
    load_config:
    Load a config file (JSON formatted).
    config_path: 'path/to/config'
    verbose: If True, output verbose messages.
    return: config dictionary object
"""
def load_config(config_path, verbose=False):
    # default config dictionary object
    config = {
        'directory': '{}/switch_tester'.format(os.environ['HOME']),
    }

    # if doesn't exist, create the default config file
    if not os.path.exists(config_path):
        verbose_msg('Config: Config file {} not found. Generating default config at location.'\
		            .format(config_path), verbose)
        with open(config_path, 'w') as config_file:
            json.dump(config, config_file, sort_keys=True)

    verbose_msg('Config: Loading config file {}.'.format(config_path), verbose)
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)

    check_config(config)

    verbose_msg('Config: {} loaded successfully.'.format(config_path), verbose)
    return config

"""
    check_config:
    Check if a configuration is valid.
    config: Configuration to check.
"""
def check_config(config):
    # Check if any keys missing, if so, throw error
    check_list = ['directory']
    missing = []

    for check in check_list:
        if check not in config:
            missing.append(check)

    if len(missing) > 0:
        msg = 'Config: Missing necessary keys.'
        for miss in missing:
            msg += '\nMissing {}'.format(miss)
        fatal_error(msg)
    
"""
    load_target:
    Load a target switch configuration (JSON formatted).
    config: config dictionary object
    switch_path: 'path/to/switch'
    return: target switch dictionary object
"""
def load_target(config, switch_path):
    # TODO actually do
    return {'model':'test', 'description':'testing', 'of_version':'1.3', \
            'ryu':{'tester-dpid':'1', 'target-dpid':'2'}}

"""
    check_switch:
    Check if a switch configuration is valid.
    switch: Switch configuration to check
"""
def check_switch(switch):
    # Check if any keys missing, if so, throw error
    # First round. no specifics to Ryu or OFTest
    check_list = ['model', 'description', 'of_version']
    missing = []

    for check in check_list:
        if check not in switch:
            missing.append(check)

    if len(missing) > 0:
        msg = 'Switch: Missing necessary generic keys.'
        for miss in missing:
            msg += '\nMissing {}'.format(miss)
        fatal_error(msg)

    if switch['of_version'] == '1.3':
        if 'ryu' not in switch:
            fatal_error('Switch: Missing key ryu')
        else:
            switch = switch['ryu']
            check_list = ['tester-dpid', 'target-dpid']

    for check in check_list:
        if check not in switch:
            missing.append(check)

    if len(missing) > 0:
        msg = 'Switch: Missing necessary keys.'
        for miss in missing:
            msg += '\nMissing {}'.format(miss)
        fatal_error(msg)

"""
    load_profile:
    Load a profile file (JSON formatted).
    profile_path: 'path/to/profile'
    verbose: If True, output verbose messages.
    return: profile dictionary object
"""
def load_profile(config, profile_path):
    verbose = config['verbose']

    if not os.path.exists(profile_path):
        fatal_error('Profile file {} not found.'.format(profile_path))

    verbose_msg('Profile: Loading profile file {}.'.format(profile_path), verbose)
    with open(profile_path, 'r') as profile_file:
        profile = json.load(profile_file)

    check_profile(profile)

    verbose_msg('Profile: {} loaded successfully'.format(profile_path), verbose)
    return profile

"""
    check_profile:
    Check if a profile is valid.
    profile: Profile to check.
"""
def check_profile(profile):
    # Check if any keys missing, if so, throw error
    check_list = ['name', 'compatibility']
    missing = []
        
    for check in check_list:
        if check not in profile:
            missing.append(check)

    if len(missing) > 0:
        msg = 'Profile: Missing necessary keys.'
        for miss in missing:
            msg += '\nMissing {}'.format(miss)
        fatal_error(msg)

"""
    create_dir:
    Function to create a directory if it doesn't exist.
    Throws OSError or crashes on failure.
    dir_to_create: 'path/to/directory'
    verbose: If True, output verbose messages.
"""
def create_dir(dir_to_create, verbose=False):
    if not os.path.exists(dir_to_create):
        verbose_msg('Misc: Creating directory {}'.format(dir_to_create), verbose)
        os.makedirs(dir_to_create)
    elif not os.path.isdir(dir_to_create):
        fatal_error('{} already exists, but is not a directory.'\
                    .format(dir_to_create))


