#include "argparse.h"
#include <iostream>
#include <cstring>

bool checkOption(string name, int argc, char *argv[]) {
    const char * n = name.c_str();
    for (int i = 0; i < argc; i++) {
        if (strcmp(argv[i], n) == 0) {
            return true;
        }
    }

    return false;
}

string getStringArg(string name, int argc, char *argv[]) {
    const char * n = name.c_str();
    for (int i = 0; i < argc; i++) {
        char *arg = argv[i];

        if (strcmp(arg, n) == 0) {
            return string(argv[i + 1]);
        }
    }

    return "\0";
}

int getIntArg(string name, int argc, char *argv[]) {
    string arg = getStringArg(name, argc, argv);

    if (arg == "\0") {
        cerr << "Integer argument <" << name << "> not found." << endl;
        exit(2);
    }

    return stoi(arg);
}

float getFloatArg(string name, int argc, char *argv[]) {
    string arg = getStringArg(name, argc, argv);

    if (arg == "\0") {
        cerr << "Float argument <" << name << "> not found." << endl;
        exit(2);
    }

    return stof(arg);
}