#include "vec.h"

int main() {
    Vec_i32 arr = vec_new_i32();
    vec_push_i32(&arr, 1);
    vec_push_i32(&arr, 3);
    vec_push_i32(&arr, 5);
    vec_push_i32(&arr, 2);
    vec_push_i32(&arr, 4);
    int max_val = 0;
    {
        int __t1 = 0;
        for (; __t1 < vec_len_i32(arr); __t1++) {
            int x = vec_get_i32(arr, __t1);
            if ((x > max_val)) {
                max_val = x;
            }
        }
    }
    int i = 0;
    while ((i < 3)) {
        i = (i + 1);
    }
    free(arr.data);
    return 0;
}