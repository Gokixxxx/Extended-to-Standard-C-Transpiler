#include "option.h"
#include "vec.h"
#include "closure.h"

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

int main() {
    Vec_i32 v = vec_new_i32();
    vec_push_i32(&v, 1);
    vec_push_i32(&v, 2);
    vec_push_i32(&v, 3);
    vec_push_i32(&v, 4);
    vec_push_i32(&v, 5);
    Option_i32 res = find(v, 3);
    int val;
    if (res.is_some) {
        val = res.value;
    } else {
        val = 0;
    }
    printf("%d\n", val);
    free(v.data);
    return 0;
}