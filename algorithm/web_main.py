from arena import Arena, CellType
from flask import Flask, session, request, flash, jsonify, url_for, redirect, render_template, g, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from werkzeug.datastructures import Headers
from werkzeug.wrappers import Response
import json
from race import getInstructions
from simulation_server import SimulatorServer
from exploration_example import ExplorationExample
from tcp_client import TcpClient
from threading import Thread
from enum import Enum
from exploration import Explorer
app = Flask(__name__)
app.config["SECRET_KEY"] = "nHDG3Zi4HVtyc1fPBcrUEi0oACzUPRkI"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
global explore_algo
explore_algo = ExplorationExample(None)


class Mode(Enum):
    NONE = 0
    SIM_SERVER = 1
    PI_CONNECTION = 2


class MdfStrings(db.Model):
    part1 = db.Column(db.String(100))
    part2 = db.Column(db.String(100), primary_key=True)

    def __init__(self, part1, part2):
        self.part1 = part1
        self.part2 = part2

    def __repr__(self):
        return '<OrgUnit %r>' % self.part1 + " | " + self.part2


mode = Mode.NONE


@app.route('/', methods=['GET'])
def index():
    return render_template('main.html', mdf_strings=MdfStrings.query.all())


@app.route('/save_arena', methods=['POST'])
def save_arena():
    new_mdf = MdfStrings(request.form['part1'], request.form['part2'])
    db.session.add(new_mdf)
    db.session.commit()
    return "Saved."


@app.route('/array_to_mdf', methods=['POST'])
def array_to_mdf():
    arena_2d = json.loads(request.data)
    arena_obj = array_to_arena(arena_2d)
    return json.dumps({"part1": arena_obj.to_mdf_part1(), "part2": arena_obj.to_mdf_part2()})


@app.route('/mdf_to_array', methods=['POST'])
def mdf_to_array():
    part1 = request.form['part1']
    part2 = request.form['part2']

    arena_obj = Arena()
    arena_obj.from_mdf_strings(part1, part2)
    arena_2d = arena_to_array(arena_obj)

    return json.dumps(arena_2d)


@app.route('/fastest_path_sim', methods=['POST'])
def fastest_path():
    data = json.loads(request.data)
    arena_2d = data[0]
    try:
        waypoint = (int(data[1]), int(data[2]))
    except ValueError:
        return json.dumps({"Bad input": "please enter numerical values"})
    instructions = getInstructions(array_to_arena(arena_2d), waypoint)
    return json.dumps({"instructions": instructions})


@app.route('/exploration_sim', methods=['POST'])
def exploration():
    data = json.loads(request.data)
    arena_2d = data[0]
    robot_pos = [int(data[1]), int(data[2]), int(data[3])]
    speed = float(data[4])
    arena_obj = array_to_arena(arena_2d)
    sim_server_thread = Thread(target=start_simulation_server,
                               args=[arena_obj, robot_pos, speed])
    sim_server_thread.start()
    tcp_client_thread = Thread(
        target=connect_tcp_client, args=["127.0.0.1", 77])
    tcp_client_thread.start()
    global mode
    mode = Mode.SIM_SERVER
    return "Simulation server started."


@app.route('/connect_to_pi', methods=['GET'])
def connect_to_pi():
    tcp_client_thread = Thread(
        target=connect_tcp_client, args=["192.168.7.1", 77])
    tcp_client_thread.start()
    global mode
    mode = Mode.PI_CONNECTION
    return "OK"


@app.route('/disconnect_from_pi', methods=['GET'])
def disconnect_from_pi():
    global tcp_conn
    tcp_conn.close_conn()
    global mode
    mode = Mode.NONE
    return "OK"


@app.route('/current_mode', methods=['GET'])
def current_mode():
    global mode
    return str(mode.value)


@app.route('/get_explore_status', methods=['GET'])
def get_explore_status():
    global explore_algo
    if explore_algo.get_arena() == None:
        print("Exploration not running.")
        return "N"
    arena_2d = arena_to_array(explore_algo.get_arena())
    result = [arena_2d, explore_algo.get_robot()]
    return json.dumps(result)


def arena_to_array(arena):
    arena_2d = [[-1 for y in range(15)] for x in range(20)]
    for x in range(20):
        for y in range(15):
            arena_2d[19-x][y] = arena.get(x, y).value
    return arena_2d


def array_to_arena(arena_2d):
    arena_obj = Arena()
    for x in range(20):
        for y in range(15):
            arena_obj.set(19-x, y, CellType(arena_2d[x][y]))
    return arena_obj


def start_simulation_server(arena_obj, robot_pos, speed):
    global mode
    server = SimulatorServer("127.0.0.1", 77, arena_obj, robot_pos, speed)
    server.run()
    mode = Mode.NONE


def start_exploration_algo(robot_pos):
    global tcp_conn
    global explore_algo
    explore_algo = Explorer(tcp_conn, robot_pos)
    explore_algo.run()


def connect_tcp_client(ip, port):
    global tcp_conn
    global mode
    tcp_conn = TcpClient(ip, port)
    tcp_conn.run()
    try:
        while True:
            data = tcp_conn.get_json()
            if data is None:
                break
            handle_request(data)
    except:
        mode = Mode.NONE
    mode = Mode.NONE


def handle_request(data):
    global tcp_conn
    request = json.loads(data)
    if request["command"] == "beginExplore":
        explore_thread = Thread(target=start_exploration_algo, args=[
                                request["robotPos"]])
        explore_thread.start()
    elif request["command"] == "beginFastest":
        tcp_conn.send_command(getInstructions(None, None))


if __name__ == '__main__':
    app.run(debug=True)
