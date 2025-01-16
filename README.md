
# 环境准备

- 安装 Python 3.7+
- 安装依赖 `pip install -r requirements.txt`


# 脚本说明

## db-tool.py

数据库文档生成工具，支持 MySQL、PostgreSQL(todo), KingBase(todo) 数据库。


![](./image/db-tool-demo.gif)


### 使用方法

```
(.venv) PS D:\code\dev-auto> python .\db-tool.py doc --help                                                               
Usage: db-tool.py doc [OPTIONS]

  生成数据库文档

Options:
  -j, --jdbc TEXT        jdbc url for host port database
  -o, --output TEXT      output file  [default: db-doc.docx]
  -t, --dbtype [mysql]   database type
  -h, --host TEXT        database host
  -p, --port TEXT        database port
  -u, --user TEXT        database user
  -pwd, --password TEXT  database password
  -d, --database TEXT    database name
  --open                 open file after generate
  --template TEXT        ms word template file
  --help                 Show this message and exit.

```

```shell
# 查看帮助

python db-tool.py -h


# 生成数据库文档

python db-tool.py doc -h 10.111.128.219 -p 8889 -u tech_ext -pwd password!!! -d tech_ext
```


### 进阶用法
可以通过指定模板文件，生成自定义的数据库文档。
模板可以参考 default.docx 文件，使用 jinja2 语法。 模板工具使用的是 python-docx-template 库。

渲染上下文对象 db, 可以参考 db-tool.py 中 Database 类的定义。



参考文档：
- https://docxtpl.readthedocs.io/en/latest/
- https://jinja.palletsprojects.com/en/2.11.x/templates/





