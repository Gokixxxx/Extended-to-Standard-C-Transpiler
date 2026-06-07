#include "option.h"
#include "vec.h"
#include "closure.h"

typedef struct {
    int min;
    int max;
} Range;

static int __fn_1(int n) {
    return (n * 2);
}
static int __fn_1_closure(void *__env, int n) {
    (void)__env;
    return __fn_1(n);
}

int Range_contains(Range *self, int x) {
    if ((x < (self)->min)) {
        return 0;
    }
    if ((x > (self)->max)) {
        return 0;
    }
    return 1;
}

Option_i32 find(Vec_i32 arr, int target) {
    Range range = (Range){target, 10};
    {
        int __t1 = 0;
        for (; __t1 < vec_len_i32(arr); __t1++) {
            int x = vec_get_i32(arr, __t1);
            if ((Range_contains(&(range), x) > 0)) {
                return Some_i32(x);
            }
        }
    }
    return None_i32();
}

int apply_twice(Closure_i32_i32 f, int x) {
    return f.fn(f.env, f.fn(f.env, x));
}

int main() {
    Vec_i32 v = vec_new_i32();
    vec_push_i32(&v, 1);
    vec_push_i32(&v, 2);
    vec_push_i32(&v, 3);
    vec_push_i32(&v, 4);
    vec_push_i32(&v, 5);
    
    int (*doubler)(int) = __fn_1;
    Closure_i32_i32 __t2 = {NULL, __fn_1_closure};
    int ans = apply_twice(__t2, 3);
    printf("%d\n", ans);
    vec_push_i32(&v, 6);
    vec_set_i32(&v, 3, 11);
    Option_i32 res = find(v, 4);
    int val;
    if (res.is_some) {
        val = res.value;
    } else {
        val = 0;
    }
    printf("%d\n", val);
    printf("%d\n", vec_len_i32(v));
    free(v.data);
    return 0;
}