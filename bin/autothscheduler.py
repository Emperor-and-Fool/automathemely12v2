#!/usr/bin/env python3
import sys
import shutil
import logging
import time
from datetime import datetime

from schedule import Scheduler, CancelJob

from automathemely import info_or_lower_handler, warning_or_higher_handler, scheduler_file_handler, timed_details_format
from automathemely.autoth_tools.utils import get_local

logger = logging.getLogger('autothscheduler.py')
logger.propagate = False

logger.addHandler(scheduler_file_handler)
logger.addHandler(info_or_lower_handler)
logger.addHandler(warning_or_higher_handler)

for handler in logger.handlers[:]:
    handler.setFormatter(logging.Formatter(timed_details_format))


def get_next_run():
    import pickle, tzlocal, pytz
    try:
        with open(get_local('sun_times'), 'rb') as file:
            sunrise, sunset = pickle.load(file)
    except FileNotFoundError:
        import sys
        logger.error('Could not find times file, exiting...')
        sys.exit()

    try:
        local_tz = tzlocal.get_localzone()
    except Exception as e:
        logger.warning('tzlocal failed (%s), falling back to system local timezone', e)
        local_tz = datetime.now().astimezone().tzinfo

    now = datetime.now(pytz.utc).astimezone(local_tz).time()
    sunrise, sunset = (sunrise.astimezone(local_tz).time(),
                       sunset.astimezone(local_tz).time())

    if sunrise < now < sunset:
        return ':'.join(str(sunset).split(':')[:-1])
    else:
        return ':'.join(str(sunrise).split(':')[:-1])


def run_automathemely():
    """
    Run the main automathemely CLI for the scheduled event.

    Prefer a real 'automathemely' executable on PATH (user-installed launcher),
    otherwise fall back to invoking the current Python interpreter with the
    package module (-m automathemely). This ensures we stay inside the venv
    when the scheduler was started from a venv.
    """
    try:
        verify_desktop_session(True)

        # prefer an installed wrapper/launcher if available
        wrapper = shutil.which("automathemely")
        if wrapper:
            cmd = [wrapper]
        else:
            # fallback to the current interpreter running this process
            py = sys.executable or "python3"
            cmd = [py, "-m", "automathemely"]

        check_output(cmd, stderr=PIPE)
    except Exception as e:
        logger.exception("Scheduled run failed: %s", e)
    finally:
        # The scheduler expects the job to cancel itself after running once
        return CancelJob

class SafeScheduler(Scheduler):
    def __init__(self, reschedule_on_failure=False):
        self.reschedule_on_failure = reschedule_on_failure
        super().__init__()

    def _run_job(self, job):
        # noinspection PyBroadException
        try:
            super()._run_job(job)
        except Exception as e:
            logger.exception('Exception while running AutomaThemely', exc_info=e)
            job.last_run = datetime.now()
            # job._schedule_next_run()


scheduler = SafeScheduler()

while True:
    scheduler.every().day.at(get_next_run()).do(run_automathemely)

    while True:
        if not scheduler.jobs:
            logger.info('Running...')
            break
        scheduler.run_pending()
        time.sleep(1)
