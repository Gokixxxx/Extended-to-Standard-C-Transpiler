#include "vec.h"

int mytest(void) {
    Vec_i32 v = vec_new_i32();
    vec_push_i32(&v, 1);
    vec_push_i32(&v, 2);
    vec_push_i32(&v, 3);
    vec_set_i32(&v, 1, 99);
    int x = vec_get_i32(v, 1);
    free(v.data);
}

int main() {
    return 0;
}