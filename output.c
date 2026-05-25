#include "option.h"
#include "vec.h"
#include "closure.h"

struct __env_3 {
    int a;
};

static int __fn_1(int y) {
    return (y * 2);
}

static int __fn_3(void *__env, int b) {
    struct __env_3 *env = (struct __env_3 *)__env;
    int a = env->a;
    return (a + b);
}

static Closure_i32_i32 __fn_2(int a) {
    struct __env_3 *__t2 = malloc(sizeof(struct __env_3));
    __t2->a = a;
    Closure_i32_i32 __t3 = {__t2, __fn_3};
    return __t3;
}

int apply(Closure_i32_i32 f, int x) {
    return f.fn(f.env, x);
}

int apply_closure(Closure_i32_i32 f, int x) {
    return f.fn(f.env, x);
}

int main() {
    int (*doubled)(int) = __fn_1;
    Closure_i32_i32 __t1 = {NULL, doubled};
    int r1 = apply(__t1, 5);
    Closure_i32_i32 (*make_adder)(int) = __fn_2;
    Closure_i32_i32 add5 = make_adder(5);
    int r2 = apply_closure(add5, 10);
    Closure_i32_i32 add3 = make_adder(3);
    int r3 = apply_closure(add3, 7);
    free(add5.env);
    free(add3.env);
    return 0;
}