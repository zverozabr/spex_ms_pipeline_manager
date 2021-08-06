import re
from os import getenv
import os
# from datetime import datetime, timedelta
import pathlib
import csv
from random import randint
import shutil
from PIL import Image
import numpy as np
excluded_headers = [
    'content-encoding',
    'content-length',
    'transfer-encoding',
    'connection',
    'Authorization'
]


def getFilename_fromCd(cd):

    if not cd:
        return None
    fname = re.findall('filename=(.+)', cd)
    if len(fname) == 0:
        return None

    return fname[0]


def getAbsoluteRelative(path, absolute=True):
    if absolute:
        return path.replace('%DATA_STORAGE%', getenv('DATA_STORAGE'))
    else:
        return path.replace(getenv('DATA_STORAGE'), '%DATA_STORAGE%')


def download_file(path, method='get', client=None, jobid='', taskid=''):

    if client is None:
        return None
    dir = getenv('DATA_STORAGE') + '//' + str(jobid) + '//' + str(taskid) + '//'
    relative_dir = '%DATA_STORAGE%' + '//' + str(jobid) + '//' + str(taskid) + '//'
    with client.get(path, stream=True) as r:
        filename = getFilename_fromCd(r.headers.get('content-disposition'))
        if r.ok is False:
            return None

        r.raise_for_status()
        if filename is None:
            return None
        pathlib.Path(dir).mkdir(parents=True, exist_ok=True)
        with open(dir+filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                # if chunk:
                f.write(chunk)

    return relative_dir+filename


def getCsvAsList(path):

    with open(path, newline='') as csvfile:
        data = list(csv.reader(csvfile))
    return data


def getPoolInt():
    return randint(int(getenv('POOL_START')), int(getenv('POOL_STOP')))


def rmDir(path):
    shutil.rmtree(os.path.dirname(path))


def rmFiles(file):
    for filename in os.listdir(os.path.dirname(file)):
        if filename not in file:
            full_file_path = os.path.join(os.path.dirname(file), filename)
            os.remove(full_file_path)


# rmFiles('c:\\\\temp\\\\DATA_STORAGE/15726402/2//collected.png')


def changeColor(old_color=(68, 1, 84), new_color=(0, 0, 0, 0), image_file=''):

    im = Image.open(image_file).convert('RGBA')
    RGBA = np.array(im)
    marked = (RGBA[:, :, 0:3] == [old_color]).all(2)
    RGBA[marked] = new_color
    im = Image.fromarray(RGBA)
    im.save(image_file)
    im.close()
