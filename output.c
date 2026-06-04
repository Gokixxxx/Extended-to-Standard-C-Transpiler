#include "option.h"
#include "vec.h"
#include "closure.h"

struct __env_1 {
    int x2;
};

struct __env_2 {
    int x2;
};

static int __fn_1(void *__env, int a) {
    struct __env_1 *env = (struct __env_1 *)__env;
    int x2 = env->x2;
    return (x2 + a);
}

static int __fn_2(void *__env, int b) {
    struct __env_2 *env = (struct __env_2 *)__env;
    int x2 = env->x2;
    return (x2 * b);
}

int main() {
    int x2 = 10;
    int r14 = 0;
    if ((x2 > 5)) {
        struct __env_1 *f4_env = malloc(sizeof(struct __env_1));
        f4_env->x2 = x2;
        Closure_i32_i32 f4 = {f4_env, __fn_1};
        r14 = f4.fn(f4.env, 1);;
        free(f4.env);
    }
    else {
        struct __env_2 *g1_env = malloc(sizeof(struct __env_2));
        g1_env->x2 = x2;
        Closure_i32_i32 g1 = {g1_env, __fn_2};
        r14 = g1.fn(g1.env, 2);;
        free(g1.env);
    }
    return 0;
}