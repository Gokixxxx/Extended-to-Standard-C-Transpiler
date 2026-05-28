#include "option.h"
#include "vec.h"
#include "closure.h"

typedef struct {
                void *env;
                Closure_i32_i32 (*fn)(void *env, int);
            } Closure_Closure_i32_i32__i32;

struct __env_1 {
    int base;
};

struct __env_2 {
    int offset;
};

struct __env_3 {
    int a3;
};

struct __env_4 {
    int b3;
};

struct __env_5 {
    int d;
};

struct __env_7 {
    int e;
    int a;
};

struct __env_6 {
    int e;
};

struct __env_8 {
    int base6;
};

struct __env_9 {
    int base6;
};

struct __env_10 {
    int base6;
};

struct __env_11 {
    int loop_base;
};

static int __fn_1(void *__env, int x) {
    struct __env_1 *env = (struct __env_1 *)__env;
    int base = env->base;
    return (base + x);
}

static int __fn_2(void *__env, int y) {
    struct __env_2 *env = (struct __env_2 *)__env;
    int offset = env->offset;
    return (offset + y);
}

static int __fn_3(void *__env, int x) {
    struct __env_3 *env = (struct __env_3 *)__env;
    int a3 = env->a3;
    return (a3 + x);
}

static int __fn_4(void *__env, int x) {
    struct __env_4 *env = (struct __env_4 *)__env;
    int b3 = env->b3;
    return (b3 + x);
}

static int __fn_5(void *__env, int x) {
    struct __env_5 *env = (struct __env_5 *)__env;
    int d = env->d;
    return (d + x);
}

static int __fn_7(void *__env, int b) {
    struct __env_7 *env = (struct __env_7 *)__env;
    int e = env->e;
    int a = env->a;
    return ((e + a) + b);
}

static Closure_i32_i32 __fn_6(void *__env, int a) {
    struct __env_6 *env = (struct __env_6 *)__env;
    int e = env->e;
    struct __env_7 *__t1 = malloc(sizeof(struct __env_7));
    __t1->e = e;
    __t1->a = a;
    Closure_i32_i32 __t2 = {__t1, __fn_7};
    return __t2;
}

static int __fn_8(void *__env, int x) {
    struct __env_8 *env = (struct __env_8 *)__env;
    int base6 = env->base6;
    return (base6 + x);
}

static int __fn_9(void *__env, int x) {
    struct __env_9 *env = (struct __env_9 *)__env;
    int base6 = env->base6;
    return (base6 + x);
}

static int __fn_10(void *__env, int x) {
    struct __env_10 *env = (struct __env_10 *)__env;
    int base6 = env->base6;
    return (base6 + x);
}

static int __fn_11(void *__env, int x) {
    struct __env_11 *env = (struct __env_11 *)__env;
    int loop_base = env->loop_base;
    return (loop_base + x);
}

Closure_i32_i32 make_adder(int offset) {
    struct __env_2 *inner_env = malloc(sizeof(struct __env_2));
    inner_env->offset = offset;
    Closure_i32_i32 inner = {inner_env, __fn_2};
    inner.env = NULL;
    return inner;
}

int main() {
    int base = 10;
    struct __env_1 *f1_env = malloc(sizeof(struct __env_1));
    f1_env->base = base;
    Closure_i32_i32 f1 = {f1_env, __fn_1};
    Closure_i32_i32 g1 = f1;
    f1.env = NULL;
    int r1 = g1.fn(g1.env, 5);
    Closure_i32_i32 add5 = make_adder(5);
    int r2 = add5.fn(add5.env, 3);
    int a3 = 1;
    struct __env_3 *h_env = malloc(sizeof(struct __env_3));
    h_env->a3 = a3;
    Closure_i32_i32 h = {h_env, __fn_3};
    int b3 = 2;
    struct __env_4 *k_env = malloc(sizeof(struct __env_4));
    k_env->b3 = b3;
    Closure_i32_i32 k = {k_env, __fn_4};
    free(h.env);
    h = k;
    k.env = NULL;
    int r3 = h.fn(h.env, 10);
    int d = 100;
    struct __env_5 *m_env = malloc(sizeof(struct __env_5));
    m_env->d = d;
    Closure_i32_i32 m = {m_env, __fn_5};
    Closure_i32_i32 n = m;
    m.env = NULL;
    Closure_i32_i32 p = n;
    n.env = NULL;
    int r4 = p.fn(p.env, 1);
    int e = 7;
    struct __env_6 *outer_env = malloc(sizeof(struct __env_6));
    outer_env->e = e;
    Closure_Closure_i32_i32__i32 outer = {outer_env, __fn_6};
    Closure_i32_i32 mid = outer.fn(outer.env, 3);
    Closure_i32_i32 final = mid;
    mid.env = NULL;
    int r5 = final.fn(final.env, 4);
    int cond = 1;
    int base6 = 20;
    struct __env_8 *branch_fn_env = malloc(sizeof(struct __env_8));
    branch_fn_env->base6 = base6;
    Closure_i32_i32 branch_fn = {branch_fn_env, __fn_8};
    struct __env_9 *moved_env = malloc(sizeof(struct __env_9));
    moved_env->base6 = base6;
    Closure_i32_i32 moved = {moved_env, __fn_9};
    if ((cond > 0)) {
        free(moved.env);
        moved = branch_fn;
        branch_fn.env = NULL;
    }
    else {
        struct __env_10 *alt_env = malloc(sizeof(struct __env_10));
        alt_env->base6 = base6;
        Closure_i32_i32 alt = {alt_env, __fn_10};
        free(moved.env);
        moved = alt;
        alt.env = NULL;
        free(alt.env);
    }
    int r6 = moved.fn(moved.env, 2);
    int loop_base = 0;
    struct __env_11 *loop_fn_env = malloc(sizeof(struct __env_11));
    loop_fn_env->loop_base = loop_base;
    Closure_i32_i32 loop_fn = {loop_fn_env, __fn_11};
    Closure_i32_i32 saved = loop_fn;
    loop_fn.env = NULL;
    int r7 = saved.fn(saved.env, 99);
    free(f1.env);
    free(g1.env);
    free(add5.env);
    free(h.env);
    free(k.env);
    free(m.env);
    free(n.env);
    free(p.env);
    free(outer.env);
    free(mid.env);
    free(final.env);
    free(branch_fn.env);
    free(moved.env);
    free(loop_fn.env);
    free(saved.env);
    return 0;
}