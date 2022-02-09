from spex_common.config import load_config
from spex_common.modules.logging import get_logger
from spex_common.modules.database import db_instance
from spex_common.services.Timer import every
import spex_common.services.Pipeline as PipelineService
import spex_common.services.Job as JobService
import spex_common.services.Task as TaskService
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


def recursion(data, first=False):
    if data is None:
        return

    tasks = data.get("tasks")
    if tasks is not None and len(tasks) > 0:
        status = sum(item.get("status") for item in tasks) / len(tasks)
        status = int(round(status, 0))
        status = max(0, min(status, 100))
        update_box_status(data, status, first)

    if len(data.get("jobs", [])) < 1:
        return

    for item in data.get("jobs", []):
        recursion(item)


def get_box():
    logger.info("working")
    insert_task_result()
    lines = db_instance().select(collection, " FILTER doc.complete < 100")
    logger.info(f"uncompleted pipelines: {len(lines)}")
    for line in lines:
        logger.debug(f"processing pipeline: {line['_key']}")
        if data := PipelineService.get_tree(line["_key"]):
            recursion(data[0], first=True)


def insert_task_result():
    jobs = db_instance().select(collection, ' FILTER doc.status == 100 and doc.complete != True ', fields=' doc.parent ')
    if jobs is not None:
        for job in jobs:
            uncompleted_tasks = db_instance().count(collection, search=' FILTER doc.status != 100 and doc.status > 0 and doc.parent == @job and doc.complete != True ', job=str(job))

            if len(uncompleted_tasks) == 1 and uncompleted_tasks[0] == 0:
                parent = db_instance().select('jobs', ' FILTER doc._key == @jobid ', jobid=str(job))

                if parent:
                    parent = parent[0]
                    task_arr = db_instance().select(collection, ' FILTER doc.parent == @jobid and doc.status > 0 and doc.status == 100 and doc.complete != True ', jobid=str(job))
                    parent.update({'tasks': task_arr})
                    new = db_instance().insert('resource', parent, overwrite_mode='replace')

                    if new is not None:
                        for task2 in task_arr:
                            updated = db_instance().update(collection, search='FILTER doc._key == @taskid', data={'status': 100, 'complete': True}, taskid=str(task2.get('_key')))
                            logger.info(updated)


if __name__ == "__main__":
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    load_config()
    every(10, get_box)
