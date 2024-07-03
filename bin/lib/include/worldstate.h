#include <iostream>

using namespace std;


class WorldState{
    private:
        int nodes;
        
        string world_map;//How do we encode different types of rewards? Maybe a char * of length "nodes"?
        //int resetTime;
        //int currentTime;
        //bool circular;

        void validate();

        int remainder(int a, int b);




    public:
        int location;
        WorldState();

        WorldState(string map, int loc);

        void display();

        void move_left();

        void move_right();

        char get_position();
    };
