#include "option.h"
#include "vec.h"
#include "closure.h"

static int __fn_1(int n) {
    return (n * 2);
}

int apply_twice(int (*f)(int), int x) {
    return f(f(x));
}

int mytest(void) {
    int (*doubled)(int) = __fn_1;
    int result = apply_twice(doubled, 3);
}

int main() {
    return 0;
}