from spex_common.config import load_config
from spex_common.modules.logging import get_logger
from spex_common.modules.database import db_instance
from spex_common.services.Timer import every
import spex_common.services.Pipeline as PipelineService
import spex_common.services.Job as JobService
from spex_common.models.Status import PipelineStatus
import logging

logger = get_logger("pipeline_manager")
collection = "pipeline"


def update_box_status(data, status):
    if data.get("status") == status:
        return

    job_id = data.get("id")
    data = {"status": status}
    logger.debug(f"job {job_id} updating {data}")
    JobService.update_job(job_id, data)


def recursion(data, _status: int = None):
    if data is None:
        return

    tasks = data.get("tasks")
    if tasks is not None and len(tasks) > 0:
        status = min(item.get("status") for item in tasks if item.get("status") is not None)
        update_box_status(data, status)

    if len(data.get("jobs", [])) < 1:
        return

    for item in data.get("jobs", []):
        recursion(item, _status=_status)


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

            recursion(data[0], _status=status)

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
