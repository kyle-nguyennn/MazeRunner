from Map import Map, CellType
from flask import Flask, session, request, flash, jsonify, url_for, redirect, render_template, g, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from werkzeug.datastructures import Headers
from werkzeug.wrappers import Response
import json
from race import getInstructions
from socket_server import TCPServer, TCPServerChild, TCPClient
from simulation_server import SimulatorServer
from exploration_example import ExplorationExample
from threading import Thread

app = Flask(__name__)
app.config["SECRET_KEY"] = "nHDG3Zi4HVtyc1fPBcrUEi0oACzUPRkI"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
explore_algo = ExplorationExample()


class MdfStrings(db.Model):
    part1 = db.Column(db.String(100))
    part2 = db.Column(db.String(100), primary_key=True)

    def __init__(self, part1, part2):
        self.part1 = part1
        self.part2 = part2

    def __repr__(self):
        return '<OrgUnit %r>' % self.part1 + " | " + self.part2


@app.route('/', methods=['GET'])
def index():
    return render_template('main.html', mdf_strings=MdfStrings.query.all())


@app.route('/save_arena', methods=['POST'])
def save_arena():
    new_mdf = MdfStrings(request.form['part1'], request.form['part2'])
    db.session.add(new_mdf)
    db.session.commit()
    return "Saved"


@app.route('/array_to_desc', methods=['POST'])
def array_to_desc():
    map_2d = json.loads(request.data)
    map_obj = Map()
    for x in range(20):
        for y in range(15):
            map_obj.set(19-x, y, CellType(map_2d[x][y]))
    return json.dumps({"part1": map_obj.toMDFPart1(), "part2": map_obj.toMDFPart2()})


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


@app.route('/exploration', methods=['GET'])
def exploration():
    thread = Thread(target=startSimulationServer)
    thread.start()
    thread = Thread(target=startExplorationAlgo)
    thread.start()
    return "ok"


@app.route('/get_status', methods=['GET'])
def get_status():
    map_obj = explore_algo.getMap()
    map_2d = [[-1 for y in range(15)] for x in range(20)]
    for x in range(20):
        for y in range(15):
            map_2d[19-x][y] = map_obj.get(x, y).value

    return json.dumps(map_2d)


def startSimulationServer():
    server = TCPServer(('127.0.0.1', 6666), SimulatorServer)
    server.serve_forever()


def startExplorationAlgo():
    explore_algo.run()


if __name__ == '__main__':
    app.run(debug=True)
