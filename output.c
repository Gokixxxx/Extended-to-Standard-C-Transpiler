#include "option.h"
#include "vec.h"
#include "closure.h"

typedef struct {
                void *env;
                Closure_i32_i32 (*fn)(void *env, int);
            } Closure_Closure_i32_i32__i32;

struct __env_5 {
    int a;
};

struct __env_8 {
    int x;
    int factor;
};

struct __env_7 {
    int factor;
};

struct __env_9 {
    int outer;
};

struct __env_11 {
    int base;
    int a;
};

struct __env_10 {
    int base;
};

struct __env_13 {
    int x;
};

struct __env_14 {
    int x;
};

struct __env_15 {
    int j;
};

struct __env_16 {
    int i;
};

struct __env_17 {
    int flag;
};

static int __fn_1(int x) {
    return (x * 2);
}

static int __fn_2(int x) {
    return (x * 3);
}

static int __fn_3(int x, int y) {
    return (x + y);
}

static int __fn_5(void *__env, int b) {
    struct __env_5 *env = (struct __env_5 *)__env;
    int a = env->a;
    return (a + b);
}

static Closure_i32_i32 __fn_4(int a) {
    struct __env_5 *__t1 = malloc(sizeof(struct __env_5));
    __t1->a = a;
    Closure_i32_i32 __t2 = {__t1, __fn_5};
    return __t2;
}

static int __fn_8(void *__env, int y) {
    struct __env_8 *env = (struct __env_8 *)__env;
    int x = env->x;
    int factor = env->factor;
    return ((x * y) * factor);
}

static Closure_i32_i32 __fn_7(void *__env, int x) {
    struct __env_7 *env = (struct __env_7 *)__env;
    int factor = env->factor;
    struct __env_8 *__t4 = malloc(sizeof(struct __env_8));
    __t4->x = x;
    __t4->factor = factor;
    Closure_i32_i32 __t5 = {__t4, __fn_8};
    return __t5;
}

static Closure_Closure_i32_i32__i32 __fn_6(int factor) {
    struct __env_7 *__t6 = malloc(sizeof(struct __env_7));
    __t6->factor = factor;
    Closure_Closure_i32_i32__i32 __t7 = {__t6, __fn_7};
    return __t7;
}

static int __fn_9(void *__env, int x) {
    struct __env_9 *env = (struct __env_9 *)__env;
    int outer = env->outer;
    return (outer + x);
}

static int __fn_11(void *__env, int b) {
    struct __env_11 *env = (struct __env_11 *)__env;
    int base = env->base;
    int a = env->a;
    return ((base + a) + b);
}

static Closure_i32_i32 __fn_10(void *__env, int a) {
    struct __env_10 *env = (struct __env_10 *)__env;
    int base = env->base;
    struct __env_11 *__t8 = malloc(sizeof(struct __env_11));
    __t8->base = base;
    __t8->a = a;
    Closure_i32_i32 __t9 = {__t8, __fn_11};
    return __t9;
}

static int __fn_12(int y) {
    return (y + 3);
}

static int __fn_13(void *__env, int a) {
    struct __env_13 *env = (struct __env_13 *)__env;
    int x = env->x;
    return (x + a);
}

static int __fn_14(void *__env, int b) {
    struct __env_14 *env = (struct __env_14 *)__env;
    int x = env->x;
    return (x * b);
}

static int __fn_15(void *__env) {
    struct __env_15 *env = (struct __env_15 *)__env;
    int j = env->j;
    return j;
}

static int __fn_16(void *__env) {
    struct __env_16 *env = (struct __env_16 *)__env;
    int i = env->i;
    return i;
}

static int __fn_17(void *__env) {
    struct __env_17 *env = (struct __env_17 *)__env;
    int flag = env->flag;
    return flag;
}

static int __fn_18(void) {
    return 42;
}

int apply_twice(Closure_i32_i32 f, int x) {
    return f.fn(f.env, f.fn(f.env, x));
}

int main() {
    int (*doubled)(int) = __fn_1;
    int r1 = doubled(10);
    int (*triple)(int) = __fn_2;
    int r2 = triple(5);
    int (*add)(int, int) = __fn_3;
    int r3 = add(3, 4);
    Closure_i32_i32 (*make_adder)(int) = __fn_4;
    Closure_i32_i32 add5 = make_adder(5);
    int r4 = add5.fn(add5.env, 3);
    Closure_i32_i32 __t3 = make_adder(10);
    int r5 = __t3.fn(__t3.env, 2);
    Closure_Closure_i32_i32__i32 (*make_multiplier)(int) = __fn_6;
    Closure_Closure_i32_i32__i32 m2 = make_multiplier(2);
    Closure_i32_i32 m2x3 = m2.fn(m2.env, 3);
    int r6 = m2x3.fn(m2x3.env, 4);
    int outer = 100;
    struct __env_9 *capture_test_env = malloc(sizeof(struct __env_9));
    capture_test_env->outer = outer;
    Closure_i32_i32 capture_test = {capture_test_env, __fn_9};
    int r7 = capture_test.fn(capture_test.env, 1);
    int base = 10;
    struct __env_10 *make_complex_env = malloc(sizeof(struct __env_10));
    make_complex_env->base = base;
    Closure_Closure_i32_i32__i32 make_complex = {make_complex_env, __fn_10};
    Closure_i32_i32 __t10 = make_complex.fn(make_complex.env, 3);
    int r8 = __t10.fn(__t10.env, 4);
    int (*add3)(int) = __fn_12;
    Closure_i32_i32 __t11 = {NULL, add3};
    int r9 = apply_twice(__t11, 5);
    int x = 10;
    if ((x > 5)) {
        struct __env_13 *f_env = malloc(sizeof(struct __env_13));
        f_env->x = x;
        Closure_i32_i32 f = {f_env, __fn_13};
        int r10 = f.fn(f.env, 1);
        free(f.env);
    }
    else {
        struct __env_14 *g_env = malloc(sizeof(struct __env_14));
        g_env->x = x;
        Closure_i32_i32 g = {g_env, __fn_14};
        int r10 = g.fn(g.env, 2);
        free(g.env);
    }
    Vec_i32 arr = vec_new_i32();
    vec_push_i32(&arr, 1);
    vec_push_i32(&arr, 2);
    vec_push_i32(&arr, 3);
    int sum = 0;
    {
        int __t12 = 0;
        for (; __t12 < vec_len_i32(arr); __t12++) {
            int j = vec_get_i32(arr, __t12);
            struct __env_15 *f_env = malloc(sizeof(struct __env_15));
            f_env->j = j;
            Closure_i32 f = {f_env, __fn_15};
            int r = f.fn(f.env);
            sum = (sum + r);
            free(f.env);
        }
    }
    int i = 0;
    int wsum = 0;
    while ((i < 3)) {
        struct __env_16 *f_env = malloc(sizeof(struct __env_16));
        f_env->i = i;
        Closure_i32 f = {f_env, __fn_16};
        int r = f.fn(f.env);
        wsum = (wsum + r);
        i = (i + 1);
        free(f.env);
    }
    int flag = 1;
    if ((flag > 0)) {
        if ((flag > 0)) {
            struct __env_17 *f_env = malloc(sizeof(struct __env_17));
            f_env->flag = flag;
            Closure_i32 f = {f_env, __fn_17};
            int r13 = f.fn(f.env);
            free(f.env);
        }
    }
    int (*get42)(void) = __fn_18;
    int r14 = get42();
    free(arr.data);
    free(__t3.env);
    free(__t10.env);
    free(add5.env);
    free(m2.env);
    free(m2x3.env);
    free(capture_test.env);
    free(make_complex.env);
    return 0;
}