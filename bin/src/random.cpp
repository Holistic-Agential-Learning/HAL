#include <iostream>
#include <stdlib.h>

using namespace std;

int main(int argc, char *argv[]) {
    srand(1);
    for (int i = 0; i < 10; i++) {
        cout << rand() << endl;
    }
} 