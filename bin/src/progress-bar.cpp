#include <iostream>
#include <ncurses.h>
#include <unistd.h>
using namespace std;

void printBarRaw(char bar[]) {
    cout << "\r[";
    for (int i = 0; i < 50; i++) {
        cout << bar[i];
    }

     cout << "]";
}

int main()
{
    char bar[50];

    for (int i = 0; i < 50; i++) {
        bar[i] = '.';
    }  

    printBarRaw(bar);

    for (int i = 0; i < 50; i++) {
        bar[i] = '#';
        usleep(100000);
        // cout << '\r' << flush;
        printBarRaw(bar);
    }

    cout << endl;
}

