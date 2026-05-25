#include "option.h"
#include "vec.h"
#include "closure.h"

struct __env_2 {
    int a;
};

static int __fn_2(void *__env, int b) {
    struct __env_2 *env = (struct __env_2 *)__env;
    int a = env->a;
    return (a + b);
}

static Closure_i32_i32 __fn_1(int a) {
    struct __env_2 *__t1 = malloc(sizeof(struct __env_2));
    __t1->a = a;
    Closure_i32_i32 __t2 = {__t1, __fn_2};
    return __t2;
}

int apply_closure(Closure_i32_i32 f, int x) {
    return f.fn(f.env, x);
}

int main() {
    Closure_i32_i32 (*make_adder)(int) = __fn_1;
    Closure_i32_i32 add5 = make_adder(5);
    int result = apply_closure(add5, 10);
    printf("%d\n", result);
    return 0;
}