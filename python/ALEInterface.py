# Python interface with the ALE C++ simulator code.

import subprocess
import Protocol
from ALEObject import ALEObject
from State import State

EXEC = "../proj"


class ALEInterface():
    """Provides an interface to the C++ code through IPC."""
    
    def __init__(self, rom):
        """
        Tries to open up a subprocess for IPC with the C++ program.
        If successful, interaction will begin with initial data transaction.
        Also sets up the state, time, and reward variables.
        """
        self.t = 0
        self.valid_actions = []
        self.cur_state = None
        self.last_reward = None
        cmd = EXEC + " " + rom
        try:
            self.proc = subprocess.Popen(cmd.split(),
                stdout = subprocess.PIPE, stdin = subprocess.PIPE)
            self.connect()
        except:
            self.proc = None
            print "Error: failed to run command '" + cmd + "'"

    def writeline(self, msg):
        """Writes a single line out through the pipe."""
        if self.proc is None:
            return
        self.proc.stdin.write(msg + "\n")
        self.proc.stdin.flush()

    def readline(self):
        """Returns a line from the pipe with the trailing newline removed."""
        if self.proc is None:
            return ""
        return self.proc.stdout.readline().rstrip()

    def get_next_message(self):
        """
        Returns the next message sent by the C++ code as a list of lines.
        Any output received before the message is ignored.
        """
        line = self.readline()
        while line != Protocol.MESSAGE_START:
            line = self.readline()
        message = []
        line = self.readline()
        while line != Protocol.MESSAGE_END:
            message.append(line)
            line = self.readline()
        return message

    def send_message(self, messages):
        """
        Sends the given list of messages to the C++ code.
        If you're only sending one message, pass it as a list anyway.
        """
        if self.proc is not None:
            self.proc.stdin.write(Protocol.MESSAGE_START + "\n")
            for msg in messages:
                self.proc.stdin.write(msg + "\n")
            self.proc.stdin.write(Protocol.MESSAGE_END + "\n")
            self.proc.stdin.flush()

    def connect(self):
        """Establishes connection with the C++ code and receives valid actions."""
        greeting = self.get_next_message()
        print '\n'.join(greeting)
        actions = self.get_next_message()
        self.valid_actions = map(int, actions)

    def recv_state(self):
        """Reads a state from C++ and returns the State object."""
        self.cur_state = State(self.t)
        obj_params = self.get_next_message()
        num_objs = len(obj_params)/9 # TODO - define 9 elsewhere
        for i in range(num_objs):
            obj = ALEObject(obj_params[i:i+9])
            self.cur_state.add_object(obj)
        self.t += 1

    def send_action_get_reward(self, action):
        """Sends the selected action and gets the reward."""
        self.send_message([str(action)])
        self.last_reward = self.get_next_message()

    def get_valid_actions(self):
        """Returns a list of valid actions."""
        return self.valid_actions

    def do_action(self, action):
        """Selects the chosen action ."""
        if action in self.valid_actions:
            self.send_action_get_reward(action)
        else:
            raise "Invalid Action!"

    def get_state_and_reward(self):
        """
        Returns the current game state at time t and the reward at previous
        time t-1 as a tuple.
        """
        self.recv_state()
        return self.cur_state, self.last_reward