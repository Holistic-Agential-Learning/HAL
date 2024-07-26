#include <string>

using namespace std;


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

/* getStringArg
 * 
 * Parses through arguments, and returns value of matching name of the format:
 * 
 *                  <option> <value> 
 * 
 * Where <option> is matched to name.
 * 
 * Parameters:
 *      - name: string to match option with
 *      - argc: number of arguments
 *      - argv: array of C-style arguments
 *      - usage: optional usage message to print on failure
 * 
 * Returns: std::string representing the matching value. If no such value is found,
 *          then the null character is returned.
 */
string getStringArg(string name, int argc, char *argv[], string usage="");

/* getIntArg
 * 
 * Parses through arguments, and returns value of matching name of the format:
 * 
 *                  <option> <value> 
 * 
 * Where <option> is matched to name.
 * 
 * Parameters:
 *      - name: string to match option with
 *      - argc: number of arguments
 *      - argv: array of C-style arguments
 *      - usage: optional usage message to print on failure
 * 
 * Returns: Integer representing the matching value. If no such value is found,
 *          it exits with status 2.
 */
int getIntArg(string name, int argc, char *argv[], string usage="");

/* getFloatArg
 * 
 * Parses through arguments, and returns value of matching name of the format:
 * 
 *                  <option> <value> 
 * 
 * Where <option> is matched to name.
 * 
 * Parameters:
 *      - name: string to match option with
 *      - argc: number of arguments
 *      - argv: array of C-style arguments
 *      - usage: optional usage message to print on failure
 * 
 * Returns: Integer representing the matching value. If no such value is found,
 *          it exits with status 2.
 */
float getFloatArg(string name, int argc, char *argv[], string usage="");


/* getStringArgSecure
 * 
 * Parses through arguments, and returns value of matching name of the format:
 * 
 *                  <option> <value> 
 * 
 * Where <option> is matched to name. If the option isn't found, it returns the 
 * given default value.
 * 
 * Parameters:
 *      - name: string to match option with
 *      - defaultValue: string representing the default value if the option 
 *                      isn't found
 *      - argc: number of arguments
 *      - argv: array of C-style arguments
 * 
 * Returns: std::string representing the matching value. If no such value is found,
 *          then the null character is returned.
 */
string getStringArgSecure(string name, string defaultValue, int argc, char *argv[]);


/* getIntArgSecure
 * 
 * Parses through arguments, and returns value of matching name of the format:
 * 
 *                  <option> <value> 
 * 
 * Where <option> is matched to name. If the option isn't found, it returns the 
 * default value.
 * 
 * Parameters:
 *      - name: string to match option with
 *      - defaultValue: integer representing the default value if the option 
 *                      isn't found 
 *      - argc: number of arguments
 *      - argv: array of C-style arguments
 * 
 * Returns: Integer representing the matching value. If no such value is found,
 *          it returns defaultValue.
 */
int getIntArgSecure(string name, int defaultValue, int argc, char *argv[]);

/* getFloatArgSecure
 * 
 * Parses through arguments, and returns value of matching name of the format:
 * 
 *                  <option> <value> 
 * 
 * Where <option> is matched to name. If the option isn't found, it returns the 
 * default value.
 * 
 * Parameters:
 *      - name: string to match option with
 *      - defaultValue: integer representing the default value if the option 
 *                      isn't found 
 *      - argc: number of arguments
 *      - argv: array of C-style arguments
 * 
 * Returns: Integer representing the matching value. If no such value is found,
 *          it returns defaultValue.
 */
float getFloatArgSecure(string name, float defaultValue, int argc, char *argv[]);
