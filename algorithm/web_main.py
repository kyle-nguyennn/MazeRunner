from Map import Map
from flask import Flask, session, request, flash, jsonify, url_for, redirect, render_template, g, stream_with_context
from werkzeug.datastructures import Headers
from werkzeug.wrappers import Response
import json

app = Flask(__name__)
app.config["SECRET_KEY"] = "nHDG3Zi4HVtyc1fPBcrUEi0oACzUPRkI"


@app.route('/', methods=['GET'])
def index():
    map = Map("BCF", 3, 4)
    return render_template('main.html')


@app.route('/desc_to_array', methods=['POST'])
def desc_to_array():
    part1 = request.form['part1']
    part2 = request.form['part2']

    map_obj = Map(part1, part2)
    map_2d = [[0 for y in range(15)] for x in range(20)]

    for x in range(20):
        for y in range(15):
            map_2d[19-x][y] = map_obj.get(x, y)
    return json.dumps(map_2d)


@app.route('/array_to_desc', methods=['POST'])
def array_to_desc():
    map_2d = json.loads(request.data)
    map_obj = Map(0)
    for x in range(20):
        for y in range(15):
            if map_2d[x][y] == 1:
                map_obj.set(19-x, y)
    return map_obj.toHexString()


if __name__ == '__main__':
    app.run(debug=True)
