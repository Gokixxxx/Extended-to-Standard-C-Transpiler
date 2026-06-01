#include "option.h"
#include "vec.h"
#include "closure.h"

struct __env_1 {
    int a;
};

typedef struct {
    int width;
    int height;
} Rectangle;

static int __fn_1(void *__env, int b) {
    struct __env_1 *env = (struct __env_1 *)__env;
    int a = env->a;
    return (a + b);
}

int doubled(int x) {
    return (x * 2);
}

Closure_i32_i32 add(int a) {
    struct __env_1 *ret_env = malloc(sizeof(struct __env_1));
    ret_env->a = a;
    Closure_i32_i32 ret = {ret_env, __fn_1};
    return ret;
}

int Rectangle_area(Rectangle *self) {
    return ((self)->width * (self)->height);
}

int main() {
    int x = 10;
    printf("%d\n", x);
    printf("%d\n", (x + 5));
    printf("%d\n", doubled(7));
    Closure_i32_i32 f = add(3);
    printf("%d\n", f.fn(f.env, 4));
    
    Rectangle rect = (Rectangle){5, 6};
    printf("%d\n", Rectangle_area(&(rect)));
    Option_i32 opt = Some_i32(42);
    int val;
    if (opt.is_some) {
        val = opt.value;
    } else {
        val = 0;
    }
    printf("%d\n", val);
    free(f.env);
    return 0;
}