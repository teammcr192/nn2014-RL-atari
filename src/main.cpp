/* File: main.cpp
 *
 * Neural Networks, Fall 2014
 *
 * Provides a wrapper to interface with the ALE emulator.
 * This was hacked together... don't take this code seriously.
 *
 * ROM_DIRECTORY has been pre-defined by the Makefile.
 */

#include <iostream>
#include <string>
#include <vector>
#include "ale_interface.hpp"
#include "ipc.h"

using namespace std;

typedef map<long,CompositeObject>::iterator ObjMapItr;
#define OBJECTS ale.visProc->composite_objs


int main(int argc, char** argv)
{
    bool enable_comm = true;
    if(argc > 2 && string(argv[2]) == "-test")
        enable_comm = false;
    ALEComm comm(enable_comm);
    bool testing = !enable_comm;

    // set up the rom path
    if(argc < 2)
    {
        cout << "Please provide the name of a rom file." << endl;
        comm.sendMessage("Failed to load: no arguments.");
        return 0;
    }
    string rom_file = string(ROM_DIRECTORY) + "/" + string(argv[1]) + ".bin";

    comm.sendMessage("Hello from C++!");
    cout << "Loading ROM: " << rom_file << endl;

    // set up the emulator and load the rom
    ALEInterface ale;
    bool disp_screen = true;
    if(!testing)
        disp_screen = comm.getBool();
    bool proc_screen = true;
    ale.loadROM(rom_file, false, proc_screen); // TODO - second param disp_screen?

    // send initial greeting and set of valid actions
    vector<string> legal_actions;
    for(ActionVect::iterator it = ale.legal_actions.begin();
        it != ale.legal_actions.end();
        it++)
    {
        legal_actions.push_back(to_string(*it));
    }
    comm.sendMessage(legal_actions);

    // if displaying screen, also send screen width and height
    if(disp_screen)
    {
        comm.sendMessage(to_string(ale.screen_width));
        comm.sendMessage(to_string(ale.screen_height));
    }

    // play n episodes
    int episode = 0;
    while(comm.isGameStarting())
    {
        cout << "Game starting." << endl;
        episode++;
        float total_reward = 0;
        int frame = 0;
        while(!ale.game_over())
        {
            // send the state to python
            vector<string> obj_params;
            for(ObjMapItr it = OBJECTS.begin(); it != OBJECTS.end(); it++)
            {
                CompositeObject &obj = it->second;
                obj_params.push_back(to_string(obj.id));
                obj_params.push_back(to_string(obj.x_velocity));
                obj_params.push_back(to_string(obj.y_velocity));
                obj_params.push_back(to_string(obj.x_min));
                obj_params.push_back(to_string(obj.x_max));
                obj_params.push_back(to_string(obj.y_min));
                obj_params.push_back(to_string(obj.y_max));
                obj_params.push_back(to_string(obj.frames_since_last_movement));
                obj_params.push_back(to_string(obj.age));
            }
            comm.sendMessage(obj_params);

            // if self is known, send that
            if(testing && ale.visProc->found_self())
            {
                cout << "Found self!" << endl;
                cout << ale.visProc->self_id << endl;
            }

            // if displaying screen and not testing, send all the pixel values
            if(disp_screen && enable_comm)
            {
                string pixels = "";
                for(int y=0; y<ale.screen_height; y++)
                {
                    for(int x=0; x<ale.screen_width; x++)
                    {
                        uInt8 pixel = ale.screen_matrix[y][x];
                        pixels += to_string(pixel) + " ";
                    }
                }
                comm.sendMessage(pixels);
            }

            // get an action selection from python
            int choice = comm.getAction();
            if(testing)
                choice = rand() % legal_actions.size();
            Action a = ale.legal_actions[choice];
            
            // apply the action and send back the reward
            float reward = ale.act(a);
            comm.sendMessage(to_string(reward));
            total_reward += reward;
            if(testing)
            {
                if(reward != 0)
                    cout << "Test frame " << frame << ", reward = "
                         << reward << endl;
                /*if(frame % 100 == 0)
                {
                    for(int y=0; y<ale.screen_height; y++)
                    {
                        for(int x=0; x<ale.screen_width; x++)
                        {
                            uInt8 pixel = ale.screen_matrix[x][y];
                            if(pixel > 0)
                                cout << pixel / 26;
                            else
                                cout << " ";
                        }
                        cout << endl;
                    }
                    cout << "------------" << endl;
                }*/
            }
            frame++;
        }

        cout << "Episode " << (episode) << ", score = " << total_reward << endl;
        if(total_reward < 100)
            cout << "Wow, you really suck." << endl;
        ale.reset_game();
        comm.sendMessage(GAME_END);
        if(testing)
            break;
    }
}

