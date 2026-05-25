#include "option.h"
#include "vec.h"
#include "closure.h"

typedef struct {
                void *env;
                Closure_i32_i32 (*fn)(void *env, int);
            } Closure_Closure_i32_i32__i32;

struct __env_2 {
    int a;
};

struct __env_4 {
    int x;
    int y;
    int a;
};

struct __env_3 {
    int x;
    int y;
};

struct __env_7 {
    int a;
    int b;
};

struct __env_6 {
    int a;
};

struct __env_8 {
    int base;
};

struct __env_10 {
    int factor;
};

struct __env_11 {
    int base;
    int delta;
};

Closure_i32_i32 make_adder(int base) {
    struct __env_8 *__t13 = malloc(sizeof(struct __env_8));
    __t13->base = base;
    Closure_i32_i32 __t14 = {__t13, __fn_8};
    return __t14;
}

int apply_twice(int (*f)(int), int x) {
    return f(f(x));
}

Closure_i32_i32 make_multiplier(int factor) {
    struct __env_10 *__t15 = malloc(sizeof(struct __env_10));
    __t15->factor = factor;
    Closure_i32_i32 __t16 = {__t15, __fn_10};
    return __t16;
}

Closure_i32_i32 make_offset_adder(int base, int delta) {
    struct __env_11 *__t17 = malloc(sizeof(struct __env_11));
    __t17->base = base;
    __t17->delta = delta;
    Closure_i32_i32 __t18 = {__t17, __fn_11};
    return __t18;
}

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

static int __fn_4(void *__env, int b) {
    struct __env_4 *env = (struct __env_4 *)__env;
    int x = env->x;
    int y = env->y;
    int a = env->a;
    return (((x + y) + a) + b);
}

static Closure_i32_i32 __fn_3(void *__env, int a) {
    struct __env_3 *env = (struct __env_3 *)__env;
    int x = env->x;
    int y = env->y;
    struct __env_4 *__t4 = malloc(sizeof(struct __env_4));
    __t4->x = x;
    __t4->y = y;
    __t4->a = a;
    Closure_i32_i32 __t5 = {__t4, __fn_4};
    return __t5;
}

static int __fn_7(void *__env, int c) {
    struct __env_7 *env = (struct __env_7 *)__env;
    int a = env->a;
    int b = env->b;
    return ((a + b) + c);
}

static Closure_i32_i32 __fn_6(void *__env, int b) {
    struct __env_6 *env = (struct __env_6 *)__env;
    int a = env->a;
    struct __env_7 *__t7 = malloc(sizeof(struct __env_7));
    __t7->a = a;
    __t7->b = b;
    Closure_i32_i32 __t8 = {__t7, __fn_7};
    return __t8;
}

static Closure_Closure_i32_i32__i32 __fn_5(int a) {
    struct __env_6 *__t9 = malloc(sizeof(struct __env_6));
    __t9->a = a;
    Closure_Closure_i32_i32__i32 __t10 = {__t9, __fn_6};
    return __t10;
}

static int __fn_8(void *__env, int x) {
    struct __env_8 *env = (struct __env_8 *)__env;
    int base = env->base;
    return (base + x);
}

static int __fn_9(int n) {
    return (n * 2);
}

static int __fn_10(void *__env, int x) {
    struct __env_10 *env = (struct __env_10 *)__env;
    int factor = env->factor;
    return (x * factor);
}

static int __fn_11(void *__env, int x) {
    struct __env_11 *env = (struct __env_11 *)__env;
    int base = env->base;
    int delta = env->delta;
    return ((base + delta) + x);
}

int main() {
    Closure_i32_i32 (*add)(int) = __fn_1;
    Closure_i32_i32 __t3 = add(3);
    int result1 = __t3.fn(__t3.env, 4);
    int x = 1;
    int y = 2;
    struct __env_3 *f_env = malloc(sizeof(struct __env_3));
    f_env->x = x;
    f_env->y = y;
    Closure_Closure_i32_i32__i32 f = {f_env, __fn_3};
    Closure_i32_i32 __t6 = f.fn(f.env, 3);
    int result2 = __t6.fn(__t6.env, 4);
    Closure_Closure_i32_i32__i32 (*triple)(int) = __fn_5;
    Closure_Closure_i32_i32__i32 __t11 = triple(1);
    Closure_i32_i32 __t12 = __t11.fn(__t11.env, 2);
    int result3 = __t12.fn(__t12.env, 3);
    Closure_i32_i32 add10 = make_adder(10);
    int result4 = add10.fn(add10.env, 5);
    int (*doubled)(int) = __fn_9;
    int result5 = apply_twice(doubled, 3);
    Closure_i32_i32 triple_fn = make_multiplier(3);
    int result6 = triple_fn.fn(triple_fn.env, 7);
    Closure_i32_i32 add_150 = make_offset_adder(100, 50);
    int result7 = add_150.fn(add_150.env, 7);
    free(f_env);
    free(__t3.env);
    free(__t6.env);
    free(__t11.env);
    free(__t12.env);
    return 0;
}