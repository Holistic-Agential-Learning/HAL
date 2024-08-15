#include <iostream>
#include <ncurses.h>
#include <unistd.h>
using namespace std;

int main()
{
    initscr();

    for (int n = 0; n < 10; n++)
    {
        mvaddch(0,n,'#');
        refresh();
        usleep(10000);
    }
    getch();
    endwin();
}