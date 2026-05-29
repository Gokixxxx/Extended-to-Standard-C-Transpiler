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

int main() {
    int a = 1;
    struct __env_1 *f_env = malloc(sizeof(struct __env_1));
    f_env->a = a;
    Closure_i32_i32 f = {f_env, __fn_1};
    if ((1 > 0)) {
        Closure_i32_i32 g = f;
        f.env = NULL;
        free(g.env);
    }
    else {
        Closure_i32_i32 h = f;
        f.env = NULL;
        free(h.env);
    }
    free(f.env);
    return 0;
}