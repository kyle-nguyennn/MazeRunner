from Map import Map, CellType
from flask import Flask, session, request, flash, jsonify, url_for, redirect, render_template, g, stream_with_context
from werkzeug.datastructures import Headers
from werkzeug.wrappers import Response
import json
from race import getInstructions

app = Flask(__name__)
app.config["SECRET_KEY"] = "nHDG3Zi4HVtyc1fPBcrUEi0oACzUPRkI"


@app.route('/', methods=['GET'])
def index():
    return render_template('main.html')


@app.route('/desc_to_array', methods=['POST'])
def desc_to_array():
    part1 = request.form['part1']
    part2 = request.form['part2']

    map_obj = Map()
    map_obj.fromMDFStrings(part1, part2)
    map_2d = [[-1 for y in range(15)] for x in range(20)]

    for x in range(20):
        for y in range(15):
            map_2d[19-x][y] = map_obj.get(x, y).value

    return json.dumps(map_2d)


@app.route('/array_to_desc', methods=['POST'])
def array_to_desc():
    map_2d = json.loads(request.data)
    map_obj = Map()
    for x in range(20):
        for y in range(15):
            map_obj.set(19-x, y, CellType(map_2d[x][y]))
    return json.dumps({"part1": map_obj.toMDFPart1(), "part2": map_obj.toMDFPart2()})


@app.route('/fastest_path', methods=['POST'])
def fastest_path():
    data = json.loads(request.data)
    map_2d = data[0]
    try:
        waypoint = (int(data[1]), int(data[2]))
    except ValueError:
        return json.dumps({"Bad input": "please enter numerical values"})
    map = Map()
    for x in range(20):
        for y in range(15):
            map.set(19-x, y, CellType(map_2d[x][y]))
    instructions = getInstructions(map, waypoint)
    return json.dumps({"instructions": instructions})


if __name__ == '__main__':
    app.run(debug=True)
