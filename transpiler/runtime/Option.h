// option.h
#ifndef OPTION_H
#define OPTION_H

#include <stdbool.h>

// Option<i32> 结构体，支持整数类型
typedef struct {
    bool is_some;
    int value;
} Option_i32;

static inline Option_i32 Some_i32(int val) {
    Option_i32 opt = {true, val};
    return opt;
}

static inline Option_i32 None_i32() {
    Option_i32 opt = {false, 0};
    return opt;
}

#endif