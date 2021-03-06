# Test the ALEInterface object.

import signal
import sys
import os
import random
import numpy
from ALEInterface import ALEInterface
import agent
from config import *
import cv2
from FrameImage import FrameImage
from copy import deepcopy
from pybrain.tools.customxml.networkwriter import NetworkWriter
from pybrain.tools.customxml.networkreader import NetworkReader


game = "pong"

# cleanup routine for when exitting the program
def cleanup(signal = None, frame = None):
    if disp_screen:
        fi.close()
    interface.close()
    print "Cleanup done."


# exit nicely if ctrl+c
signal.signal(signal.SIGINT, cleanup)


# read arguments (ROM name, and display options)
if len(sys.argv) > 1:
    game = sys.argv[1]
    disp_screen = False
    video_fname = None
    if len(sys.argv) > 2 and "disp" in sys.argv[2]:
        disp_screen = True
        if len(sys.argv) > 3:
            video_fname = sys.argv[3]
else:
    print "Use: $ python test.py game_name [disp]"
    exit(0)


# compile the c++ code
#os.system("cd ..; make")


#A new agent here
gameAgent = agent.Agent(loadWeightsFromFile, nnFileName)
win_count = 0

for eps in range(NUM_EPISODE):
    interface = ALEInterface(game, disp_screen)
    actions = interface.get_valid_actions()
    if disp_screen:
        width, height = interface.get_screen_dimensions()
        fi = FrameImage(width, height)
    interface.start_new_game()   
   #Initialize s
    state = numpy.zeros(NODE_INPUT)
    raw_state, reward = interface.get_state_and_reward()
    if GAME == PONG:
        is_valid_frame, state = agent.process_state_pong(state, raw_state)
    if reward == None: reward = 0

    #Training steps
    print("Training Episode:", eps)
    while int(reward) == 0:
        if disp_screen:
            pixels = interface.get_pixels()
            fi.display(pixels)
	
#	print("reward: ", reward)
#	print(raw_state)
#	print("current frame valid: ", is_valid_frame)
# 	print("processed state: ", state)
        #agent chooses action according to e-greedy
# 	if is_valid_frame:
        action = gameAgent.eGreedyAct(state) 
#        print("Action values:", pongAgent.nn.activate(state), "action", action + OFFSET)
        #action = pongAgent.reflexAct(state)        
        #action = pongAgent.greedyAct(state)
#	else:
#	    if last_valid_state[PLAYER_Y] > MAX_Y/2.0: action = RIGHT
#	    else: action = LEFT   
# 	    action = random.choice(ACTION_SET)  #should be move to middle
        
	#Pass action to emulator
	interface.do_action(action + OFFSET) 
		
        raw_state, reward = interface.get_state_and_reward()
	if GAME == PONG:
  	    is_valid_frame, state_new = agent.process_state_pong(state, raw_state)
  	
        #update Q values
#	if is_valid_frame:
        gameAgent.updateNN(state, action, reward, state_new)
	
	state = deepcopy(state_new)
	
	if reward == 1.0: 
	    win_count += 1
	    print("You win one game!")	
    interface.close()

NetworkWriter.writeToFile(gameAgent.nn, nnFileName)
print("Total win count: ", win_count)
if disp_screen:
    fi.close()
#        if not interface.game_running:
#            break
 
cleanup()

