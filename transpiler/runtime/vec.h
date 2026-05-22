// vec.h
#ifndef VEC_H
#define VEC_H

#include <stdio.h>
#include <stdlib.h>

// TODO: GC

typedef struct {
    int *data;
    int size;
    int capacity;
} Vec_i32;

static inline Vec_i32 vec_new_i32(void) {
    Vec_i32 v = {NULL, 0, 0};
    return v;
}

static inline void __vec_grow_i32(Vec_i32 *v) {
    int new_cap = v->capacity == 0 ? 4 : v->capacity * 2;
    int *new_data = (int *)malloc(new_cap * sizeof(int));
    for (int i = 0; i < v->size; i++) new_data[i] = v->data[i];
    if (v->data) free(v->data);
    v->data = new_data;
    v->capacity = new_cap;
}

static inline void vec_push_i32(Vec_i32 *v, int val) {
    if (v->size >= v->capacity) __vec_grow_i32(v);
    v->data[v->size++] = val;
}

static inline int vec_len_i32(Vec_i32 v) {
    return v.size;
}

static inline int vec_get_i32(Vec_i32 v, int idx) {
    if (idx < 0 || idx >= v.size) {
        fprintf(stderr, "panic: index out of bounds: %d (len: %d)\n", idx, v.size);
        exit(1);
    }
    return v.data[idx];
}

static inline void vec_set_i32(Vec_i32 *v, int idx, int val) {
    if (idx < 0 || idx >= v->size) {
        fprintf(stderr, "panic: index out of bounds: %d (len: %d)\n", idx, v->size);
        exit(1);
    }
    v->data[idx] = val;
}

static inline int vec_pop_i32(Vec_i32 *v) {
    if (v->size == 0) {
        fprintf(stderr, "panic: pop from empty vector\n");
        exit(1);
    }
    return v->data[--v->size];
}

static inline void vec_remove_i32(Vec_i32 *v, int idx) {
    if (idx < 0 || idx >= v->size) {
        fprintf(stderr, "panic: remove index out of bounds: %d (len: %d)\n", idx, v->size);
        exit(1);
    }
    for (int i = idx; i < v->size - 1; i++) v->data[i] = v->data[i + 1];
    v->size--;
}

#endif