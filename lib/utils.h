#include <stdio.h>
#define assert(x) (x || printf("%s:%d: Assertion \"%s\" failed.\n", __FILE__, __LINE__, #x), exit(1))