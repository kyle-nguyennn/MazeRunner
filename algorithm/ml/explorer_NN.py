import sys, random, time
sys.path.append("..")
from web_main import db, MdfStrings
from arena import Arena, CellType
from keras.models import Sequential
from keras.layers import Dense, Activation
from keras.optimizers import SGD
import numpy as np
from Robot import Robot
from race import detectCollision
import matplotlib.pylab as plt

run_timeout = 0.1 # in seconds ~ 150 instructions in my pc
generations = 100
pool_size = 100
ideal_mean_instructions = 130
current_pool = []
new_model = True
model_path = __file__ + "/../model_pool"

def load_or_init_pool(path=None):
    for i in range(pool_size):
        model = init_model()
        current_pool.append(model)
    if path != None:
        for i in range(pool_size):
            current_pool[i].load_weights(path + "/model_new" + str(i) + ".keras")

def save_pool():
    for i in range(pool_size):
        current_pool[i].save_weights(model_path + "/model_new" + str(i) + ".keras")
    print("Saved current pool!")

def init_model():
    model = Sequential()
    # construct model structure
    model.add(Dense(input_dim=9, units=16))
    model.add(Activation("sigmoid"))
    model.add(Dense(units=4))
    # output of the last layer has 4 values coresponding to 4 actions (F, B, L, R) 
    model.add(Activation("softmax"))
    sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
    model.compile(loss="mse", optimizer=sgd, metrics=["accuracy"])
    return model

def model_crossover(model_idx1, model_idx2):
    # return new weights for the 2 models
    global current_pool
    weights1 = current_pool[model_idx1].get_weights()
    weights2 = current_pool[model_idx2].get_weights()
    weightsnew1 = weights1
    weightsnew2 = weights2
    weightsnew1[0] = weights2[0]
    weightsnew2[0] = weights1[0]
    return np.asarray([weightsnew1, weightsnew2])

def model_mutate(weights):
    # return the mutated weights
    for xi in range(len(weights)):
        for yi in range(len(weights[xi])):
            if random.uniform(0, 1) > 0.85:
                change = random.uniform(-0.5,0.5)
                weights[xi][yi] += change
    return weights

def predict_action(model, input):
    '''
    input: nparray of 9 values that already go through neural_input = np.atleast_2d(neural_input)
    input consists of 6 sensor reading values and the 3-tuple of the current state of the robot
    '''
    global current_pool
    
    output_prob = model.predict(input)
    # output_prob corresponding to 4 actions (F, B, L, R)
    action = {
        0: "F",
        1: "B",
        2: "L",
        3: "R"
    }[np.argmax(output_prob)]
    return action

def getSensorData(arena, robot):
    x,y = robot.getPositionMod4()[:-1]
    sensor_data = [sensor.visible_range for sensor in robot.sensors]
    for sensorIndex in range(len(robot.sensors)):
        sensor = robot.sensors[sensorIndex]
        offsets = robot.visible_offsets(sensor)
        for i in range(len(offsets)):
            offset = offsets[i]
            xx = x + offset[0]
            yy =  y+offset[1]
            if arena.get(xx, yy) == CellType.OBSTACLE or arena.get(xx, yy) == False:
                sensor_data[sensorIndex] = i
                break
    # print("sensor data ", sensor_data)
    return sensor_data

def updateMap(sensor_data, knowledge_map, robot): # update knowledge_map and return points for discover cells
    discovered = 0
    x,y = robot.getPositionMod4()[:-1]
    for sensorIndex in range(len(robot.sensors)):
        sensor = robot.sensors[sensorIndex]
        offsets = robot.visible_offsets(sensor) # note that len of offsets == sensor.visible_range
        for i in range(sensor_data[sensorIndex]):
            # trust in sensor_data that it wont give out-of-bound cell coordinates
            offset = offsets[i]
            xx = x + offset[0]
            yy = y + offset[1]
            if knowledge_map.get(xx, yy) == CellType.UNKNOWN and knowledge_map.set(xx, yy, CellType.EMPTY) == True:
                discovered += 1
        if sensor_data[sensorIndex] < sensor.visible_range:
            offset = offsets[sensor_data[sensorIndex]]
            xx = x + offset[0]
            yy = y + offset[1]
            if knowledge_map.get(xx, yy) == CellType.UNKNOWN and knowledge_map.set(xx, yy, CellType.OBSTACLE) == True:
                discovered += 1
    # give points for discovered cells
    # print("discovered this time ", discovered)
    return discovered

def execute(action, robot, arena):
    if action == "F":
        robot.forward()
    if action == "B":
        robot.backward()
    if action == "L":
        robot.rotateLeft()
    if action == "R":
        robot.rotateRight()
    x,y = robot.getPosition()[:-1]
    if detectCollision(arena.get_2d_arr(), robot.getPosition()[:-1]):
        return (-1,-1,-1)
    return None

def computeFitness(discovered, instruction_count, runtime):
    # instruction_count score follow a Gaussian distribution such that mean = ideal_mean_instructions
    # and 50% lies between (-30, 30) around ideal_mean_instructions
    from math import e, sqrt, pi
    def gaussian(x, m=ideal_mean_instructions, s=43):
        gauss = 1/(sqrt(2*pi)*s)*e**(-0.5*(float(x-m)/s)**2)
        return gauss
    return discovered+gaussian(instruction_count)*10000

def evolve(fitness):
    global current_pool
    new_weights = []
    total_fitness = 0
    for select in range(pool_size):
        total_fitness += fitness[select]
    for select in range(pool_size):
        fitness[select] /= total_fitness
        if select > 0:
            fitness[select] += fitness[select-1]
    for select in range(int(pool_size/2)):
        parent1 = random.uniform(0, 1)
        parent2 = random.uniform(0, 1)
        idx1 = -1
        idx2 = -1
        for idxx in range(pool_size):
            if fitness[idxx] >= parent1:
                idx1 = idxx
                break
        for idxx in range(pool_size):
            if fitness[idxx] >= parent2:
                idx2 = idxx
                break
        new_weights1 = model_crossover(idx1, idx2)
        updated_weights1 = model_mutate(new_weights1[0])
        updated_weights2 = model_mutate(new_weights1[1])
        new_weights.append(updated_weights1)
        new_weights.append(updated_weights2)
    for select in range(len(new_weights)):
        fitness[select] = -100
        current_pool[select].set_weights(new_weights[select])

if __name__ == "__main__":
    maps = db.session.query(MdfStrings).all()
    if new_model:
        load_or_init_pool(None)
        save_pool()
    else:
        load_or_init_pool(model_path)
    # evaluation metrics
    discovered_avg = []
    discovered_max = []
    instruction_avg = []
    instruction_min = []
    ### start training 
    for generation in range(generations):
        fitness = [0 for i in range(pool_size)]
        total_discovered = 0
        max_discovered = 0
        total_instructions = 0
        min_instructions = 1000
        # start evaluating models in current generation
        for modelIndex in range(pool_size):
            model = current_pool[modelIndex]
            mapIndex = random.randrange(0, 5)
            map = maps[mapIndex]
            arena = Arena()
            arena.from_mdf_strings(map.part1, map.part2)
            #arena = arena.get_2d_arr()
            # book record variables for this model run
            knowledge_map = Arena()#.get_2d_arr()
            gameover = False
            discovered = 0
            # head=random.randrange(0,4)
            robot = Robot(head=random.randrange(0,4), h=1, w=1)
            start_time = time.time()
            runtime = 0
            instruction_count = 0
            # start running
            print("start exploring")
            while not gameover:
                sensor_data = getSensorData(arena, robot)
                discovered += updateMap(sensor_data, knowledge_map, robot)
                robot_pos = robot.getPositionMod4()
                input_nn = np.atleast_2d(np.array(sensor_data + robot_pos))
                action = predict_action(model, input_nn)
                instruction_count += 1
                # print("robot pos ", robot_pos)
                # print("action taken ", action)
                result = execute(action, robot, arena)
                # print("robot pos ", robot.getPosition())
                # if no crash happens, robot will be at the supposed position after execute
                if result == (-1,-1,-1):
                    runtime = time.time() - start_time
                    gameover = True
                else: # moved successfully without crashing
                    # check winning condition
                    if discovered == 300 or time.time()-start_time > run_timeout:
                        runtime = time.time() - start_time
                        gameover = True
            else:
                print("generation ", generation, "model ", modelIndex)
                print("discovered: ", discovered)
                print("instruction count:", instruction_count)
                print("runtime: ", runtime)
                total_discovered += discovered
                total_instructions += instruction_count
                if discovered > max_discovered:
                    max_discovered = discovered
                if instruction_count < min_instructions:
                    min_instructions = instruction_count
            # game over for this model
            # update fitness
            fitness[modelIndex] = computeFitness(discovered, instruction_count, runtime)
        # evolving now
        evolve(fitness)
        discovered_max.append(max_discovered)
        instruction_min.append(min_instructions)
        discovered_avg.append(total_discovered/pool_size)
        instruction_avg.append(total_instructions/pool_size)

        # nn_input = np.atleast_2d(np.asarray([3,3,3,3,3,3,3,3,3]))
        # action = predict_action(current_pool[0], nn_input)
        # print(action)
    ### plot evaluation metrics
    plt.plot(range(generations), discovered_max, label="discovered_max")
    plt.plot(range(generations), discovered_avg, label="discovered_avg")
    plt.plot(range(generations), instruction_min, label="instruction_min")
    plt.plot(range(generations), instruction_avg, label="instruction_avg")
    plt.xlabel('Generation')
    plt.legend(loc='upper left')
    plt.show()