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
    int x1;
    int y1;
    int a;
};

struct __env_3 {
    int x1;
    int y1;
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

struct __env_12 {
    int base;
};

struct __env_13 {
    int base;
};

struct __env_15 {
    int j;
};

struct __env_16 {
    int i1;
};

struct __env_17 {
    int x2;
};

struct __env_18 {
    int x2;
};

struct __env_19 {
    int flag;
};

struct __env_21 {
    int j;
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
static Closure_i32_i32 __fn_1_closure(void *__env, int a) {
    (void)__env;
    return __fn_1(a);
}

static int __fn_4(void *__env, int b) {
    struct __env_4 *env = (struct __env_4 *)__env;
    int x1 = env->x1;
    int y1 = env->y1;
    int a = env->a;
    return (((x1 + y1) + a) + b);
}

static Closure_i32_i32 __fn_3(void *__env, int a) {
    struct __env_3 *env = (struct __env_3 *)__env;
    int x1 = env->x1;
    int y1 = env->y1;
    struct __env_4 *__t4 = malloc(sizeof(struct __env_4));
    __t4->x1 = x1;
    __t4->y1 = y1;
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
static Closure_Closure_i32_i32__i32 __fn_5_closure(void *__env, int a) {
    (void)__env;
    return __fn_5(a);
}

static int __fn_8(void *__env, int x) {
    struct __env_8 *env = (struct __env_8 *)__env;
    int base = env->base;
    return (base + x);
}

static int __fn_9(int n) {
    return (n * 2);
}
static int __fn_9_closure(void *__env, int n) {
    (void)__env;
    return __fn_9(n);
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

static int __fn_12(void *__env, int x) {
    struct __env_12 *env = (struct __env_12 *)__env;
    int base = env->base;
    return (base + x);
}

static int __fn_13(void *__env, int x) {
    struct __env_13 *env = (struct __env_13 *)__env;
    int base = env->base;
    return (base + x);
}

static int __fn_14(int n) {
    return (n * 2);
}
static int __fn_14_closure(void *__env, int n) {
    (void)__env;
    return __fn_14(n);
}

static int __fn_15(void *__env) {
    struct __env_15 *env = (struct __env_15 *)__env;
    int j = env->j;
    return j;
}

static int __fn_16(void *__env) {
    struct __env_16 *env = (struct __env_16 *)__env;
    int i1 = env->i1;
    return i1;
}

static int __fn_17(void *__env, int a) {
    struct __env_17 *env = (struct __env_17 *)__env;
    int x2 = env->x2;
    return (x2 + a);
}

static int __fn_18(void *__env, int b) {
    struct __env_18 *env = (struct __env_18 *)__env;
    int x2 = env->x2;
    return (x2 * b);
}

static int __fn_19(void *__env) {
    struct __env_19 *env = (struct __env_19 *)__env;
    int flag = env->flag;
    return flag;
}

static int __fn_20(void) {
    return 42;
}
static int __fn_20_closure(void *__env) {
    (void)__env;
    return __fn_20();
}

static int __fn_21(void *__env) {
    struct __env_21 *env = (struct __env_21 *)__env;
    int j = env->j;
    return j;
}

Closure_i32_i32 make_adder1(int base) {
    struct __env_8 *__t13 = malloc(sizeof(struct __env_8));
    __t13->base = base;
    Closure_i32_i32 __t14 = {__t13, __fn_8};
    return __t14;
}

int apply_twice(Closure_i32_i32 f, int x) {
    return f.fn(f.env, f.fn(f.env, x));
}

Closure_i32_i32 make_multiplier(int factor) {
    struct __env_10 *__t16 = malloc(sizeof(struct __env_10));
    __t16->factor = factor;
    Closure_i32_i32 __t17 = {__t16, __fn_10};
    return __t17;
}

Closure_i32_i32 make_offset_adder(int base, int delta) {
    struct __env_11 *__t18 = malloc(sizeof(struct __env_11));
    __t18->base = base;
    __t18->delta = delta;
    Closure_i32_i32 __t19 = {__t18, __fn_11};
    return __t19;
}

Closure_i32_i32 make_adder2(int base) {
    struct __env_12 *__t20 = malloc(sizeof(struct __env_12));
    __t20->base = base;
    Closure_i32_i32 __t21 = {__t20, __fn_12};
    return __t21;
}

int plain_add(int a, int b) {
    return (a + b);
}

Closure_i32_i32 make_adder3(int base) {
    struct __env_13 *__t22 = malloc(sizeof(struct __env_13));
    __t22->base = base;
    Closure_i32_i32 __t23 = {__t22, __fn_13};
    return __t23;
}

int apply_twice2(Closure_i32_i32 f, int x) {
    return f.fn(f.env, f.fn(f.env, x));
}

int main() {
    Closure_i32_i32 (*add)(int) = __fn_1;
    Closure_i32_i32 __t3 = add(3);
    int r1 = __t3.fn(__t3.env, 4);
    int x1 = 1;
    int y1 = 2;
    struct __env_3 *f1_env = malloc(sizeof(struct __env_3));
    f1_env->x1 = x1;
    f1_env->y1 = y1;
    Closure_Closure_i32_i32__i32 f1 = {f1_env, __fn_3};
    Closure_i32_i32 __t6 = f1.fn(f1.env, 3);
    int r2 = __t6.fn(__t6.env, 4);
    Closure_Closure_i32_i32__i32 (*triple)(int) = __fn_5;
    Closure_Closure_i32_i32__i32 __t11 = triple(1);
    Closure_i32_i32 __t12 = __t11.fn(__t11.env, 2);
    int r3 = __t12.fn(__t12.env, 3);
    Closure_i32_i32 add10 = make_adder1(10);
    int r4 = add10.fn(add10.env, 5);
    int (*doubled)(int) = __fn_9;
    Closure_i32_i32 __t15 = {NULL, __fn_9_closure};
    int r5 = apply_twice(__t15, 3);
    Closure_i32_i32 triple_fn = make_multiplier(3);
    int r6 = triple_fn.fn(triple_fn.env, 7);
    Closure_i32_i32 add_150 = make_offset_adder(100, 50);
    int r7 = add_150.fn(add_150.env, 7);
    Closure_i32_i32 add5 = make_adder2(5);
    Closure_i32_i32 add100 = make_adder2(100);
    int r8 = add5.fn(add5.env, 3);
    int r9 = add100.fn(add100.env, 3);
    int a1 = plain_add(2, 3);
    Closure_i32_i32 add10b = make_adder3(10);
    int b1 = add10b.fn(add10b.env, 5);
    int (*doubled2)(int) = __fn_14;
    Closure_i32_i32 __t24 = {NULL, __fn_14_closure};
    int c1 = apply_twice2(__t24, 4);
    Vec_i32 arr1 = vec_new_i32();
    vec_push_i32(&arr1, 1);
    vec_push_i32(&arr1, 2);
    vec_push_i32(&arr1, 3);
    int sum1 = 0;
    {
        int __t25 = 0;
        for (; __t25 < vec_len_i32(arr1); __t25++) {
            int j = vec_get_i32(arr1, __t25);
            struct __env_15 *f2_env = malloc(sizeof(struct __env_15));
            f2_env->j = j;
            Closure_i32 f2 = {f2_env, __fn_15};
            int r10 = f2.fn(f2.env);
            sum1 = (sum1 + r10);
            free(f2.env);
        }
    }
    int r11 = sum1;
    int i1 = 0;
    int wsum = 0;
    while ((i1 < 3)) {
        struct __env_16 *f3_env = malloc(sizeof(struct __env_16));
        f3_env->i1 = i1;
        Closure_i32 f3 = {f3_env, __fn_16};
        int r12 = f3.fn(f3.env);
        wsum = (wsum + r12);
        i1 = (i1 + 1);
        free(f3.env);
    }
    int r13 = wsum;
    int x2 = 10;
    int r14 = 0;
    if ((x2 > 5)) {
        struct __env_17 *f4_env = malloc(sizeof(struct __env_17));
        f4_env->x2 = x2;
        Closure_i32_i32 f4 = {f4_env, __fn_17};
        r14 = f4.fn(f4.env, 1);
        free(f4.env);
    }
    else {
        struct __env_18 *g1_env = malloc(sizeof(struct __env_18));
        g1_env->x2 = x2;
        Closure_i32_i32 g1 = {g1_env, __fn_18};
        r14 = g1.fn(g1.env, 2);
        free(g1.env);
    }
    int flag = 1;
    int r15 = 0;
    if ((flag > 0)) {
        if ((flag > 0)) {
            struct __env_19 *f5_env = malloc(sizeof(struct __env_19));
            f5_env->flag = flag;
            Closure_i32 f5 = {f5_env, __fn_19};
            r15 = f5.fn(f5.env);
            free(f5.env);
        }
    }
    int (*get42)(void) = __fn_20;
    int r16 = get42();
    Vec_i32 arr2 = vec_new_i32();
    vec_push_i32(&arr2, 1);
    vec_push_i32(&arr2, 2);
    vec_push_i32(&arr2, 3);
    int sum2 = 0;
    {
        int __t26 = 0;
        for (; __t26 < vec_len_i32(arr2); __t26++) {
            int j = vec_get_i32(arr2, __t26);
            struct __env_21 *f7_env = malloc(sizeof(struct __env_21));
            f7_env->j = j;
            Closure_i32 f7 = {f7_env, __fn_21};
            sum2 = (sum2 + f7.fn(f7.env));
            free(f7.env);
        }
    }
    int r18 = sum2;
    free(arr1.data);
    free(arr2.data);
    free(__t3.env);
    free(__t6.env);
    free(__t11.env);
    free(__t12.env);
    free(f1.env);
    free(add10.env);
    free(triple_fn.env);
    free(add_150.env);
    free(add5.env);
    free(add100.env);
    free(add10b.env);
    return 0;
}