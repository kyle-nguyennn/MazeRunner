import sys, argparse
from Commander import CommanderComposite
from RobotController import RobotController
from Simulator import Simulator, PCSimulator, AndroidSimulator

def explore(cmd, args):
    print("Start exploring ...")

def race(cmd):
    print("Get ...")
    # TODO: Load map

    print ("Set ...")
    # TODO: compute fastest path

    print("Go ...")
    # TODO: give instructions

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Auto pilot process.')
    parser.add_argument('mode', help='Mode: explore or fastestpath')
    parser.add_argument('--speed', '-s', default=1, type=float,
                    help='Speed (steps per second)')
    parser.add_argument('--maxExplore', '-m', default=1.0, type=float,
                    help='Percentage of map coverage to terminate (from 0 to 1)')
    parser.add_argument('--timelimit', '-t', default=360, type=int,
                    help='Time limit (in seconds)')
    args = vars(parser.parse_args()) # vars convert Namespace object to dict
    print(args)
    commander = CommanderComposite()
    commander.add(RobotController())
    commander.add(AndroidSimulator())
    commander.add(PCSimulator())
    if args['mode'] == 'explore':
        explore(commander, args)
    elif args['mode'] == 'fastestpath':
        race(commander)
