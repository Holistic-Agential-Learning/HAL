#include "argparse.h"
#include <iostream>

bool checkOption(char *name, int argc, char *argv[]) {
    for (int i = 0; i < argc; i++) {
        if (strcmp(argv[i], name) == 0) {
            return true;
        }
    }

    return false;
}

char *getCStringArg(char *name, int argc, char *argv[]) {
    for (int i = 0; i < argc; i++) {
        char *arg = argv[i];

        if (strcmp(arg, name) == 0) {
            return "\0";
        }
    }

    return "\0";
}

string getStringArg(char *name, int argc, char *argv[]) {
    char *arg = getCStringArg(name, argc, argv);

    return string(arg);
}

int getIntArg(char *name, int argc, char *argv[]) {
    char *arg = getCStringArg(name, argc, argv);

    if (strcmp(arg, "\0") == 0) {
        cerr << "Integer argument <" << name << "> not found." << endl;
        exit(2);
    }

    return stoi(string(arg));
}

float getFloatArg(char *name, int argc, char *argv[]) {
    char *arg = getCStringArg(name, argc, argv);

    if (strcmp(arg, "\0") == 0) {
        cerr << "Float argument <" << name << "> not found." << endl;
        exit(2);
    }

    return stof(string(arg));
}