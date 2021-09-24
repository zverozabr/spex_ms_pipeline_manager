from spex_common.config import load_config
from spex_common.modules.database import db_instance
import spex_common.services.Pipeline as PipelineService
import spex_common.services.Job as JobService
import spex_common.services.Task as TaskService
from services.Timer import every


collection = 'pipeline'


def update_tasks_to_start_from_pending(data, status):
    if status < 100:
        for box in data['jobs']:
            for _task in box['tasks']:
                if _task['status'] < 100 and _task['status'] != -1:
                    TaskService.update(_task.get("id"), data={'status': -1})
    if status == 100:
        for box in data['jobs']:
            for _task in box['tasks']:
                if _task['status'] in [-1]:
                    TaskService.update(_task.get("id"), data={'status': 0})


def update_box_status(data, status):
    update_tasks_to_start_from_pending(data, status)
    if data.get('status') != int(round(status, 0)):
        JobService.update_job(data.get('id'), {'status': int(round(status, 0))})


def recursion(data):
    if tasks := data.get('tasks'):
        box_status = 0 if sum(item['status'] for item in tasks) / len(tasks) < 0 else sum(item['status'] for item in tasks) / len(tasks)
        update_box_status(data, box_status)
    if len(data['jobs']) > 0:
        for item in data['jobs']:
            recursion(item)


def get_box():
    lines = db_instance().select(collection, ' FILTER doc.complete < 100')
    for line in lines:
        if data := PipelineService.get_tree(line["_key"]):
            recursion(data[0])
    print("pipeline manager working")


if __name__ == '__main__':
    load_config()
    every(10, get_box)


