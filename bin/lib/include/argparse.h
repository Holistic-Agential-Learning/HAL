/**
 * @file argparse.h
 * @author Trevor Sullivan (trevor.sullivan@tufts.edu)
 * @brief Header file for argparse module
 * @version 0.1
 * @date 2024-09-18
 * 
 * @copyright Copyright (c) 2024
 * 
 */
#ifndef __ARGPARSE_H__
#define __ARGPARSE_H__

#include <string>

using namespace std;

/**
 * @brief test
 * DOCUMENTING THE NAMESPACE
 */
namespace argparse {
    
/**
 * @brief Parses through arguments and checks if an option/flag exists
 * 
 * @param name <code>string</code> to match option with
 * @param argc <code>int</code> representing the number of arguments
 * @param argv array of <code>char</code> arrays, representing string arguments
 * 
 * @return <code>bool</code> representing whether the flag exists.
 */
bool checkOption(string name, int argc, char *argv[]);


/**
 * @brief Gets the value of an argument option as a <code>string</code>
 * 
 * Parses through arguments, and returns value of matching name of the format:
 * 
 *                  <option> <value> 
 * 
 * Where <option> is matched to <code>name</code>. This functions exits when 
 * the option isn't found, and prints an optional usage message
 * 
 * @param name <code>string</code> to match option with
 * @param argc <code>int</code> indicating the number of arguments
 * @param argv array of <code>char</code> arrays, representing string arguments
 * @param usage <code>string</code> representing an optional usage message, 
 *              printed upon failure, default=<code>""</code>
 * @return <code>string</code> 
 */
string getStringArg(string name, int argc, char *argv[], string usage="");


/**
 * @brief Gets the value of an argument option as an <code>int</code>
 * 
 * Parses through arguments, and returns value of matching name of the format:
 * 
 *                  <option> <value> 
 * 
 * Where <option> is matched to <code>name</code>. This functions exits when 
 * the option isn't found, and prints an optional usage message
 * 
 * @param name <code>string</code> to match option with
 * @param argc <code>int</code> indicating the number of arguments
 * @param argv array of <code>char</code> arrays, representing string arguments
 * @param usage <code>string</code> representing an optional usage message, 
 *              printed upon failure, default=<code>""</code>
 * @return <code>int</code> 
 */
int getIntArg(string name, int argc, char *argv[], string usage="");


/**
 * @brief Gets the value of an argument option as an <code>float</code>
 * 
 * Parses through arguments, and returns value of matching name of the format:
 * 
 *                  <option> <value> 
 * 
 * Where <option> is matched to <code>name</code>. This functions exits when 
 * the option isn't found, and prints an optional usage message
 * 
 * @param name <code>string</code> to match option with
 * @param argc <code>int</code> indicating the number of arguments
 * @param argv array of <code>char</code> arrays, representing string arguments
 * @param usage <code>string</code> representing an optional usage message, 
 *              printed upon failure, default=<code>""</code>
 * @return <code>float</code> 
 */
float getFloatArg(string name, int argc, char *argv[], string usage="");


/**
 * @brief Gets the value of an argument option as a <code>string</code>
 * 
 * Parses through arguments, and returns value of matching name of the format:
 * 
 *                  <option> <value> 
 * 
 * Where <option> is matched to <code>name</code>. 
 * 
 * @param name <code>string</code> to match option with
 * @param defaultValue <code>string</code> representing the default value if the
 *                      option isn't found
 * @param argc <code>int</code> indicating the number of arguments
 * @param argv array of <code>char</code> arrays, representing string arguments
 * @return <code>string</code>; will return <code>defaultValue</code> if the 
 *          option isn't found
 */
string getStringArgSecure(string name, string defaultValue, int argc, char *argv[]);


/**
 * @brief Gets the value of an argument option as a <code>int</code>
 * 
 * Parses through arguments, and returns value of matching name of the format:
 * 
 *                  <option> <value> 
 * 
 * Where <option> is matched to <code>name</code>. 
 * 
 * @param name <code>string</code> to match option with
 * @param defaultValue <code>int</code> representing the default value if the
 *                      option isn't found
 * @param argc <code>int</code> indicating the number of arguments
 * @param argv array of <code>char</code> arrays, representing string arguments
 * @return <code>int</code>; will return <code>defaultValue</code> if the 
 *          option isn't found
 */
int getIntArgSecure(string name, int defaultValue, int argc, char *argv[]);

/**
 * @brief Gets the value of an argument option as a <code>float</code>
 * 
 * Parses through arguments, and returns value of matching name of the format:
 * 
 *                  <option> <value> 
 * 
 * Where <option> is matched to <code>name</code>. 
 * 
 * @param name <code>string</code> to match option with
 * @param defaultValue <code>float</code> representing the default value if the
 *                      option isn't found
 * @param argc <code>int</code> indicating the number of arguments
 * @param argv array of <code>char</code> arrays, representing string arguments
 * @return <code>float</code>; will return <code>defaultValue</code> if the 
 *          option isn't found
 */
float getFloatArgSecure(string name, float defaultValue, int argc, char *argv[]);

};

#endif