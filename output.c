#include "option.h"
#include "vec.h"
#include "closure.h"

struct __env_1 {
    int x;
};

struct __env_2 {
    int x;
};

struct __env_3 {
    int j;
};

struct __env_4 {
    int i;
};

struct __env_5 {
    int flag;
};

static int __fn_1(void *__env, int a) {
    struct __env_1 *env = (struct __env_1 *)__env;
    int x = env->x;
    return (x + a);
}

static int __fn_2(void *__env, int b) {
    struct __env_2 *env = (struct __env_2 *)__env;
    int x = env->x;
    return (x * b);
}

static int __fn_3(void *__env) {
    struct __env_3 *env = (struct __env_3 *)__env;
    int j = env->j;
    return j;
}

static int __fn_4(void *__env) {
    struct __env_4 *env = (struct __env_4 *)__env;
    int i = env->i;
    return i;
}

static int __fn_5(void *__env) {
    struct __env_5 *env = (struct __env_5 *)__env;
    int flag = env->flag;
    return flag;
}

static int __fn_6(void) {
    return 42;
}

int main() {
    int x = 10;
    if ((x > 5)) {
        struct __env_1 *f_env = malloc(sizeof(struct __env_1));
        f_env->x = x;
        Closure_i32_i32 f = {f_env, __fn_1};
        int r1 = f.fn(f.env, 1);
        free(f.env);
    }
    else {
        struct __env_2 *g_env = malloc(sizeof(struct __env_2));
        g_env->x = x;
        Closure_i32_i32 g = {g_env, __fn_2};
        int r2 = g.fn(g.env, 2);
        free(g.env);
    }
    Vec_i32 arr = vec_new_i32();
    vec_push_i32(&arr, 1);
    vec_push_i32(&arr, 2);
    vec_push_i32(&arr, 3);
    int sum = 0;
    {
        int __t1 = 0;
        for (; __t1 < vec_len_i32(arr); __t1++) {
            int j = vec_get_i32(arr, __t1);
            struct __env_3 *f_env = malloc(sizeof(struct __env_3));
            f_env->j = j;
            Closure_i32 f = {f_env, __fn_3};
            int r = f.fn(f.env);
            sum = (sum + r);
            free(f.env);
        }
    }
    int i = 0;
    int wsum = 0;
    while ((i < 3)) {
        struct __env_4 *f_env = malloc(sizeof(struct __env_4));
        f_env->i = i;
        Closure_i32 f = {f_env, __fn_4};
        int r = f.fn(f.env);
        wsum = (wsum + r);
        i = (i + 1);
        free(f.env);
    }
    int flag = 1;
    if ((flag > 0)) {
        if ((flag > 0)) {
            struct __env_5 *f_env = malloc(sizeof(struct __env_5));
            f_env->flag = flag;
            Closure_i32 f = {f_env, __fn_5};
            int r = f.fn(f.env);
            free(f.env);
        }
    }
    int (*h)(void) = __fn_6;
    int r0 = h();
    free(arr.data);
    return 0;
}