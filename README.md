# Rust-like → C Transpiler

一个将类 Rust 语法转译为标准 C 代码的源到源编译器（Source-to-Source Compiler），支持现代语言特性（闭包、代数数据类型、泛型容器、方法调用），生成的 C 代码零外部库依赖，可直接用标准 C 编译器编译运行。

## 项目概述

本项目实现了一个四阶段转译器，将带有 Rust/Go 风格语法的扩展语言解析并转译为纯标准 C 代码。所有高级抽象（Option、Vector、闭包、方法调用）均通过 C 结构体、函数指针和宏模拟，不引入任何运行时库依赖。

### 核心特性

| 特性 | 说明 | 示例 |
|------|------|------|
| **Option 类型** | `Some`/`None` 代数数据类型，支持 `match` 表达式 | `let x = Some(10); match x { Some(v) => v+1, None => 0 }` |
| **动态数组** | `Vec<i32>` 支持 `push`/`pop`/`len`/`remove` | `let v = [1, 2, 3]; v.push(4);` |
| **函数式编程** | 一等函数、闭包捕获、高阶函数、Lambda 语法糖 | `let add = fn(a) => fn(b) => a + b; add(3)(4)` |
| **Struct + Impl** | 数据封装与方法调用，隐式 `&self` 注入 | `rect.area()` → `Rectangle_area(&rect)` |
| **输出语句** | `print(expr)` 自动换行输出 | `print(x + 5);` |

### 转译流程

```
源代码 → Lexer(词法分析) → Parser(语法分析) → AST
  → Semantic(语义分析) → Codegen(代码生成) → 标准 C 代码
```

## 目录结构

```
.
├── transpiler/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── lexer.py          # 词法分析器
│   │   ├── parser.py         # 语法分析器（SLY LALR）
│   │   ├── semantic.py       # 语义分析器（类型检查、闭包捕获分析）
│   │   ├── codegen.py        # C 代码生成器
│   │   └── compiler.py       # 编译器入口
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── testP0.py         # 基础功能测试
│   │   ├── testP4.py         # 闭包/高阶函数测试
│   │   ├── testP5.py         # Struct/Impl 测试
│   │   └── testP6.py         # print 输出测试
│   └── runtime/
│       ├── option.h            # Option<i32> 运行时
│       ├── vec.h               # Vec<i32> 运行时
│       └── closure.h           # 闭包结构体定义
├── main.py                     # 命令行入口
├── input.txt                   # 输入源文件
├── output.c                    # 生成 C 文件
├── instructor.md               # 项目规划与进度
└── README.md                   # 本文件
```

## 语言语法

### 基础类型

- `i32` — 32 位有符号整数
- `bool` — 布尔类型（C 中用 `int` 表示）
- `Vec<i32>` — 整数动态数组
- `Option<i32>` — 可选整数
- `fn(T...) -> R` — 函数类型

### 变量与表达式

```rust
let x = 10;                    // 变量声明
let y = x + 5;                 // 算术表达式
let z = Some(42);              // Option
let v = [1, 2, 3];             // Vec 字面量
let rect = new Rectangle { width: 5, height: 6 };  // struct 实例化
```

### 控制流

```rust
if (x > 5) { ... } else { ... }          // 条件分支
while (i < 10) { ... }                   // 循环
for x in arr { ... }                     // 迭代循环
match opt { Some(v) => v, None => 0 }    // 模式匹配
```

### 函数与闭包

```rust
// 命名函数
fn add(a, b) { return a + b; }

// 匿名函数（无捕获）
let double = fn(x) { return x * 2; };

// Lambda 语法糖
let triple = fn x => x * 3;

// 闭包（捕获外部变量）
let adder = fn(a) => fn(b) => a + b;
let f = adder(3);
print(f(4));  // 7
```

### Struct 与 Impl

```rust
struct Point { x: i32, y: i32 }

impl Point {
    fn dist(&self) {
        return self.x * self.x + self.y * self.y;
    }
}

let p = new Point { x: 3, y: 4 };
print(p.dist());  // 25
```

### 输出

```rust
print(expr);   // 打印表达式值并换行，仅支持 i32
```

## 限制与已知问题

| 限制 | 说明 |
|------|------|
| 仅支持 `i32` | 无浮点数、字符串、字符类型 |
| 闭包捕获 | 仅支持 `i32`，不支持 `Vec`/`Option`/`struct` 捕获 |
| 泛型 | `Vec`/`Option` 仅硬编码 `i32` 版本 |
| 无 GC | 依赖作用域结束时手动释放，复杂生命周期可能泄漏 |
| `match` 返回类型 | 硬编码为 `i32`，不支持返回闭包 |
