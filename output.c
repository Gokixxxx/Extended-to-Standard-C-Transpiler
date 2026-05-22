#include "vec.h"

int main() {
    Vec_i32 v = vec_new_i32();
    vec_push_i32(&v, 1);
    vec_push_i32(&v, 2);
    vec_push_i32(&v, 3);
    vec_push_i32(&v, 16);
    int k = vec_get_i32(v, 1);
    int n = vec_len_i32(v);
    int p = vec_pop_i32(&v);
    vec_remove_i32(&v, 0);
    free(v.data);
    return 0;
}