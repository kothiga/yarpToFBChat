import numpy as np
from fbchat import Client
from fbchat.models import *
import yarp
import time
import argparse

# Init Yarp.
yarp.Network.init()

def get_args():
    parser = argparse.ArgumentParser(description='yarpToFBChat')
    parser.add_argument('-n', '--name',     default="/messenger",  help='Name for the module.              (default: {})'.format("/messenger"))
    parser.add_argument('-u', '--username', default=None,          help='Username to log into fbchat with. (default: {})'.format("NONE"))
    parser.add_argument('-p', '--password', default=None,          help='Password to log into fbchat with. (default: {})'.format("NONE"))
    parser.add_argument('-s', '--sendto',   default=None,          help='Recipient of messages.            (default: {})'.format("NONE"))
    args = parser.parse_args()
    return args


class Messenger(object):

    def __init__(self, args):

        # Make sure we have some credentials.
        if args.username == None or args.password == None:
            print("Please Provide a Username and Password . . . ")
            exit()

        # Check that the recipient was provided.
        if args.sendto == None:
            print("Please Provide a recipient with ``--sendto <Name>``")
            exit()

        # Try logging in with the credentials.
        self.client = Client(args.username, args.password)

        # Query the recipient.
        users_list = self.client.searchForUsers(args.sendto)
        if len(users_list) == 0:
            print("Could not find the user to send to.")
            self.client.logout()
            exit()

        # Give brief info on who we are sending messages to.
        recipient = users_list[0]
        self.uid  = recipient.uid
        self.name = recipient.name
        print("\nUser's ID   : {}".format(self.uid))
        print(  "User's name : {}".format(self.name))
        print(  "User's URL  : {}".format(recipient.url))
        
        while True:
            print("\nPlease confirm this is the correct user . . .")
            confirmation = input(" [Y/N]  ")
            print(" ")

            if confirmation.lower() in ['y', 'yes']:  
                break
            
            elif confirmation.lower() in ['n', 'no']:
                print("Closing Messenger Client . . .")
                self.client.logout()
                exit()
            
            else:
                print("Incorrect input ``{}``. Please try again . . .".format(confirmation))
        
        print(" ")
        
        # Init the Yarp Port.
        self.port_name  = args.name

        print("Initializing Yarp Ports . . .")
        self.input_port = yarp.Port()
        self.input_port.open(self.port_name + ":i")

        # Init complete. Send first messages.
        print("\nInitialization Complete @ {}!!\n".format(self._getTimeStamp()))
        self._sendMessage("Initialization Complete @ {}.".format(self._getTimeStamp()))
        self._sendMessage("I'll forward you messages as they come!!")
        


    def run(self):

        # Initialize yarp containers.
        command = yarp.Bottle()

        # Loop until told to quit.
        while True:

            self.input_port.read(command)
            cmd = command.get(0).asString()
            len = command.size()

            # Kill this script.
            if cmd == "quit": 
                print("\nClosing Process @ {}!!".format(self._getTimeStamp()))
                self._sendMessage("Closing Forwarding Client @ {}.".format(self._getTimeStamp()))
                self._sendMessage("Good Bye!!")
                break

            # Forward messages.
            if cmd == "send" and len > 1:
                for idx in range(1, len):
                    self._sendMessage(command.get(idx).asString())
        
        return



    def _sendMessage(self, msg):
        print("[Sending {}]   {}".format(self._getTimeStamp(), msg))
        self.client.send(
            Message(text=msg), 
            thread_id=self.uid, 
            thread_type=ThreadType.USER
        )



    def _getTimeStamp(self):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())



    def cleanup(self):
        print("\nClosing Messenger Client.")
        self.client.logout()

        print("Closing Yarp Ports.")
        self.input_port.close()



def main():

    # Get arguments from parser.
    args = get_args()

    # Initialize the messenger.
    messenger = Messenger(args)

    # Loop.
    try:
        messenger.run()
    finally:
        messenger.cleanup()


if __name__ == '__main__':
    main()
