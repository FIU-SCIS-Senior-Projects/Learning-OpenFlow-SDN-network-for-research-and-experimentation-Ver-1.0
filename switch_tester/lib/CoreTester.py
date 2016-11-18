""" For 2.7 print compatibility """
from __future__ import print_function

import sys
import os
import json

def fatal_error(msg):
    """ Outputs error message to STDERR, then terminates program.

        msg : str
            Message to output.
    """
    print('ERROR: {}'.format(msg), file=sys.stderr)
    # TODO consider changing from exit to raising a custom exception (RyuCompError?)
    sys.exit(1)

def verbose_msg(msg, verbose):
    """ Outputs message when verbose is True.

        msg : str
            Message to output.
        verbose : bool
            Determines whether the message is printed.
    """
    if verbose:
        print(msg)

def check_keys(dict_, keys):
    """ Check that all keys exist within a dict.

        dict_ : dict
            The dict object to look in.
        keys : iterable of str
            A list or iterable of strings for keys.

        Returns : [str]
            A list of keys not found in dict.
    """
    missing = []

    for key in keys:
        if key not in dict_:
            missing.append(key)

    return missing

def load_config(config_path, verbose=False):
    """ Load a config file (JSON formatted).
        Should a config file not exist, a default one shall be
        written to the location.

        config_path : str
            path/to/config/file
        verbose : bool
            Determines whether verbose messages are printed.
            Used solely for load_config and verbose_msg, all
            other functions get verbose through config object.

        Returns : dict
            The program configuration.
    """
            
    """ Default config dict (satisfies check_config).
        Default working directory is ~/switch_tester.
    """
    default_config = {
        'directory': '{}/switch_tester'.format(os.environ['HOME']),
    }

    """ if doesn't exist, create file using default_config """
    if not os.path.exists(config_path):
        verbose_msg(' '.join(['Config: Config file {} not found.', \
                              'Generating default config at location.']) \
		       .format(config_path), \
                    verbose)
        with open(config_path, 'w') as config_file:
            json.dump(default_config, config_file, sort_keys=True, indent=4)

    verbose_msg('Config: Loading config file {}.'.format(config_path), verbose)
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)

    """ Confirm config is usable """
    check_config(config)

    verbose_msg('Config: {} loaded successfully.'.format(config_path), verbose)
    return config

def check_config(config):
    """ Check if a configuration is valid and usable.
        If not, an error is reported.

        config : dict
            Configuration of program.
    """

    """ Check that all necessary keys are in config.
        If not, report the missing keys as an error.
    """
    check_list = ['directory']
    missing = check_keys(config, check_list)

    if len(missing) > 0:
        missing = ['Config: Missing necessary keys.'] \
                  + missing
        fatal_error('\n'.join(missing))
    
def load_target(config, switch_path):
    """ Load a target switch configuration (JSON formatted).

        config : dict
            Configuration of the program.
        switch_path: str
            path/to/target/switch

        Returns : dict
            The loaded target switch configuration.
    """
    verbose = config['verbose']

    """ If target switch not found. Report error. """
    if not os.path.exists(switch_path):
        fatal_error('Target switch file {} not found.'.format(switch_path))

    verbose_msg('Target: Loading target switch file {}.'.format(switch_path), \
                verbose)

    with open(switch_path, 'r') as switch_file:
        switch = json.load(switch_file)

    """ Confirm switch is usable """
    check_switch(switch)

    verbose_msg('Target: {} loaded successfully'.format(switch_path), verbose)
    return switch

def check_switch(switch):
    """ Check if a switch is valid and usable.
        If not, an error is reported.

        switch : dict
            Switch configuration.
    """

    """ Check that all necessary non-tester specific keys are in switch.
        If not, report the missing keys as an error.
    """
    check_list = ['model', 'description', 'of-version']
    missing = check_keys(switch, check_list)

    if len(missing) > 0:
        missing = ['Switch: Missing necessary generic keys.'] \
                  + missing
        fatal_error('\n'.join(missing))

    """ Determine and check that all necessary tester specific keys
        are in the switch.
        If not, report the missing keys as an error.
    """
    if switch['of-version'] == '1.3':
        if 'ryu' not in switch:
            fatal_error('Switch: Missing key ryu')
        else:
            switch = switch['ryu']
            check_list = ['tester-dpid', 'target-dpid']

    missing = check_keys(switch, check_list)

    if len(missing) > 0:
        missing = ['Switch: Missing necessary keys.'] \
                  + missing
        fatal_error('\n'.join(missing))

"""
    load_profile:
    Load a profile file (JSON formatted).
    profile_path: 'path/to/profile'
    verbose: If True, output verbose messages.
    return: profile dictionary object
"""
def load_profile(config, profile_path):
    """ Load an application profile (JSON formatted).

        config : dict
            Configuration of the program.
        profile_path : str
            path/to/application/profile

        Returns : dict
            Application profile information.
    """
    verbose = config['verbose']

    """ If profile not found, report the error """
    if not os.path.exists(profile_path):
        fatal_error('Profile file {} not found.'.format(profile_path))

    verbose_msg('Profile: Loading profile file {}.'.format(profile_path), verbose)
    with open(profile_path, 'r') as profile_file:
        profile = json.load(profile_file)

    """ Check that profile is valid and usable """
    check_profile(profile)

    verbose_msg('Profile: {} loaded successfully'.format(profile_path), verbose)
    return profile

def check_profile(profile):
    """ Check if a profile is valid and usable.
        If not, an error is reported.

        profile : dict
            Application profile information.
    """
    # Check if any keys missing, if so, throw error
    check_list = ['name', 'compatibility']
    missing = check_keys(profile, check_list)
        
    if len(missing) > 0:
        missing = ['Profile: Missing necessary keys.'] \
                  + missing
        fatal_error('\n'.join(missing))

def create_dir(config, dir_to_create):
    """ Creates a directory if it doesn't exist.
        On failure throws OSError or reports error.

        config : dict
            Configuration of the program
        dir_to_create : str
            path/to/dir/to/create
    """
    check_config(config)
    verbose = config['verbose']

    if not os.path.exists(dir_to_create):
        verbose_msg('Misc: Creating directory {}'.format(dir_to_create), \
                    verbose)
        os.makedirs(dir_to_create)
    elif not os.path.isdir(dir_to_create):
        fatal_error('{} already exists, but is not a directory.'\
                    .format(dir_to_create))
