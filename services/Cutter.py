# https://pypi.org/project/aicsimageio/
from aicsimageio import AICSImage
from tifffile import TiffFile, TiffWriter
from PIL import Image
import os
import json
from services.Utils import getAbsoluteRelative
import csv


def getImageMetadata(path, dimY=100, dimX=100, debug=False, margin=10):
    path = getAbsoluteRelative(path, absolute=True)
    if margin > 100:
        print('Input max 100 percent')
        return None
    try:
        img = AICSImage(path)
    except FileNotFoundError:
        print('File not found')
        return None

    x = img.size_x
    y = img.size_y

    currentY = 0
    currentX = 0
    region_arr = []

    celX = round(x / dimX, 0)
    celY = round(y / dimY, 0)
    stepX = round(x / celX, 0)
    stepY = round(y / celY, 0)
    curentCount = 0
    marginX = round((dimX / 100) * margin, 0)
    marginY = round((dimY / 100) * margin, 0)

    while currentY != y:
        while currentX != x:
            objStart = {"start": {"x": int(currentX), "y": int(currentY)}}
            currentX += stepX
            if currentX + stepX > x:
                currentX = x
            if currentY + stepY*2 > y:
                celYInsideWhile = y
            else:
                celYInsideWhile = currentY + stepY

            objStop = {"stop": {"x": int(currentX), "y": int(celYInsideWhile)}}
            region_arr.append({"count"+str(curentCount): {**objStart, **objStop}})
            curentCount += 1
            lastX = currentX
        currentY += stepY
        if currentY + stepY > y:
            currentY = y
        lastY = currentY
        currentX = 0

    img.close()
    data = dict()
    path = getAbsoluteRelative(path, absolute=False)

    data['parentData'] = {
        'path': path,
        'filename': os.path.basename(path),
        'folder': os.path.dirname(path),
        'resolution': {'x': lastX, 'y': lastY}
    }
    data['region_arr'] = region_arr
    data['margin'] = True if margin > 0 else False
    if debug:
        print(region_arr, len(region_arr), lastX, lastY)
        print(f'img.dims: {img.dims}')
        print(f'img.shape: {img.shape}')
        print('img.channel_names:', img.get_channel_names())
        print('data: ', data)

    for region in data['region_arr']:
        fName = (list(region.keys())[0])
        boxC = region[fName]

        start = boxC['start']
        if start['x'] != 0 and start['x'] - marginX > 0:
            mStartX = start['x'] - marginX
            mStartXRes = marginX
        else:
            mStartX = 0
            mStartXRes = 0
        if start['y'] != 0 and start['y'] - marginY > 0:
            mStartY = start['y'] - marginY
            mStartYRes = marginY
        else:
            mStartY = 0
            mStartYRes = 0

        stop = boxC['stop']
        if stop['x'] != x and stop['x'] + marginX < x:
            mStopX = stop['x'] + marginX
            mStopXRes = -marginX
        else:
            mStopX = x
            mStopXRes = 0
        if stop['y'] != y and stop['y'] + marginY < y:
            mStopY = stop['y'] + marginY
            mStopYRes = -marginY
        else:
            mStopY = y
            mStopYRes = 0
        boxC.update({'mstart': {'x': mStartX, 'y': mStartY}, 'mstop': {'x': mStopX, 'y': mStopY}})
        boxC.update({'marginsStart': {'x': mStartXRes, 'y': mStartYRes}, 'marginsStop': {'x': mStopXRes, 'y': mStopYRes}})
        if debug:
            print(boxC)

    return data


def splitImage(data):
    if data is None:
        return
    margin = data['margin']

    folder = data['parentData']['folder']
    folder = getAbsoluteRelative(folder, absolute=True)

    for region in data['region_arr']:
        fName = (list(region.keys())[0])
        boxC = region[fName]
        if margin:
            box = (boxC['mstart']['y'], boxC['mstop']['y'], boxC['mstart']['x'], boxC['mstop']['x'])
        else:
            box = (boxC['start']['y'], boxC['stop']['y'], boxC['start']['x'], boxC['stop']['x'])
        path = f'{folder}//{fName}.tif'
        cropTiff(source=data['parentData']['path'], box=box, saveto=path)
        region.update({'path': getAbsoluteRelative(path, absolute=False)})


def collectImageCsv(**kwargs):
    extraPath = kwargs.get('extraPath')
    if not extraPath:
        extraPath = ''
    if kwargs.get('data') is None:
        return None
    folder = kwargs['folder']
    pathToSave = f'{folder}//collected.png'
    margin = kwargs.get('margin')

    region = kwargs.get('data')
    fName = list(kwargs.get('data').keys())[0]
    boxC = region[fName]
    imToPaste = Image.open(f'{folder}//{fName}.tif{extraPath}.png')
    (x, y) = imToPaste.size

    y = imToPaste.height
    x = imToPaste.width
    if margin:
        box_cropped = (0 + boxC['marginsStart']['x'], 0 + boxC['marginsStart']['y'], x + boxC['marginsStop']['x'], y + boxC['marginsStop']['y'])
        cropped_image = imToPaste.crop(box_cropped)
    else:
        box_cropped = None
        cropped_image = imToPaste
    box = (boxC['start']['x'], boxC['start']['y'])
    if os.path.isfile(pathToSave):
        collected = Image.open(pathToSave)
    else:
        collected = Image.new(size=(kwargs['res'][0], kwargs['res'][1]), mode='RGB')

    collected.paste(cropped_image, box)
    collected.save(f'{folder}//collected.png')
    collected.close()
    kwargs.update(box_cropped=box_cropped)
    collectCsv(kwargs)
    return True


def tiles(data, tileshape):
    for y in range(0, data.shape[0], tileshape[0]):
        for x in range(0, data.shape[1], tileshape[1]):
            yield data[y: y + tileshape[0], x: x + tileshape[1]]


def cropTiff(source='', box=None, saveto=''):
    source = getAbsoluteRelative(source, absolute=True)
    data = TiffFile(source)
    with TiffWriter(saveto) as tif:
        for page in data.pages:
            image = page.asarray()
            # options = dict(page)
            tif.write(image[int(box[0]):int(box[1]), int(box[2]):int(box[3])])  # , **options
    return tif


def cutForSegmenation(path='', task=None):
    path = getAbsoluteRelative(path, absolute=True)

    boxC = {}
    try:
        boxC = json.loads(task.get('content'))
    except TypeError:
        return None
    box = (boxC['start']['y'], boxC['stop']['y'], boxC['start']['x'], boxC['stop']['x'])

    folder = os.path.dirname(path)
    resultFile = folder + '//to_segment' + os.path.splitext(path)[1]

    cropTiff(path, box, resultFile)

    boxC.update({'path': getAbsoluteRelative(resultFile, absolute=False)})

    task.update({'content': boxC})

    return True


def collectCsv(kwargs):
    debug = False
    extraPath = kwargs.get('extraPath')
    if not extraPath:
        extraPath = ''
    if kwargs.get('data') is None:
        return None
    folder = kwargs['folder']
    lines = []
    box_cropped = kwargs.get('box_cropped')

    fName = list(kwargs.get('data').keys())[0]
    fileName = f'{folder}//{fName}.csv'
    isFile = False
    if os.path.isfile(fileName):
        isFile = True
    if debug:
        print(f'{folder}//{fName}.csv')
    with open(f'{folder}//{fName}.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                if not isFile:
                    lines.append(row)
                if debug:
                    print(f'Column names are {", ".join(row)}')
                line_count += 1
            else:
                lines.append(row)
                y = int(round(float(row[1]), 0))
                x = int(round(float(row[2]), 0))
                if box_cropped is not None:
                    if x > box_cropped[0] and x < box_cropped[2] and y > box_cropped[1] and y < box_cropped[3]:
                        if debug:
                            print('in sector', (x, y), box_cropped)
                    else:
                        if debug:
                            print('need delete', (x, y), box_cropped)
                        lines.remove(row)
    with open(f'{folder}//collected.csv', 'a') as writeFile:
        writer = csv.writer(writeFile, lineterminator='\n')
        writer.writerows(lines)


def getArrayFromCsv(path, **kwargs):
    debug = False
    extraPath = kwargs.get('extraPath')
    if not extraPath:
        extraPath = ''
    if kwargs.get('data') is None:
        return None
    folder = kwargs['folder']
    lines = []

    fName = list(kwargs.get('data').keys())[0]
    fileName = f'{folder}//{fName}.csv'
    isFile = False
    if os.path.isfile(fileName):
        isFile = True
    if debug:
        print(f'{folder}//{fName}.csv')
    with open(f'{folder}//{fName}.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                if not isFile:
                    lines.append(row)
                if debug:
                    print(f'Column names are {", ".join(row)}')
                line_count += 1
            else:
                lines.append(row)
