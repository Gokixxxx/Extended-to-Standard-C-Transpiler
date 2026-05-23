#include "option.h"
#include "vec.h"

Option_i32 find(Vec_i32 arr, int target) {
    {
        int __t1 = 0;
        for (; __t1 < vec_len_i32(arr); __t1++) {
            int x = vec_get_i32(arr, __t1);
            if ((x > target)) {
                return Some_i32(x);
            }
        }
    }
    return None_i32();
}

static int __fn_1(int x) {
    return (x * 2);
}

int main() {
    int (*double_num)(int) = __fn_1;
    int result = double_num(2);
    Vec_i32 g = vec_new_i32();
    vec_push_i32(&g, 1);
    vec_push_i32(&g, 3);
    vec_push_i32(&g, 5);
    vec_push_i32(&g, 2);
    vec_push_i32(&g, 4);
    Option_i32 result1 = find(g, result);
    free(g.data);
    return 0;
}