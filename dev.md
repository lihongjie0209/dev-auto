## 更新requirements.txt

```shell

pip freeze > requirements.txt

```


## postgresql 开发环境


```
docker run --name some-postgres -e POSTGRES_DB=test -e POSTGRES_USER=root -e POSTGRES_PASSWORD=root -p 5432:5432 -d postgres

db-tool.py doc  -h localhost -p 5432 -u root -pwd root -d test -t postgresql

```


```sql

-- 创建表
CREATE TABLE example_table (
    -- 整数类型
    id SERIAL PRIMARY KEY, -- 主键，自增整数
    age INTEGER NOT NULL, -- 年龄，整数，不能为空
    score DECIMAL(5, 2), -- 分数，小数，最多5位，其中2位小数

    -- 字符串类型
    name VARCHAR(100) NOT NULL, -- 姓名，可变长字符串，最大长度100，不能为空
    address TEXT, -- 地址，文本类型，长度不限

    -- 日期和时间类型
    birth_date DATE, -- 出生日期
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- 创建时间，无时区的时间戳，默认为当前时间

    -- 布尔类型
    is_active BOOLEAN NOT NULL DEFAULT TRUE, -- 是否激活，布尔类型，不能为空，默认为true

    -- 枚举类型
    status ENUM('active', 'inactive', 'pending') NOT NULL DEFAULT 'pending' -- 状态，枚举类型，不能为空，默认为'pending'
);

-- 添加表注释
COMMENT ON TABLE example_table IS '示例表，包含常见数据类型';

-- 添加字段注释
COMMENT ON COLUMN example_table.id IS '主键ID';
COMMENT ON COLUMN example_table.age IS '年龄';
COMMENT ON COLUMN example_table.score IS '分数';
COMMENT ON COLUMN example_table.name IS '姓名';
COMMENT ON COLUMN example_table.address IS '地址';
COMMENT ON COLUMN example_table.birth_date IS '出生日期';
COMMENT ON COLUMN example_table.created_at IS '创建时间';
COMMENT ON COLUMN example_table.is_active IS '是否激活';
COMMENT ON COLUMN example_table.status IS '状态';



```