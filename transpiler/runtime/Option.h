// option.h
#ifndef OPTION_H
#define OPTION_H

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

// Option<i32> 结构体，仅支持int
typedef struct {
    bool is_some;   // true: Some, false: None
    int  value;     // 仅当 is_some == true 时有效
} Option_i32;

static inline Option_i32 Some_i32(int val) {
    return (Option_i32){true, val};
}

static inline Option_i32 None_i32(void) {
    return (Option_i32){false, 0};
}

static inline bool is_some(Option_i32 opt) {
    return opt.is_some;
}

static inline bool is_none(Option_i32 opt) {
    return !opt.is_some;
}

static inline bool unwrap_i32(Option_i32 opt, int *out) {
    if (opt.is_some) {
        if (out) *out = opt.value;
        return true;
    }
    return false;
}

static inline int unwrap_or_i32(Option_i32 opt, int default_val) {
    return opt.is_some ? opt.value : default_val;
}

static inline int expect_i32(Option_i32 opt, const char *msg) {
    if (!opt.is_some) {
        fprintf(stderr, "panic: %s\n", msg ? msg : "called `expect` on a `None` value");
        exit(1);
    }
    return opt.value;
}

#endif