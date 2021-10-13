from spex_common.config import load_config
from spex_common.modules.database import db_instance
import spex_common.services.Pipeline as PipelineService
import spex_common.services.Job as JobService
import spex_common.services.Task as TaskService
from spex_common.modules.logging import get_logger
from services.Timer import every

logger = get_logger('pipeline_manager')
collection = "pipeline"


def update_tasks_to_start_from_pending(data, status, first):
    if status < 100:
        for box in data["jobs"]:
            for _task in box["tasks"]:
                if _task["status"] < 100 and _task["status"] != -1:
                    _data = {"status": -1}
                    TaskService.update(_task.get("id"), data=_data)
                    logger.debug(f"task {_task.get('id')} updated {_data}")

    if status == 100:
        for box in data["jobs"]:
            for _task in box["tasks"]:
                if _task["status"] in [-1]:
                    _data = {"status": 0}
                    TaskService.update(_task.get("id"), data=_data)
                    logger.debug(f"task {_task.get('id')} updated {_data}")
    if first:
        for _task in data["tasks"]:
            if _task["status"] == -1:
                _data = {"status": 0}
                TaskService.update(_task.get("id"), data=_data)
                logger.debug(f"task {_task.get('id')} updated {_data}")


def update_box_status(data, status, first):
    update_tasks_to_start_from_pending(data, status, first)
    if data.get("status") != int(round(status, 0)):
        _data = {"status": int(round(status, 0))}
        JobService.update_job(data.get("id"), _data)
        logger.debug(f"job {data.get('id')} updated {_data}")


def recursion(data, first=False):
    if tasks := data.get("tasks"):
        box_status = (
            0
            if sum(item["status"] for item in tasks) / len(tasks) < 0
            else sum(item["status"] for item in tasks) / len(tasks)
        )
        update_box_status(data, box_status, first)
        first = False
    if len(data["jobs"]) > 0:
        for item in data["jobs"]:
            recursion(item, first)


def get_box():
    lines = db_instance().select(collection, " FILTER doc.complete < 100")
    for line in lines:
        if data := PipelineService.get_tree(line["_key"]):
            if data[0]["_id"] == "pipeline/85862992":
                recursion(data[0], first=True)
    logger.info("pipeline manager working")


if __name__ == "__main__":
    load_config()
    every(10, get_box)
    # get_box()
