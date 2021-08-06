from spex_common.config import load_config
from spex_common.modules.database import db_instance
import os.path
import requests
import os
from services.Timer import every
from services.Task import task


collection = 'pipeline'


def update_box_status(data, status, session, project):
    if data.get('status') != int(round(status, 0)):
        resp = session.put(url=f'{base_url}pipeline/update/{project}/{data.get("id")}', json={'complete': int(round(status, 0))})
        if resp.status_code != 200:
            print(f'error on update: {data}')


def recursion(data, session, project):
    if tasks := data.get('tasks'):
        box_status = 0 if sum(item['status'] for item in tasks) / len(tasks) < 0 else sum(item['status'] for item in tasks) / len(tasks)
        update_box_status(data, box_status, session, project)
    if len(data['boxes']) > 0:
        for item in data['boxes']:
            recursion(item, session, project)


def get_box():
    lines = db_instance().select(collection, ' FILTER doc.complete < 100  LIMIT 1 ')
    ses = requests.session()
    resp = ses.post(url=f'{base_url}users/login', json={"username": os.getenv('BACKEND_LOGIN'), 'password': os.getenv('BACKEND_PASSWORD')})
    if resp.status_code == 200:
        ses.headers = {'Authorization': f'Bearer {resp.headers.get("authorization")}'}
        for line in lines:
            line_resp = ses.get(url=f'{base_url}pipeline/path/{ line["project"] }/{ line["_key"] }')
            if line_resp.status_code == 200:
                data = line_resp.json()
                if data["success"] is True:
                    recursion(data["data"]["pipelines"][0], session=ses, project=line["project"])
    print(resp, lines)


if __name__ == '__main__':
    load_config()
    base_url = os.getenv("BACKEND_URL")
    get_box()
    # insert_task_result()
    # every(1, get_sub_tasks)
    # get_sub_tasks()
