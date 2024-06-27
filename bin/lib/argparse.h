#include <string>

using namespace std;


/* checkOption
 * 
 * Parses through arguments and checks if an option/flag exists.
 * 
 * Parameters:
 *      - name: C string to match option with
 *      - argc: number of arguments
 *      - argv: array of C-style arguments
 * 
 * Returns: bool representing whether the flag exists.
 */
bool checkOption(char *name, int argc, char *argv[]);

/* getCStringArg
 * 
 * Parses through arguments, and returns value of matching name of the format:
 * 
 *                  <option> <value> 
 * 
 * Where <option> is matched to name.
 * 
 * Parameters:
 *      - name: C string to match option with
 *      - argc: number of arguments
 *      - argv: array of C-style arguments
 * 
 * Returns: C string representing the matching value. If no such value is found,
 *          then the null character is returned.
 */
char *getCStringArg(char *name, int argc, char *argv[]);

/* getStringArg
 * 
 * Parses through arguments, and returns value of matching name of the format:
 * 
 *                  <option> <value> 
 * 
 * Where <option> is matched to name.
 * 
 * Parameters:
 *      - name: C string to match option with
 *      - argc: number of arguments
 *      - argv: array of C-style arguments
 * 
 * Returns: std::string representing the matching value. If no such value is found,
 *          then the null character is returned.
 */
string getStringArg(char *name, int argc, char *argv[]);

/* getIntArg
 * 
 * Parses through arguments, and returns value of matching name of the format:
 * 
 *                  <option> <value> 
 * 
 * Where <option> is matched to name.
 * 
 * Parameters:
 *      - name: C string to match option with
 *      - argc: number of arguments
 *      - argv: array of C-style arguments
 * 
 * Returns: Integer representing the matching value. If no such value is found,
 *          it exits with status 2.
 */
int getIntArg(char *name, int argc, char *argv[]);

/* getArg
 * 
 * Parses through arguments, and returns value of matching name of the format:
 * 
 *                  <option> <value> 
 * 
 * Where <option> is matched to name.
 * 
 * Parameters:
 *      - name: C string to match option with
 *      - argc: number of arguments
 *      - argv: array of C-style arguments
 * 
 * Returns: Integer representing the matching value. If no such value is found,
 *          it exits with status 2.
 */
float getFloatArg(char *name, int argc, char *argv[]);
