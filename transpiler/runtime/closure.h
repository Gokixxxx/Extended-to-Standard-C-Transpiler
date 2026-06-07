#ifndef CLOSURE_H
#define CLOSURE_H

// 命名规则：Closure_i32（0参数）或 Closure_i32 + "_i32" × 参数个数
// 例如：1个参数 → Closure_i32_i32，2个参数 → Closure_i32_i32_i32
// 注意：目前预定义最多支持 2 个 int 参数
// 3 个及以上参数需要 codegen.py 动态生成结构体定义

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
