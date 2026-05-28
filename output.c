#include "option.h"
#include "vec.h"
#include "closure.h"

struct __env_1 {
    int a;
};

struct __env_3 {
    int x;
};

struct __env_4 {
    int b;
};

struct __env_5 {
    int b;
};

struct __env_8 {
    int a;
};

static int __fn_1(void *__env, int x) {
    struct __env_1 *env = (struct __env_1 *)__env;
    int a = env->a;
    return (a + x);
}

static int __fn_2(int x) {
    return (x * 2);
}
static int __fn_2_closure(void *__env, int x) {
    (void)__env;
    return __fn_2(x);
}

static int __fn_3(void *__env, int y) {
    struct __env_3 *env = (struct __env_3 *)__env;
    int x = env->x;
    return (x + y);
}

static int __fn_4(void *__env, int x) {
    struct __env_4 *env = (struct __env_4 *)__env;
    int b = env->b;
    return (b + x);
}

static int __fn_5(void *__env, int x) {
    struct __env_5 *env = (struct __env_5 *)__env;
    int b = env->b;
    return ((b * 2) + x);
}

static int __fn_6(int x) {
    return (x + 3);
}
static int __fn_6_closure(void *__env, int x) {
    (void)__env;
    return __fn_6(x);
}

static int __fn_8(void *__env, int b) {
    struct __env_8 *env = (struct __env_8 *)__env;
    int a = env->a;
    return (a + b);
}

static Closure_i32_i32 __fn_7(int a) {
    struct __env_8 *__t2 = malloc(sizeof(struct __env_8));
    __t2->a = a;
    Closure_i32_i32 __t3 = {__t2, __fn_8};
    return __t3;
}
static Closure_i32_i32 __fn_7_closure(void *__env, int a) {
    (void)__env;
    return __fn_7(a);
}

Closure_i32_i32 make_adder(int x) {
    struct __env_3 *adder_env = malloc(sizeof(struct __env_3));
    adder_env->x = x;
    Closure_i32_i32 adder = {adder_env, __fn_3};
    return adder;
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
    int (*double)(int) = __fn_2;
    int (*d1)(int) = double;
    int (*d2)(int) = double;
    int r2 = d1(3);
    int r3 = d2(4);
    Closure_i32_i32 add5 = make_adder(5);
    int r4 = add5.fn(add5.env, 3);
    int b = 1;
    struct __env_4 *f1_env = malloc(sizeof(struct __env_4));
    f1_env->b = b;
    Closure_i32_i32 f1 = {f1_env, __fn_4};
    struct __env_5 *f2_env = malloc(sizeof(struct __env_5));
    f2_env->b = b;
    Closure_i32_i32 f2 = {f2_env, __fn_5};
    free(f2.env);
    f2 = f1;
    f1.env = NULL;
    int r5 = f2.fn(f2.env, 10);
    int (*add3)(int) = __fn_6;
    Closure_i32_i32 __t1 = {NULL, __fn_6_closure};
    int r6 = apply_twice(__t1, 5);
    Closure_i32_i32 (*add)(int) = __fn_7;
    int r7 = add(3)(4);
    free(f.env);
    free(g.env);
    free(add5.env);
    free(f1.env);
    free(f2.env);
    return 0;
}