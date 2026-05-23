#include "option.h"

#include "vec.h"

int mytest(void) {
    Vec_i32 v = vec_new_i32();
    vec_push_i32(&v, 1);
    vec_push_i32(&v, 2);
    vec_push_i32(&v, 3);
    Option_i32 x = Some_i32(5);
    int y;
    if (x.is_some) {
        y = ((x.value * 2) + 1);
    } else {
        y = 0;
    }
    free(v.data);
}

int main() {
    return 0;
}