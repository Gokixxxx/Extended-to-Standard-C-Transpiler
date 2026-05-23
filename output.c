#include "option.h"

int mytest(void) {
    Option_i32 x = Some_i32(5);
    int b = is_some(x);
    int c = is_none(x);
}

int main() {
    return 0;
}