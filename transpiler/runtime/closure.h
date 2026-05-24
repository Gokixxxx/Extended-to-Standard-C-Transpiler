#ifndef CLOSURE_H
#define CLOSURE_H

// 闭包结构体：按签名特化，保留类型信息，避免完全擦除为 void*
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
