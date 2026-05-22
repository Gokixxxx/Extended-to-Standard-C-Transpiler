#include "option.h"

int add(int a, int b) {
    return (a + b);
}

Option_i32 make_some(int x) {
    return Some_i32(x);
}

int main() {
    int x = add(1, 2);
    Option_i32 y = make_some(10);
    int z;
    if (y.is_some) {
        z = (y.value + 1);
    } else {
        z = 0;
    }
    return 0;
}