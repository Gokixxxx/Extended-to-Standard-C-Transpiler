#include "option.h"
#include "vec.h"
#include "closure.h"

struct __env_1 {
    int a;
};

static int __fn_1(void *__env, int x) {
    struct __env_1 *env = (struct __env_1 *)__env;
    int a = env->a;
    return (a + x);
}

static int __fn_2(int x) {
    return (x + 3);
}
static int __fn_2_closure(void *__env, int x) {
    (void)__env;
    return __fn_2(x);
}

int apply_twice(Closure_i32_i32 f, int x) {
    return f.fn(f.env, f.fn(f.env, x));
}

int main() {
    int a = 10;
    struct __env_1 *f_env = malloc(sizeof(struct __env_1));
    f_env->a = a;
    Closure_i32_i32 f = {f_env, __fn_1};
    Closure_i32_i32 g = f;
    f.env = NULL;
    int r1 = g.fn(g.env, 5);
    int (*add3)(int) = __fn_2;
    Closure_i32_i32 __t1 = {NULL, __fn_2_closure};
    int r6 = apply_twice(__t1, 5);
    free(f.env);
    free(g.env);
    return 0;
}