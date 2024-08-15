#include "progressBar.h"

using namespace std;

ProgressBar::ProgressBar() {
    for (int i = 0; i < 50; i++) {
        bar.push_back('.');
    }

    current = 0;
    desc = "";
}

ProgressBar::ProgressBar(string description) {
    for (int i = 0; i < 50; i++) {
        bar.push_back('.');
    }

    current = 0;
    desc = description;
}

void ProgressBar::increment() {
    bar[current] = '#';
    current++;
    cout << "\r" << flush;
    print();
    
}

void ProgressBar::print() {
    cout << "[";
    for (int i = 0; i < 50; i++) {
        cout << bar[i] << flush;
    }

    float progress = current / 50.0;

    cout << "] " << (int) (progress * 100) << "% " << desc << flush;

}