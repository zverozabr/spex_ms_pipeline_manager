from spex_common.config import load_config
from spex_common.modules.logging import get_logger
from spex_common.modules.database import db_instance
from spex_common.services.Timer import every
import spex_common.services.Pipeline as PipelineService
import spex_common.services.Job as JobService
import spex_common.services.Task as TaskService
from spex_common.models.Status import PipelineStatus
import logging

logger = get_logger("pipeline_manager")
collection = "pipeline"


def update_tasks_to_start_from_pending(data, status, first):
    if status < 100:
        for box in data.get("jobs", []):
            for _task in box.get("tasks", []):
                if 0 <= _task["status"] < 100:
                    _data = {"status": -1}
                    logger.debug(f"task {_task.get('id')} updating {_data}")
                    TaskService.update(_task.get("id"), data=_data)

    if status == 100:
        for box in data.get("jobs", []):
            for _task in box.get("tasks", []):
                if _task["status"] == -1:
                    _data = {"status": 0}
                    logger.debug(f"task {_task.get('id')} updating {_data}")
                    TaskService.update(_task.get("id"), data=_data)

    if first:
        for _task in data["tasks"]:
            if _task["status"] == -1:
                _data = {"status": 0}
                logger.debug(f"task {_task.get('id')} updating {_data}")
                TaskService.update(_task.get("id"), data=_data)


def update_box_status(data, status, first):
    update_tasks_to_start_from_pending(data, status, first)

    if data.get("status") == status:
        return

    _data = {"status": status}
    logger.debug(f"job {data.get('id')} updating {_data}")
    JobService.update_job(data.get("id"), _data)


def recursion(data, first=False, _status: int = None):
    if data is None:
        return

    tasks = data.get("tasks")
    if tasks is not None and len(tasks) > 0:
        status = sum(item.get("status") for item in tasks) / len(tasks)
        status = int(round(status, 0))
        status = max(0, min(status, 100))
        if _status:
            status = _status
        update_box_status(data, status, first)

    if len(data.get("jobs", [])) < 1:
        return

    for item in data.get("jobs", []):
        recursion(item, first=False, _status=_status)


def get_box():
    logger.info("working")
    lines = db_instance().select(collection, " FILTER doc.complete <= 100")
    logger.info(f"uncompleted pipelines: {len(lines)}")
    for line in lines:
        logger.debug(f"processing pipeline: {line['_key']}")
        if data := PipelineService.get_tree(line["_key"]):
            status = None
            if data[0].get("status") in [PipelineStatus.stopped.value, PipelineStatus.started.value]:
                status = data[0].get("status")

            recursion(data[0], first=True, _status=status)

            job_ids = PipelineService.get_jobs(data[0].get('jobs', []))
            jobs = JobService.select_jobs(condition="in", _id=job_ids)
            pipeline_status = 0
            if jobs is not None:
                for job in jobs:
                    pipeline_status += job.get('status', 0)
                pipeline_status = int(round(pipeline_status / len(jobs), 0))
                if data[0].get("status") != pipeline_status:
                    updated = PipelineService.update(
                        data[0].get('id'),
                        data={"complete": pipeline_status},
                        collection='pipeline'
                    )
                    if updated:
                        logger.debug(f"processing pipeline: {line['_key']} changed status to: {pipeline_status}")


if __name__ == "__main__":
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    load_config()
    every(10, get_box)
