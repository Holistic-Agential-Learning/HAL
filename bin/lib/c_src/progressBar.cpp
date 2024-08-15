#include "progressBar.h"

using namespace std;

ProgressBar::ProgressBar() {
    for (int i = 0; i < 50; i++) {
        bar.push_back(".");
    }

    current = 0;
}

void ProgressBar::increment() {
    bar[current] = "#";

}

void ProgressBar::printBar() {
    cout << "\r[";
    for (int i = 0; i < 50; i++) {
        cout << bar[i];
    }

     cout << "] " << (int) ((float) current) / 50 << "%";
}