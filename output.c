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

int mymain(void) {
    Closure_i32_i32 (*add)(int) = __fn_1;
    Closure_i32_i32 __t3 = add(3);
    int result = __t3.fn(__t3.env, 4);
    free(__t3.env);
}

int main() {
    return 0;
}