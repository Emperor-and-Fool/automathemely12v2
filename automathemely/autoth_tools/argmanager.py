#!/usr/bin/env python3
import argparse
import sys
import json
import logging
import pickle as pkl

from automathemely.autoth_tools.utils import get_local, read_dict, write_dic

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
options = parser.add_mutually_exclusive_group()
options.add_argument('-l', '--list', help='list all current settings', action='store_true', default=False)
options.add_argument('-s', '--setting', help="change a specific setting (e.g. key.subkey=value)")
options.add_argument('-m', '--manage', help='easier to use settings manager GUI', action='store_true',
                     default=False)
options.add_argument('-u', '--update', help='update the sunrise and sunset\'s times manually', action='store_true',
                     default=False)
options.add_argument('-r', '--restart',
                     help='(re)start the scheduler script if it were to not start or stop unexpectedly',
                     action='store_true', default=False)
options.add_argument('-L', '--light', help='apply light theme', action='store_true', default=False)
options.add_argument('-D', '--dark', help='apply dark theme', action='store_true', default=False)

#   For --list arg
def print_list(d, indent=0):
    for key, value in d.items():
        print('{}{}'.format('\t' * indent, key), end='')
        if isinstance(value, dict):
            print('.')
            print_list(value, indent + 1)
        else:
            print(' = {}'.format(value))


#   ARGUMENTS FUNCTION
def main(us_se):
    args = parser.parse_args()

    #   LIST
    if args.list:
        logger.info('Printing current settings...')
        print('')
        print_list(us_se)
        return

    #   SET
    elif args.setting:
        if not args.setting.count('=') == 1:
            logger.error('Invalid string (None or more than one "=" signs)')
            return

        setts = args.setting.split('=')
        to_set_key = setts[0].strip()
        to_set_val = setts[1].strip()

        if to_set_key == '':
            logger.error('Invalid string (Empty key)')
        elif to_set_key[-1] == '.':
            logger.error('Invalid string (Key ends in dot)')
        if not to_set_val:
            logger.error('Invalid string (Empty value)')
        elif to_set_val.lower() in ['t', 'true']:
            to_set_val = True
        elif to_set_val.lower() in ['f', 'false']:
            to_set_val = False
        else:
            try:
                to_set_val = int(to_set_val)
            except ValueError:
                try:
                    to_set_val = float(to_set_val)
                except ValueError:
                    pass

        if to_set_key.count('.') > 0:
            key_list = [s.strip() for s in to_set_key.split('.')]
        else:
            key_list = [to_set_key]

        if read_dict(us_se, key_list) is not None:
            write_dic(us_se, key_list, to_set_val)

            with open(get_local('user_settings.json'), 'w') as file:
                json.dump(us_se, file, indent=4)

            # Warning if user disables auto by --setting
            if 'enabled' in to_set_key and not to_set_val:
                logger.warning('Remember to set all the necessary values with either --settings or --manage')
            logger.info('Successfully set key "{}" as "{}"'.format(to_set_key, to_set_val))
            exit()

        else:
            logger.error('Key "{}" not found'.format(to_set_key))

        return

    #   MANAGE
    elif args.manage:
        from . import settsmanager
        #   From here on the manager takes over 'til exit
        settsmanager.main(us_se)
        return

    #   RESTART
    elif args.restart:
        # Purpose: stop any existing scheduler and spawn a detached scheduler process
        # whose stdout/stderr are atomically bound to the scheduler logfile so we
        # capture early startup errors. Keep parent-side logging minimal.

        from automathemely.autoth_tools.utils import pgrep, get_bin, get_local
        import os
        import time
        from subprocess import Popen

        # 1) Kill any running scheduler (best-effort)
        if pgrep(['autothscheduler.py'], use_full=True):
            Popen(['pkill', '-f', 'autothscheduler.py']).wait()

        # 2) Path to scheduler log (we no longer rotate here; rotation lives in __init__.py)
        log_path = get_local('.autothscheduler.log')

        # 3) Parent marker (small, non-verbose): timestamp + VIRTUAL_ENV for later comparison
        try:
            with open(log_path, 'a', buffering=1) as m:
                m.write('=== parent spawn attempt at {}\n'.format(time.strftime('%Y-%m-%d %H:%M:%S')))
                m.write(f'PARENT_PID={os.getpid()}\n')
                m.write(f'VIRTUAL_ENV={os.environ.get("VIRTUAL_ENV")}\n')
                m.flush()
        except Exception:
            # never raise here; best-effort diagnostic only
            pass

        # 4) Pre-exec setup that runs inside the child (before Python code executes):
        #    - create a new session (setsid) so the child is disowned from the parent
        #    - open the logfile and dup it to stdout/stderr so any early output is captured
        def _preexec_setup():
            try:
                os.setsid()
            except Exception:
                pass
            fd = os.open(log_path, os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o644)
            # atomic replacement of stdout/stderr
            os.dup2(fd, 1)
            os.dup2(fd, 2)
            if fd > 2:
                os.close(fd)

        # 5) Spawn the scheduler. We call the repo bin via get_bin() (repo must be importable).
        try:
            p = Popen([sys.executable, get_bin('autothscheduler.py')],
                      preexec_fn=_preexec_setup,
                      close_fds=True)
        except Exception as e:
            # record spawn failure in main logger and append a brief marker to the logfile
            logger.exception('Failed to spawn autothscheduler.py: %s', e)
            try:
                with open(log_path, 'a', buffering=1) as m:
                    m.write('=== spawn exception: {}\n'.format(e))
                    m.flush()
            except Exception:
                pass
            return

        # 6) Short delay to detect an immediate crash; log outcome and PID
        time.sleep(0.3)
        if p.poll() is not None:
            rc = p.returncode
            logger.warning('autothscheduler.py exited immediately (rc=%s)', rc)
            try:
                with open(log_path, 'a', buffering=1) as m:
                    m.write('=== child exited immediately rc={}\n'.format(rc))
                    m.flush()
            except Exception:
                pass
        else:
            logger.info('Restarted the scheduler (pid=%s)', getattr(p, 'pid', 'unknown'))
    
    #   MANUAL theme mode
    elif args.light:
        return 'light'
    elif args.dark:
        return 'dark'

