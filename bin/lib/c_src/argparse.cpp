/**
 * @file argparse.cpp
 * @author Trevor Sullivan (trevor.sullivan@tufts.edu)
 * @brief Implementation of the argparse Module
 * @version 0.1
 * @date 2024-09-18
 * 
 * @copyright Copyright (c) 2024
 * 
 */
#include "argparse.h"
#include <iostream>
#include <cstring>

namespace argparse {

bool checkOption(string name, int argc, char *argv[]) {
    const char * n = name.c_str();
    for (int i = 0; i < argc; i++) {
        if (strcmp(argv[i], n) == 0) {
            return true;
        }
    }

    return false;
}

string getStringArg(string name, int argc, char *argv[], string usage) {
    const char * n = name.c_str();
    for (int i = 0; i < argc; i++) {
        char *arg = argv[i];

        if (strcmp(arg, n) == 0) {
            return string(argv[i + 1]);
        }
    }
    if (usage != "") {
        cout << usage << endl;
    }
    cout << "Error: argument " << name << " not found." << endl;
    exit(1);
}

int getIntArg(string name, int argc, char *argv[], string usage) {
    string arg = getStringArg(name, argc, argv, usage);

    if (arg == "\0") {
        cerr << "Integer argument <" << name << "> not found." << endl;
        exit(2);
    }

    return stoi(arg);
}

float getFloatArg(string name, int argc, char *argv[], string usage) {
    string arg = getStringArg(name, argc, argv, usage);

    if (arg == "\0") {
        cerr << "Float argument <" << name << "> not found." << endl;
        exit(2);
    }

    return stof(arg);
}

string getStringArgSecure(string name, string defaultValue, int argc, char *argv[]) {
    const char * n = name.c_str();
    for (int i = 0; i < argc; i++) {
        char *arg = argv[i];

        if (strcmp(arg, n) == 0) {
            return string(argv[i + 1]);
        }
    }

    return defaultValue;
}

int getIntArgSecure(string name, int defaultValue, int argc, char *argv[]) {
    if (checkOption(name, argc, argv)) {
        string arg = getStringArg(name, argc, argv);
        return stoi(arg);
    }

    return defaultValue;
}

float getFloatArgSecure(string name, float defaultValue, int argc, char *argv[]) {
    if (checkOption(name, argc, argv)) {
        string arg = getStringArg(name, argc, argv);
        return stof(arg);
    }

    return defaultValue;
}

};