import sys, random, time, copy
sys.path.append("..")
from web_main import db, MdfStrings
from arena import Arena, CellType
import keras
from keras.models import Sequential
from keras.layers import Dense, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras.layers import Dense, Activation
from keras.optimizers import SGD
import numpy as np
from Robot import Robot
from race import detectCollision
import matplotlib.pylab as plt

map_shape= (20,15,1)
run_timeout = 1 # 0.12 in seconds ~ 150 instructions in my pc
pool_size = 100
ideal_mean_instructions = 130
new_model = True

def init_model(type="cnn"):
    model = None
    if type=="mlp":
        model = Sequential()
        # construct model structure
        model.add(Dense(input_dim=9, units=16))
        model.add(Activation("sigmoid"))
        model.add(Dense(units=4))
        # output of the last layer has 4 values coresponding to 4 actions (F, B, L, R) 
        model.add(Activation("softmax"))
        sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
        model.compile(loss="mse", optimizer=sgd, metrics=["accuracy"])
    elif type=="cnn":
        model = Sequential()
        model.add(Conv2D(32, kernel_size=(3, 3), strides=(1, 1), activation='relu', input_shape=map_shape))
        model.add(MaxPooling2D(pool_size=(2, 2), strides=(2, 2)))
        model.add(Conv2D(64, (3, 3), activation='relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Flatten())
        # model.add(Dense(25, activation='relu'))
        # model.add(Dense(4, activation='softmax'))
        model.add(Dense(4))
        model.compile(SGD(lr=.1), "mse")
    return model

def predict_action(model, input):
    '''
    input: nparray of 9 values that already go through neural_input = np.atleast_2d(neural_input)
    input consists of 6 sensor reading values and the 3-tuple of the current state of the robot
    '''
    global current_pool
    
    output = model.predict(input)
    # output_prob corresponding to 4 actions (F, B, L, R)
    action = {
        0: "F",
        1: "B",
        2: "L",
        3: "R"
    }[np.argmax(output)]

    # for 2 actions models
    # action = {
    #     0: "F",
    #     1: "R"
    #}[np.argmax(output_prob)]
    return output, action

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
            # only give credits for previously unknown cells
            if knowledge_map.get(xx, yy) == CellType.UNKNOWN and knowledge_map.set(xx, yy, CellType.OBSTACLE) == True:
                discovered += 1
    # give points for discovered cells
    # print("discovered this time ", discovered)
    return discovered

def execute(action, robot, arena, knowledge_map, start_time):
    '''
    return:
        new_state: 2d array
        discovered: int
        gameover: boolean
    '''
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
        # does not matter much what to return as when gameover == True, new_state wont be used
        return (
            np.zeros(np.asarray(knowledge_map.get_2d_arr()).shape),
            0,
            True
            )
    else:
        sensor_data = getSensorData(arena, robot)
        discovered = updateMap(sensor_data, knowledge_map, robot)
        new_state = get_nn_input(knowledge_map, robot)
        gameover = False
        if knowledge_map.isComplete() or time.time()-start_time > run_timeout:
            gameover = True
        return (new_state, discovered, gameover)

def normalizwWithSensorData(robot_pos):
    x,y,d = robot_pos
    ratio = 20/8
    return [x/ratio, y/ratio, d]

def blendMap(knowledge_map, robot):
    '''
    return
        m: np array
    '''
    map_color = {
        CellType.EMPTY: 0,
        CellType.UNKNOWN: 63,
        CellType.OBSTACLE: 127
    }
    bodycells = robot.returnBodyCells()
    m = [[-1 for i in range(15)] for j in range(20)]
    for i in range(len(m)):
        for j in range(len(m[0])):
            m[i][j] = map_color[knowledge_map.get(i,j)]
    for x,y in bodycells:
        m[x][y] = 191
        if list((x,y)) == robot.getNoseCell():
            m[x][y] = 255
    # convert to np array
    m = np.array(m)
    return m

def get_nn_input(knowledge_map, robot): # knowledge_map is an Arena object
    input_nn = blendMap(knowledge_map, robot)
    input_nn = input_nn.reshape(1, map_shape[0], map_shape[1], map_shape[2])
    return copy.deepcopy(input_nn)

class ExperienceReplay(object):
    """
    During gameplay all the experiences < s, a, r, s’ > are stored in a replay memory. 
    In training, batches of randomly drawn experiences are used to generate the input and target for training.
    """
    def __init__(self, max_memory=100, discount=.9):
        """
        Setup
        max_memory: the maximum number of experiences we want to store
        memory: a list of experiences
        discount: the discount factor for future experience
        
        In the memory the information whether the game ended at the state is stored seperately in a nested array
        [...
        [experience, game_over]
        [experience, game_over]
        ...]
        """
        self.max_memory = max_memory
        self.memory = list()
        self.discount = discount

    def remember(self, states, game_over):
        #Save a state to memory
        self.memory.append([states, game_over])
        #We don't want to store infinite memories, so if we have too many, we just delete the oldest one
        if len(self.memory) > self.max_memory:
            del self.memory[0]

    def get_batch(self, model, batch_size=10):
        
        #How many experiences do we have?
        len_memory = len(self.memory)
        
        #Calculate the number of actions that can possibly be taken in the game
        num_actions = model.output_shape[-1]
        
        #Dimensions of the game field
        env_dim = self.memory[0][0][0].shape
        #We want to return an input and target vector with inputs from an observed state...
        inputs = np.zeros([min(len_memory, batch_size)] + list(env_dim)[1:])
        #...and the target r + gamma * max Q(s’,a’)
        #Note that our target is a matrix, with possible fields not only for the action taken but also
        #for the other possible actions. The actions not take the same value as the prediction to not affect them
        targets = np.zeros((inputs.shape[0], num_actions))
        
        #We draw states to learn from randomly
        for i, idx in enumerate(np.random.randint(0, len_memory,
                                                  size=inputs.shape[0])):
            """
            Here we load one transition <s, a, r, s’> from memory
            state_t: initial state s
            action_t: action taken a
            reward_t: reward earned r
            state_tp1: the state that followed s’
            """
            state_t, action_t, reward_t, state_tp1 = self.memory[idx][0] # get states
            
            #We also need to know whether the game ended at this state
            game_over = self.memory[idx][1]

            #add the state s to the input
            inputs[i:i+1] = state_t
            
            # First we fill the target values with the predictions of the model.
            # They will not be affected by training (since the training loss for them is 0)
            targets[i] = model.predict(state_t)[0]
            
            """
            If the game ended, the expected reward Q(s,a) should be the final reward r.
            Otherwise the target value is r + gamma * max Q(s’,a’)
            """
            
            #if the game ended, the reward is the final reward
            if game_over:  # if game_over is True
                targets[i, action_t] = reward_t
            else:
                #  Here Q_sa is max_a'Q(s', a')
                Q_sa = np.max(model.predict(state_tp1)[0])
                # r + gamma * max Q(s’,a’)
                targets[i, action_t] = reward_t + self.discount * Q_sa
        return inputs, targets

if __name__ == "__main__":
    model = init_model()
    # parameters
    epsilon = .1  # exploration
    num_actions = 4  # (F, B, L, R)
    max_memory = 500 # Maximum number of experiences we are storing
    batch_size = 1 # Number of experiences we use for training per batch
    epochs = 10000
    # Initialize experience replay object
    exp_replay = ExperienceReplay(max_memory=max_memory)
    #######
    # evaluation metrics
    discovered_avg = []
    discovered_max = []
    instruction_avg = []
    instruction_min = []
    # mapIndex = random.randrange(0, 5)
    #only train on 1 map first
    maps = db.session.query(MdfStrings).all()
    map = maps[0]
    arena = Arena()
    arena.from_mdf_strings(map.part1, map.part2)
    for e in range(epochs):
        loss = 0.
        # book record variables for this model run
        knowledge_map = Arena()#.get_2d_arr()
        gameover = False
        discovered = 0
        total_discovered = 0
        max_discovered = 0
        total_instructions = 0
        min_instructions = 1000
        # head=random.randrange(0,4)
        robot = Robot(head=random.randrange(0,2), h=1, w=1)
        start_time = time.time()
        runtime = 0
        instruction_count = 0
        # start running
        print("start exploring")
        new_state = get_nn_input(knowledge_map, robot)
        while not gameover:
            # sensor_data = getSensorData(arena, robot)
            # discovered += updateMap(sensor_data, knowledge_map, robot)
            # robot_pos = normalizwWithSensorData(robot.getPositionMod4())
            # input_nn = np.atleast_2d(np.array(sensor_data + robot_pos))
            old_state = new_state
            EQ, action = predict_action(model, old_state)
            instruction_count += 1
            # print("robot pos ", robot_pos)
            # print("action taken ", action)
            new_state, rewards, gameover = execute(action, robot, arena, knowledge_map, start_time)
            # print("robot pos ", robot.getPosition())
            # if no crash happens, robot will be at the supposed position after execute
            if gameover:
                runtime = time.time() - start_time
            discovered += rewards
            """
            The experiences < s, a, r, s’ > we make during gameplay are our training data.
            Here we first save the last experience, and then load a batch of experiences to train our model
            """
            # store experience
            exp_replay.remember([old_state, np.argmax(EQ), discovered, new_state], gameover)    
            # Load batch of experiences
            inputs, targets = exp_replay.get_batch(model, batch_size=batch_size)
            # train model on experiences
            batch_loss = model.train_on_batch(inputs, targets)
            # print(batch_loss)
            # print(model.metrics_names)
            loss += batch_loss
        #### game over
        print("Epoch {:03d}/{:03d} | Loss {:.4f} | Discovered {}".format(e,epochs, loss, discovered))
        # print("instruction count:", instruction_count)
        # print("runtime: ", runtime)
        total_discovered += discovered
        total_instructions += instruction_count
        if discovered > max_discovered:
            max_discovered = discovered
        if instruction_count < min_instructions:
            min_instructions = instruction_count
        # game over for this model
        # update metrics
        discovered_max.append(max_discovered)
        instruction_min.append(min_instructions)
        discovered_avg.append(total_discovered/pool_size)
        instruction_avg.append(total_instructions/pool_size)
    ### save model
    model.save("DQN")
    ### plot evaluation metrics
    plt.plot(range(epochs), discovered_max, label="discovered_max")
    plt.plot(range(epochs), discovered_avg, label="discovered_avg")
    plt.plot(range(epochs), instruction_min, label="instruction_min")
    plt.plot(range(epochs), instruction_avg, label="instruction_avg")
    plt.xlabel('Epochs')
    plt.legend(loc='upper left')
    plt.show()