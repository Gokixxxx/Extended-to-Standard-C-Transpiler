#include "option.h"
#include "vec.h"
#include "closure.h"

struct __env_3 {
    int a;
};

typedef struct {
    int x;
    int y;
} Point;

typedef struct {
    int width;
    int height;
} Rectangle;

static Rectangle __fn_1(int w, int h) {
    return (Rectangle){w, h};
}
static Rectangle __fn_1_closure(void *__env, int w, int h) {
    (void)__env;
    return __fn_1(w, h);
}

static int __fn_3(void *__env, int b) {
    struct __env_3 *env = (struct __env_3 *)__env;
    int a = env->a;
    return (a + b);
}

static Closure_i32_i32 __fn_2(int a) {
    struct __env_3 *__t1 = malloc(sizeof(struct __env_3));
    __t1->a = a;
    Closure_i32_i32 __t2 = {__t1, __fn_3};
    return __t2;
}
static Closure_i32_i32 __fn_2_closure(void *__env, int a) {
    (void)__env;
    return __fn_2(a);
}

int Point_distance_sq(Point *self) {
    return (((self)->x * (self)->x) + ((self)->y * (self)->y));
}

int Rectangle_area(Rectangle *self) {
    return ((self)->width * (self)->height);
}

int Rectangle_scale(Rectangle *self, int factor) {
    return ((self)->width * factor);
}

int Rectangle_perimeter(Rectangle *self) {
    return (2 * ((self)->width + (self)->height));
}

int main() {
    
    
    Point p = (Point){3, 4};
    int d = Point_distance_sq(&(p));
    Rectangle rect1 = (Rectangle){30, 50};
    int a1 = Rectangle_area(&(rect1));
    int s1 = Rectangle_scale(&(rect1), 2);
    int p1 = Rectangle_perimeter(&(rect1));
    Rectangle rect2 = (Rectangle){10, 20};
    Vec_i32 v = vec_new_i32();
    vec_push_i32(&v, Rectangle_area(&(rect1)));
    vec_push_i32(&v, Rectangle_perimeter(&(rect2)));
    vec_push_i32(&v, s1);
    Option_i32 opt = Some_i32(Rectangle_area(&(rect1)));
    int result;
    if (opt.is_some) {
        result = (opt.value + 1);
    } else {
        result = 0;
    }
    Rectangle (*make_rect)(int, int) = __fn_1;
    Rectangle r3 = make_rect(5, 6);
    int a3 = Rectangle_area(&(r3));
    Closure_i32_i32 (*adder)(int) = __fn_2;
    Closure_i32_i32 add5 = adder(5);
    int add5_result = add5.fn(add5.env, 10);
    free(v.data);
    free(add5.env);
    return 0;
}