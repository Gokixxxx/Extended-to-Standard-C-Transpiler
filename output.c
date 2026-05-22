#include "option.h"

Option_i32 find(int target) {
    if ((target < 3)) {
        return Some_i32(5);
    }
    return None_i32();
}

int main() {
    Option_i32 result1 = find(3);
    int val1;
    if (result1.is_some) {
        val1 = result1.value;
    } else {
        val1 = 0;
    }
    Option_i32 result2 = find(1);
    int val2;
    if (result2.is_some) {
        val2 = result2.value;
    } else {
        val2 = 0;
    }
    return 0;
}