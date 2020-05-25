import uuid
import asyncio

from pytz import utc
from os.path import abspath
from abc import abstractmethod
from typing import Any, Union, Optional
from datetime import datetime, timedelta, timezone

from apscheduler.job import Job
from apscheduler.events import *
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from ascheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from aspcheduler.jobstores.base import JobLookupError
from apscheduler.schedulers import SchedulerNotRunningError
from apscheduler.schedulers import SchedulerAlreadyRunningError


event_codes = {
    "EVENT_SCHEDULER_STARTED": 'Starting Task Scheduler ...',
    "EVENT_SCHEDULER_SHUTDOWN": 'Shutting Down Task Scheduler ...',
    "EVENT_SCHEDULER_PAUSED": 'Pausing Job Callbacks ...',
    "EVENT_SCHEDULER_RESUMED": 'Resuming Job Callbacks ...',
    "EVENT_ALL_JOBS_REMOVED": 'Job Store has been cleared',

    "EVENT_JOB_ADDED": 'A Job Has Been Added: {}',
    "EVENT_JOB_REMOVED": 'A Job Has Been Removed: {}',
    "EVENT_JOB_MODIFIED": 'A Job Has Been Modified: {}',

    "EVENT_JOB_SUBMITTED": 'Starting Execution of Job: {}',

    "EVENT_JOB_EXECUTED": 'Successfully Executed Job: {}',
    "EVENT_JOB_ERROR": 'Failed to Execute Job: {} - Error: {}',
    "EVENT_JOB_MISSED": 'Failed to Execute Job: {} - Task Scheduler was not active'
}

intervals = {
    "d": 86400,
    "h": 3600,
    "m": 60,
    "s": 1
}


class TaskPayload(object):
    def __init__(self, id: str, **kwargs):
        self.id = id

        if kwargs:
            for attribute, value in kwargs.items():
                setattr(self, attribute, value)
        else:
            return

class TaskNotFound(Exception):
    def __init__(self, id: str):
        self.id = id
    def __str__(self):
        return self.id


class API():
    ''' Custom Scheduling for Long-Running Events '''

    def __init__(self, log: Any):
        self.log = log
        self.handler = AsyncIOScheduler()
        config = self._getSchedulerConfig()

        self.handler.configure(
            jobstores = config['jobstores'],
            executors = config['executors'],
            job_defaults = config['defaults'],
            timezone = utc
        )

        self.handler.add_listener(self.log_event_completion, mask='EVENT_ALL')
        self.handler.start()

    @staticmethod
    def _getSchedulerConfig() -> dict:
        config = {
            "jobstores": {
                "default": SQLAlchemyJobStore(url='')  # Configure Postgres Backend
            },
            "executors": {
                "default": ThreadPoolExecutor(20)
            },
            "job_defaults": {
                "coalesce": False,
                "max_instances": 1,
                "misfire_grace_time": 15
            }
        }

        return config

    @staticmethod
    def generate_task_id():
        unique_id = uuid.uuid1()

        return str(unique_id.node)

    @classmethod
    def time_converter(cls, *, duration: Union[str, int]):
        now = datetime.now(timezone.utc)

        if isinstance(duration, int):
            return now + timedelta(seconds=duration)

        else:
            elapsing = 0
            for interval in duration.split():
                amount = int(interval[:-1])
                multiplier = intervals[interval[-1]]

                elapsing += amount * multiplier

            return now + timedelta(seconds=elapsing)

    @classmethod
    def create_task(cls, id: Optional[str], function: str, *, args: tuple = (), kwargs: dict = {}) -> TaskPayload:
        if not id:
            id = cls.generate_task_id()

        payload = TaskPayload(id, target=function, args=args, kwargs=kwargs)

        return payload

    @abstractmethod
    async def task_executor(self, payload: TaskPayload):
        '''
            `payload` represents a packaged form of the job being executed
            This method is abstract, and should be executed in `bot/__init__.py`
        '''

    def log_event_completion(self, event) -> None:
        if isinstance(event, SchedulerEvent):
            return self.log.info('scheduler', event_codes[event.code])

        elif isinstance(event, JobEvent):
            status_msg = event_codes[event.code]
            return self.log.debug('scheduler', status_msg.format(event.job_id))

        elif isinstance(event, JobSubmissionEvent):
            status_msg = event_codes[event.code]
            return self.log.trace('scheduler', status_msg.format(event.job_id))

        elif isinstance(event, JobExecutionEvent):
            status_msg = event_codes[event.code]

            if event.code == 'EVENT_JOB_EXECUTED':
                return self.log.trace('scheduler', status_msg.format(event.job_id))
            elif event.code == 'EVENT_JOB_MISSED':
                return self.log.warn('scheduler', status_msg.format(event.job_id))
            else:
                return self.log.error('scheduler', status_msg.format(event.job_id, event.exception))

    async def schedule(self, task: Union[str, TaskPayload],
                       *, id: Optional[str], time: Union[datetime, int, str], args: tuple = (), kwargs: dict = {}) -> str:

        if not isinstance(task, TaskPayload):
            task = self.create_task(id, task, args=args, kwargs=kwargs)

        if not isinstance(time, datetime):
            time = self.time_converter(duration=time)

        self.handler.add_job(
            self.task_executor, 'date',
            id = task.id,
            args = (task, ),
            next_run_time = time,
            replace_existing = True
        )

        return task.id

    async def cancel(self, task_id: str) -> Optional[str]:
        if not self.handler.get_job(task_id):
            raise TaskNotFound(task_id)

        try:
            self.handler.remove_job(task_id)
        except JobLookupError:
            raise TaskNotFound(task_id)

        return task_id

    async def cancel_all(self) -> int:
        jobs = self.handler.get_jobs()
        self.log.info('scheduler', f'Preparing to Remove {len(jobs)} Jobs ...')

        return self.handler.remove_all_jobs()

    async def view_jobs(self) -> str:
        path = abspath(__file__).replace('api/scheduler.py', '$tmp/scheduled.txt')

        with open(path, 'w+') as log:
            self.handler.print_jobs(out=log)
            log.close()

        return path

    async def find_job(self, task_id: str) -> Optional[Job]:
        try:
            job = self.handler.get_job(task_id)
        except JobLookupError:
            raise TaskNotFound(task_id)

        return job

    async def shutdown_executor(self):
        try:
            self.handler.shutdown(wait=True)
        except SchedulerNotRunningError:
            self.log.warn('scheduler', 'Task Scheduler is not online!')

    async def start_executor(self):
        try:
            self.handler.start()
        except SchedulerAlreadyRunningError:
            self.log.warn('scheduler', 'Task Scheduler is already online!')
