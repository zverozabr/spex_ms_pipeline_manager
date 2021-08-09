from spex_common.config import load_config
from spex_common.modules.database import db_instance
import os.path
import requests
import os
from services.Timer import every
from services.Task import task

collection = 'pipeline'


def update_tasks_to_start_from_pending(data, status, _session):
    if status < 100:
        for box in data['boxes']:
            for _task in box['tasks']:
                if _task['status'] < 100 and _task['status'] != -1:
                    resp = _session.put(url=f'{base_url}tasks/{_task.get("id")}', json={'status': -1})
                    if resp.status_code != 200:
                        print(f'error on update task: {task}')
    if status == 100:
        for box in data['boxes']:
            for _task in box['tasks']:
                if _task['status'] in [-1]:
                    resp = _session.put(url=f'{base_url}tasks/{_task.get("id")}', json={'status': 0})
                    if resp.status_code != 200:
                        print(f'error on update task: {task}')


def update_box_status(data, status, _session, project):
    update_tasks_to_start_from_pending(data, status, _session)
    if data.get('status') != int(round(status, 0)):
        resp = _session.put(url=f'{base_url}pipeline/update/{project}/{data.get("id")}', json={'complete': int(round(status, 0))})
        if resp.status_code != 200:
            print(f'error on update: {data}')


def recursion(data, _session, project):
    if tasks := data.get('tasks'):
        box_status = 0 if sum(item['status'] for item in tasks) / len(tasks) < 0 else sum(item['status'] for item in tasks) / len(tasks)
        update_box_status(data, box_status, _session, project)
    if len(data['boxes']) > 0:
        for item in data['boxes']:
            recursion(item, _session, project)


def get_box():
    lines = db_instance().select(collection, ' FILTER doc.complete < 100')
    ses = requests.session()
    resp = ses.post(url=f'{base_url}users/login', json={"username": os.getenv('BACKEND_LOGIN'), 'password': os.getenv('BACKEND_PASSWORD')})
    if resp.status_code == 200:
        ses.headers = {'Authorization': f'Bearer {resp.headers.get("authorization")}'}
        for line in lines:
            line_resp = ses.get(url=f'{base_url}pipeline/path/{ line["project"] }/{ line["_key"] }')
            if line_resp.status_code == 200:
                data = line_resp.json()
                if data["success"] is True:
                    recursion(data["data"]["pipelines"][0], _session=ses, project=line["project"])
    print(resp, lines)


if __name__ == '__main__':
    load_config()
    base_url = os.getenv("BACKEND_URL")

    every(10, get_box)
