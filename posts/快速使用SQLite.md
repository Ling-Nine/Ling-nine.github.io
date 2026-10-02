---
title: 快速使用SQLite
date: 2026-10-02
tags: [介绍, 技术]
excerpt: 入门使用SQLite
---

# 入门使用SQLite

SQLite 是一个轻量级的、嵌入式的关系型数据库管理系统。它以一个小型的 C 语言库形式存在，可以直接集成到应用程序中，不需要独立的数据库服务器进程，也无需配置和管理。

## 如何快速使用SQLite

在Python 中操作 SQLite 非常简单，它内置了 `sqlite3` 模块，无需额外安装。下面是常用的基本用法。

#### 建表

```python
import sqlite3

# 连接数据库（如果不存在则自动创建）
conn = sqlite3.connect('example.db')
# 或者在内存中操作
conn = sqlite3.connect(':memory:')

# 创建游标
cursor = conn.cursor()

# 创建一张表
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER
    )
''')
conn.commit()  # 提交事务
```

在创建表中：

id：列名，通常用作主键字段。
INTEGER：数据类型，表示该列存储整数。
PRIMARY KEY：主键约束，表示该列的值唯一且非空，用于唯一标识每一行记录。
AUTOINCREMENT：从1开始，自动递增。每次插入新记录时，如果没有显式指定 id 值，SQLite 会自动生成一个比最大值大 1 的整数作为新记录的 id（不会复用已删除的 id）。

需要注意的是

1. **`AUTOINCREMENT` 是 SQLite 特有的写法**，其他数据库（如 MySQL）常用 `AUTO_INCREMENT`。
2. 在 SQLite 中，如果不加 `AUTOINCREMENT`，id本身也会自动递增。区别是：
   - 不加 `AUTOINCREMENT`：如果删除了最大 id 的记录，新插入的 id 可能会复用被删除的 id。
   - 加了 `AUTOINCREMENT`：id 只会递增，不会复用已删除的 id。
3. `AUTOINCREMENT` 必须作用在 `INTEGER PRIMARY KEY` 上，否则会报错。

这样 `users` 表中的每条记录都会有一个自动生成且唯一的 `id`。

#### 数据插入与查询

```python
# 方式一：直接写 SQL
cursor.execute("INSERT INTO users (name, age) VALUES ('Alice', 25)")

# 方式二：使用占位符（推荐，防止 SQL 注入）
cursor.execute("INSERT INTO users (name, age) VALUES (?, ?)", ('Bob', 30))

# 插入多条
data = [('Charlie', 35), ('David', 40)]
cursor.executemany("INSERT INTO users (name, age) VALUES (?, ?)", data)

conn.commit()
```

```python
# 查询所有数据
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()  # 返回列表，每个元素是一条记录（元组）

for row in rows:
    print(row)

# 查询单条
cursor.execute("SELECT * FROM users WHERE id = ?", (1,))
row = cursor.fetchone()
print(row)

# 按条件查询
cursor.execute("SELECT name, age FROM users WHERE age > ?", (30,))
rows = cursor.fetchall()
```

```python
# 更新数据
cursor.execute("UPDATE users SET age = ? WHERE name = ?", (26, 'Alice'))
conn.commit()

# 删除数据
cursor.execute("DELETE FROM users WHERE name = ?", ('Bob',))
conn.commit()

# 关闭连接
cursor.close()
conn.close()
```

#### 其他用法

```python
# 使用 with 自动管理
import sqlite3

with sqlite3.connect('example.db') as conn:
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")
    cursor.execute("INSERT INTO users (name) VALUES (?)", ('Alice',))
    conn.commit()  # 使用 with 时，正常结束会自动 commit，但显式 commit 更清晰
```

注意：`with` 块只会自动提交事务，**不会自动关闭连接**。如需自动关闭，可结合 `contextlib.closing` 或手动 `close()`。

```python
# 设置行工厂，返回字典
conn.row_factory = sqlite3.Row
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()
for row in rows:
    print(row['name'], row['age'])
```

## SQLite 数据类型

每个存储在 SQLite 数据库中的值都具有以下存储类之一：

| 存储类  | 描述                                                         |
| ------- | ------------------------------------------------------------ |
| NULL    | 值是一个 NULL 值。                                           |
| INTEGER | 值是一个带符号的整数，根据值的大小存储在 1、2、3、4、6 或 8 字节中。 |
| REAL    | 值是一个浮点值，存储为 8 字节的 IEEE 浮点数字。              |
| TEXT    | 值是一个文本字符串，使用数据库编码（UTF-8、UTF-16BE 或 UTF-16LE）存储。 |
| BLOB    | 值是一个 blob 数据，完全根据它的输入存储。                   |

SQLite 的存储类稍微比数据类型更普遍。INTEGER 存储类，例如，包含 6 种不同的不同长度的整数数据类型。

## 数据库实用内容

#### 数据库配置

```sql
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
```

`PRAGMA` 是 SQLite 的特殊命令，用来设置运行参数。
`journal_mode=WAL`意为把日志模式设为 WAL（Write-Ahead Logging，预写日志）。
效果：读操作和写操作可以并发执行，写的时候读不卡，读的时候写不卡，适合 Web 应用。这是现代 SQLite 推荐的模式。
`foreign_keys=ON`开启外键约束。
默认情况下 SQLite 不会强制外键，开了之后，如果插入的 author_id 在 users 表中不存在，会报错。这样数据完整性有保障。

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    bio TEXT
) STRICT;
```

`CREATE TABLE IF NOT EXISTS`：如果表不存在才创建，重复执行不会报错。
`id INTEGER PRIMARY KEY`：自增主键（SQLite 中 `INTEGER PRIMARY KEY` 自动变成自增 ID）。
`username TEXT UNIQUE NOT NULL`：用户名，不能为空，且不能重复。
`bio TEXT`：实际场景用于存放个人简介，文字类型。
`STRICT`：严格模式表。从 SQLite 3.37 开始支持。
普通表允许“宽松类型”，比如往 INTEGER 列里塞文本也能存进去；STRICT 则会强制类型匹配，写错类型直接报错。更接近传统数据库的行为，建议使用。

```sql
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY,
    author_id INTEGER NOT NULL REFERENCES users(id),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    published_at TEXT,
    status TEXT NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft','published','archived')), 
        --限定状态只能是这三个值之一，其他值会报错。
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    --CURRENT_TIMESTAMP 最后更新时间，默认当前时间
) STRICT;
```

`author_id INTEGER NOT NULL REFERENCES users(id)`：实际场景用于存放作者 ID，不能为空，且必须存在于 users.id 中。这是外键，开启 foreign_keys 后才会真正校验。

#### 索引

```sql
CREATE INDEX IF NOT EXISTS idx_posts_author_status
    ON posts(author_id, status, published_at DESC);
```

这是**复合索引**，按三个字段联合排序：

- `author_id` 在前
- `status` 其次
- `published_at` 降序排

当你要查询“某个作者已发布的最新文章”时，数据库可以直接用这个索引快速定位，而不需要扫描整个表。例如：

```sql
SELECT * FROM posts
WHERE author_id = 1 AND status = 'published'
ORDER BY published_at DESC;
```

索引不是“函数”，**我们不需要也不会直接调用它**。是数据库自动维护的一张“目录”，只要 SQL 符合它的规则，数据库优化器就会**自动**走这个索引。

#### 触发器

```sql
CREATE TRIGGER IF NOT EXISTS trg_posts_updated
    AFTER UPDATE ON posts  -- 在更新操作完成后触发。
    FOR EACH ROW           -- 每更新一行都会执行一次。
BEGIN
    UPDATE posts SET updated_at = CURRENT_TIMESTAMP
    WHERE id = OLD.id;     -- 指被更新前的行的 ID。
END;
```

触发器的意思是：当 posts 表里任意一行被 UPDATE 之后，自动把这一行的 updated_at 改成当前时间,这样就不用手动维护这个字段了。例如：

```sql
-- 插入一篇文章
INSERT INTO posts (author_id, title, content, status) 
VALUES (1, '标题', '正文', 'draft');

-- 此时 updated_at = 插入时的时间

-- 修改文章内容

UPDATE posts SET content = '新内容' WHERE id = 1;

-- 修改后 updated_at 自动变成当前时间
```

注意：触发器内用 UPDATE posts ... WHERE id = OLD.id 本身也是更新，会不会触发自己？
不会，因为 SQLite 不允许触发器递归修改同一张表导致无限循环，它会在内部处理掉这种自我触发。

#### 聚合函数

SQL 里常见的聚合函数有 `COUNT`、`SUM`、`AVG`、`MAX`、`MIN`。它们的作用是把多行数据“合并”成一个结果，比如：

```sql
SELECT AVG(score) FROM students;
```

#### 自定义函数

SQLite 允许在 Python 里注册自己的函数，相当于给 SQL 增加内建能力。

```python
import sqlite3

conn = sqlite3.connect(':memory:')
conn.create_function('regexp_substr', 2, lambda s, p: __import__('re').search(p, s).group())

conn.execute("CREATE TABLE logs(msg TEXT)")
conn.execute("INSERT INTO logs VALUES ('error: 404, path=/admin')")

cursor = conn.execute("SELECT regexp_substr(msg, 'path=[^ ]+') FROM logs")
print(cursor.fetchone())  # ('path=/admin',)
```

也能注册聚合函数，比如分组统计特殊逻辑：

```python
class Median: # 求中位数
    def __init__(self):
        self.values = []
    def step(self, value): # SQL 引擎每扫描到一行，就调用 step 一次，把当前行的值加入列表。
        self.values.append(value)
    def finalize(self): # 所有值收集完后，在 finalize 里排序并计算中位数
        values = sorted(self.values)
        n = len(values)
        if n == 0:
            return 0
        mid = n // 2
        if n % 2 == 0:
            return (values[mid-1] + values[mid]) / 2
        return values[mid]

conn.create_aggregate('median', 1, Median)
```

注册之后，就可以在 SQL 里直接用了，比如：

```sql
SELECT median(score) FROM students;
```

也可以配合 `GROUP BY` 做分组统计：

```sql
SELECT class, median(score) FROM students GROUP BY class;
```

#### 事务与保存点

SQLite 支持保存点 SAVEPOINT，允许在事务内部做部分回滚，不废弃整个事务。

```python
conn.execute("BEGIN")
try:
    conn.execute("INSERT INTO posts(title) VALUES ('t1')")
    conn.execute("SAVEPOINT sp_before_step")
    conn.execute("INSERT INTO posts(title) VALUES ('t2')")
    # 发现问题，回滚到保存点
    conn.execute("ROLLBACK TO sp_before_step")
    # 继续执行其他操作
    conn.execute("INSERT INTO posts(title) VALUES ('t3')")
    conn.commit()
except:
    conn.rollback()
```

这在批量同步、复杂多步写入、需要中途容错的场景里很有用。

#### 数据的导入导出

- **导入 CSV**：`.import` 命令或者 Python 的 `csv` + `executemany`。
- **导出 JSON**：`json_group_array` 配合查询。

```sql
SELECT json_group_array(json_object(
    'id', id,
    'title', title,
    'status', status
))
FROM posts;
```

- **导出 Markdown/HTML**：利用 SQL 拼接字符串。

```sql
SELECT printf(
    '- [%s](/post/%d)  %s\n',
    title, id, date(updated_at)
) FROM posts WHERE status='published';
```

- **SQLite 文件直接作为应用数据交换格式**：很多软件支持导入导出 SQLite 文件，比如备忘录、词典、游戏存档。

------

## 结语

感谢你阅读这篇文章！如果你有任何问题或建议，欢迎通过 [GitHub Issues](https://github.com/Ling-Nine/Ling-nine.github.io/issues) 与我交流。

---

*本文使用 Markdown 编写，最后更新于 2026年10月2日*