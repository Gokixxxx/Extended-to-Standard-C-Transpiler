#include "option.h"
#include "vec.h"
#include "closure.h"

struct __env_1 {
    int a;
};

static int __fn_1(void *__env, int b) {
    struct __env_1 *env = (struct __env_1 *)__env;
    int a = env->a;
    return (a + b);
}

Closure_i32_i32 add(int a) {
    struct __env_1 *ret_env = malloc(sizeof(struct __env_1));
    ret_env->a = a;
    Closure_i32_i32 ret = {ret_env, __fn_1};
    return ret;
}

int main() {
    Closure_i32_i32 f = add(3);
    int x = f.fn(f.env, 4);
    free(f.env);
    return 0;
}