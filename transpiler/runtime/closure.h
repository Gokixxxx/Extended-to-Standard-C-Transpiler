#ifndef CLOSURE_H
#define CLOSURE_H

// 命名规则：Closure_{返回类型}_{参数类型1}_{参数类型2}...

// 0 个参数，返回 int
typedef struct {
    void *env;
    int (*fn)(void *env);
} Closure_i32;

// 1 个 int 参数，返回 int
typedef struct {
    void *env;
    int (*fn)(void *env, int);
} Closure_i32_i32;

// 2 个 int 参数，返回 int
typedef struct {
    void *env;
    int (*fn)(void *env, int, int);
} Closure_i32_i32_i32;

#endif
