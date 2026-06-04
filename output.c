#include "option.h"
#include "vec.h"
#include "closure.h"

void mytest(void) {
    Vec_i32 v = vec_new_i32();
    vec_push_i32(&v, 1);
    vec_push_i32(&v, 2);
    vec_push_i32(&v, 3);
    vec_push_i32(&v, 4);
    vec_set_i32(&v, 1, 99);
    int a = vec_get_i32(v, 1);
    int b = vec_len_i32(v);
    int c = vec_pop_i32(&v);
    vec_remove_i32(&v, 0);
    free(v.data);
}

int main() {
    mytest();
    return 0;
}