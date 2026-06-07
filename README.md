# Rust-like to C Transpiler

一个将类 Rust 语法转译为标准 C 代码的源到源编译器（Source-to-Source Compiler），支持现代语言特性（闭包、代数数据类型、泛型容器、方法调用），生成的 C 代码零外部库依赖，可直接用标准 C 编译器编译运行。

## 项目概述

本项目实现了一个四阶段转译器，将带有 Rust 风格语法的扩展语言解析并转译为纯标准 C 代码。所有高级抽象（Option、Vector、闭包、方法调用）均通过 C 结构体、函数指针和宏模拟。

### 核心特性

| 特性              | 说明                                                   | 示例                                                      |
| ----------------- | ------------------------------------------------------ | --------------------------------------------------------- |
| **Option 类型**   | `Some`/`None` 代数数据类型，支持 `match` 表达式        | `let x = Some(10); match x { Some(v) => v+1, None => 0 }` |
| **动态数组**      | `Vec<i32>` 支持 `push`/`pop`/`len`/`remove` 及索引读写 | `let v = [1, 2, 3]; v.push(4); v[1] = 10;`                |
| **函数式编程**    | 一等函数、闭包捕获、高阶函数、Lambda 语法糖            | `let add = fn(a) => fn(b) => a + b; add(3)(4)`            |
| **Struct + Impl** | 数据封装与方法调用，隐式 `&self` 注入                  | `rect.area()` → `Rectangle_area(&rect)`                   |
| **输出语句**      | `print(expr)` 自动换行输出                             | `print(x + 5);`                                           |

### 转译流程

```text
源代码 → Lexer(词法分析) → Parser(语法分析) → AST
  → Semantic(语义分析) → Codegen(代码生成) → 标准 C 代码
```

## 目录结构

```text
.
├── transpiler/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py           # 命令行入口
│   │   ├── compiler.py       # 编译器入口
│   │   ├── lexer.py          # 词法分析器
│   │   ├── parser.py         # 语法分析器
│   │   ├── semantic.py       # 语义分析器
│   │   └── codegen.py        # C 代码生成器
│   ├── test_outputs/
│   │   ├── *.txt			 # 测试用例
│   └── runtime/
│       ├── option.h          # Option<i32> 运行时
│       ├── vec.h             # Vec<i32> 运行时
│       └── closure.h         # 闭包结构体定义
├── input.txt                 # 输入源文件
├── output.c                  # 生成的 C 文件
└── README.md                 # 本文件
```

## 测试

在`./test_outputs`下提供了51个示例.txt文件，每个示例文件包括输入源码和生成的C代码，均经过gcc编译测试通过。

也可以在`input.txt`中构造需要的测试用例，运行`main.py`将调用编译器将生成的C代码输出到`output.c`中。



## 语言语法

### 注释

```rust
'''
仅支持类似python三个单引号的多行注释
不支持单行注释
'''
```

### 基础类型

- `i32` — 32 位有符号整数
- `bool` — 布尔类型（C 中用 `int` 表示）
- `Vec<i32>` — 整数动态数组
- `Option<i32>` — 可选整数
- `fn(T...) -> R` — 函数类型

### 变量与表达式

```rust
let x = 10;                    ''' 变量声明 '''
let y = x + 5;                 ''' 算术表达式 '''
let z = Some(42);              ''' Option '''
let v = [1, 2, 3];             ''' Vec 字面量 '''
let rect = new Rectangle { width: 5, height: 6 };  ''' struct 实例化（注意有new，与Rust语法不一样）'''
```

### 控制流

```rust
if (x > 5) { ... } else { ... }          ''' 条件分支（括号推荐但非必须）'''
while (i < 10) { ... }                   ''' 循环（括号推荐但非必须）'''
for x in arr { ... }                     ''' 迭代循环 '''
match opt { Some(v) => v, None => 0 }    ''' 模式匹配（只能对变量使用）'''
```

### Option 操作

```rust
let x = Some(10);

''' 类型测试（两种风格等价）'''
if is_some(x) { ... }
if x.is_some { ... }

''' 无值判断（两种风格等价）'''
if is_none(x) { ... }
if x.is_none { ... }
```

### Vec 操作

```rust
let v = [1, 2, 3];

''' 方法调用 '''
v.push(4);           ''' 尾部插入 '''
v.pop();             ''' 弹出尾部，并返回被弹出的值 '''
v.len();             ''' 返回当前长度 '''
v.remove(0);         ''' 按索引删除 '''

''' 索引访问（运行时越界检查，越界即 panic 退出）'''
let a = v[0];        ''' 读取 '''
v[1] = 10;           ''' 写入 '''
```

### 函数与闭包

```rust
''' 命名函数 '''
fn add(a, b) { return a + b; }

''' 匿名函数（无捕获）'''
let double = fn(x) { return x * 2; };

''' Lambda 语法糖 '''
let triple = fn x => x * 3;

''' 闭包（捕获外部变量）'''
let adder = fn(a) => fn(b) => a + b;
let f = adder(3);
print(f(4));  ''' 预期输出：7 '''

''' 函数作为参数 '''
fn apply_twice(f, x) {
    return f(f(x));
}
let doubled = fn x => x * 2;
print(apply_twice(doubled, 3));  ''' 预期输出：12 '''
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
print(p.dist());  ''' 预期输出：25 '''
```

### 输出

```rust
print(expr);   ''' 打印表达式值并换行，仅支持输出 i32 '''
```



## 已知限制

| 限制                       | 说明                                                         |
| -------------------------- | ------------------------------------------------------------ |
| 仅支持 `i32`               | 无浮点数、字符串、字符类型                                   |
| 闭包捕获仅支持 `i32`       | 不支持 `Vec`/`Option`/`struct` 捕获                          |
| `match` 返回类型支持 `i32` | 不支持返回闭包                                               |
| 变量声明的同时必须赋值     | 不支持无初始化声明                                           |
| 只能对变量进行 match       | 不支持对表达式直接 match                                     |
| 循环闭包泄漏               | `for`/`while` 内同名闭包变量仅最后一次迭代的 env 被释放，中间迭代泄漏 |
| Move 检查宽松              | 闭包变量移动后，同作用域再次使用已经移动的变量编译器不报错（当然这是非法操作） |