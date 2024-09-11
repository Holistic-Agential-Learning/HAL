#include "controller.h"

#ifndef __NES_H__
#define __NES_H__

using namespace std;

class NES : public Controller {
    public:
        void addButtonA(const char *configPath);

        void addButtonB(const char *configPath);

        void addButton();


    private:

};

#endif