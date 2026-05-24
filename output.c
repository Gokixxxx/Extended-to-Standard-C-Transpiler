#include "option.h"
#include "vec.h"
#include "closure.h"

struct __env_1 {
    int outer;
};

struct __env_4 {
    int a;
};

struct __env_5 {
    int b;
};

struct __env_6 {
    int base;
};

int apply(int (*f)(int), int x) {
    return f(x);
}

static int __fn_1(void *__env, int x) {
    struct __env_1 *env = (struct __env_1 *)__env;
    int outer = env->outer;
    return (outer + x);
}

static int __fn_2(int x) {
    return (x * 2);
}

static int __fn_3(int y) {
    return (5 + y);
}

static int __fn_4(void *__env, int x) {
    struct __env_4 *env = (struct __env_4 *)__env;
    int a = env->a;
    return (a + x);
}

static int __fn_5(void *__env, int y) {
    struct __env_5 *env = (struct __env_5 *)__env;
    int b = env->b;
    return (b + y);
}

static int __fn_6(void *__env, int z) {
    struct __env_6 *env = (struct __env_6 *)__env;
    int base = env->base;
    int local = 50;
    return ((base + local) + z);
}

int main() {
    int outer = 10;
    struct __env_1 *f_env = malloc(sizeof(struct __env_1));
    f_env->outer = outer;
    Closure_i32_i32 f = {f_env, __fn_1};
    int r = f.fn(f.env, 5);
    int (*doubled)(int) = __fn_2;
    int result = doubled(10);
    int (*add5)(int) = __fn_3;
    int applied = apply(add5, 10);
    Vec_i32 v = vec_new_i32();
    vec_push_i32(&v, 1);
    vec_push_i32(&v, 2);
    vec_push_i32(&v, 3);
    vec_push_i32(&v, 4);
    int len = vec_len_i32(v);
    int first = vec_get_i32(v, 0);
    Option_i32 opt = Some_i32(42);
    int matched;
    if (opt.is_some) {
        matched = (opt.value + 1);
    } else {
        matched = 0;
    }
    Vec_i32 arr = vec_new_i32();
    vec_push_i32(&arr, 10);
    vec_push_i32(&arr, 20);
    vec_push_i32(&arr, 30);
    int sum = 0;
    {
        int __t1 = 0;
        for (; __t1 < vec_len_i32(arr); __t1++) {
            int x = vec_get_i32(arr, __t1);
            sum = (sum + x);
        }
    }
    int a = 1;
    int b = 2;
    struct __env_4 *fa_env = malloc(sizeof(struct __env_4));
    fa_env->a = a;
    Closure_i32_i32 fa = {fa_env, __fn_4};
    struct __env_5 *fb_env = malloc(sizeof(struct __env_5));
    fb_env->b = b;
    Closure_i32_i32 fb = {fb_env, __fn_5};
    int ra = fa.fn(fa.env, 10);
    int rb = fb.fn(fb.env, 20);
    int base = 100;
    struct __env_6 *fc_env = malloc(sizeof(struct __env_6));
    fc_env->base = base;
    Closure_i32_i32 fc = {fc_env, __fn_6};
    int rc = fc.fn(fc.env, 5);
    free(v.data);
    free(arr.data);
    free(fc_env);
    free(f_env);
    free(fb_env);
    free(fa_env);
    return 0;
}