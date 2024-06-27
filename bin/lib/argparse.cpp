#include "argparse.h"


int getIntArg(char *name, int argc, char *argv[]) {
    char *arg = getCStringArg(name, argc, argv);

    if (strcmp(arg, "\0") == 0) {
        return ~0;
    }

    return stoi(string(arg));
}

float getFloatArg(char *name, int argc, char *argv[]) {
    char *arg = getCStringArg(name, argc, argv);

    if (strcmp(arg, "\0") == 0) {
        return ~0;
    }

    return stof(string(arg));
}

string getStringArg(char *name, int argc, char *argv[]) {
    char *arg = getCStringArg(name, argc, argv);

    return string(arg);
}

char *getCStringArg(char *name, int argc, char *argv[]) {
    for (int i = 0; i < argc; i++) {
        char *arg = argv[i];

        if (strcmp(arg, name) == 0) {
             return argv[i + 1];
        }
    }

    return "\0";
}

// int getArgNameIndex(char *name, int argc, char *argv[]) {
//     for (int i = 0; i < argc; i++) {
//         char *arg = argv[i];

//         if (strcmp(arg, name) == 0) {
//              return i;
//         }
//     } 
// }