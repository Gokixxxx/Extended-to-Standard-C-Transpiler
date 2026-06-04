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

void mytest(void) {
    Vec_i32 __t2 = vec_new_i32();
    vec_push_i32(&__t2, 1);
    vec_push_i32(&__t2, 3);
    vec_push_i32(&__t2, 5);
    vec_push_i32(&__t2, 2);
    vec_push_i32(&__t2, 4);
    Option_i32 result1 = find(__t2, 3);
    Vec_i32 __t3 = vec_new_i32();
    vec_push_i32(&__t3, 1);
    vec_push_i32(&__t3, 2);
    vec_push_i32(&__t3, 3);
    Option_i32 result2 = find(__t3, 5);
}

int main() {
    mytest();
    return 0;
}