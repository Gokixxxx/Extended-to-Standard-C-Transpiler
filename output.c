#include "option.h"
#include "vec.h"
#include "closure.h"

Option_i32 find_next(Vec_i32 arr, int target) {
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

static int __fn_2(int x) {
    return (x * 3);
}

static int __fn_3(int x) {
    return (x + 1);
}

int main() {
    int (*double_num)(int) = __fn_1;
    int result1 = double_num(5);
    int (*triple_num)(int) = __fn_2;
    int result2 = triple_num(4);
    int result3 = __fn_3(10);
    Vec_i32 nums = vec_new_i32();
    vec_push_i32(&nums, 1);
    vec_push_i32(&nums, 3);
    vec_push_i32(&nums, 5);
    vec_push_i32(&nums, 2);
    vec_push_i32(&nums, 4);
    int first = vec_get_i32(nums, 0);
    vec_set_i32(&nums, 1, 10);
    int len = vec_len_i32(nums);
    int target = 3;
    Option_i32 result4 = find_next(nums, target);
    int matched;
    if (result4.is_some) {
        matched = (result4.value * 10);
    } else {
        matched = 0;
    }
    int found = is_some(result4);
    int missing = is_none(result4);
    free(nums.data);
    return 0;
}