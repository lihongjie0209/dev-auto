import glob
import re
from dataclasses import dataclass
from email.policy import default
import psycopg2
import click
import survey
from click import argument, option
from lxml import etree
from psycopg2.extras import RealDictCursor
import os
import pymysql.cursors
from docxtpl import DocxTemplate


@dataclass
class Database:
    # 数据库名
    name: str
    # 表
    tables: list


@dataclass
class Table:
    # 表名
    name: str
    # 注释
    comment: str
    # 列
    columns: list


@dataclass
class Column:
    # 表名
    table: str
    # 列名
    name: str
    # 数据类型
    type: str
    # 长度
    length: int
    # 小数位数
    decimal: int
    # 是否可为空
    nullable: bool
    # 默认值
    default: str
    # 注释
    comment: str

    # 主键
    primary_key: bool = False


@click.group()
@click.pass_context
def cli(ctx):
    pass


def read_mysql_db(host, port, user, password, database):
    with pymysql.connect(host=host,
                         port=int(port),
                         user=user,
                         password=password,
                         db=database,
                         charset='utf8mb4',
                         cursorclass=pymysql.cursors.DictCursor) as connection:
        with connection.cursor() as cursor:
            tables = get_all_tables(cursor)
            table_list = []
            # get table comment

            cursor.execute("show table status")
            table_status = cursor.fetchall()
            table_comment = {table['Name']: table['Comment'] for table in table_status}

            for table in tables:
                columns = get_all_columns(cursor, table)
                table_list.append(Table(name=table, columns=columns, comment=table_comment.get(table, '')))
            return Database(name=database, tables=table_list)


def gen_file(template, output: str, db: Database | None):
    doc = DocxTemplate(template)
    context = {'db': db}
    doc.render(context)
    try:
        doc.save(output)
    except PermissionError as e:
        raise click.ClickException(f"无法保存文件: {output}, 请检查文件是否被占用或者被其他程序打开") from e


def get_all_tables_pg(cursor, schema):
    cursor.execute(f"""
    SELECT 
    c.relname AS table_name, 
    obj_description(c.oid) AS table_comment
FROM 
    pg_class c
JOIN 
    pg_namespace n ON c.relnamespace = n.oid
WHERE 
    n.nspname = '{schema}' AND 
    c.relkind = 'r'
ORDER BY 
    c.relname;
    """)
    tables = cursor.fetchall()
    return tables


def get_all_columns_pg(cursor, param, schema):
    # 执行SQL查询语句
    cursor.execute(f"""
        SELECT 
            c.table_name,
            c.column_name,
            c.data_type,
            CASE 
                WHEN c.data_type = 'character varying' OR c.data_type = 'varchar' THEN c.character_maximum_length
                WHEN c.data_type = 'numeric' THEN c.numeric_precision
                ELSE NULL
            END AS length,
            CASE 
                WHEN c.data_type = 'numeric' THEN c.numeric_scale
                ELSE NULL
            END AS decimal,
            c.is_nullable = 'YES' AS nullable,
            c.column_default,
            d.description AS comment,
            c.column_name IN (
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = c.table_name::regclass AND i.indisprimary
            ) AS primary_key
        FROM 
            information_schema.columns c
        JOIN 
            pg_description d ON d.objoid = c.table_name::regclass AND d.objsubid = c.ordinal_position
        WHERE 
            c.table_schema = '{schema}'
        ORDER BY 
            c.table_name, 
            c.ordinal_position;
    """)

    # 获取查询结果
    columns = cursor.fetchall()

    # 将结果转换为Column类的实例
    column_objects = [
        Column(
            table=row['table_name'],
            name=row['column_name'],
            type=row['data_type'],
            length=row['length'],
            decimal=row['decimal'],
            nullable=row['nullable'],
            default=row['column_default'] or '',
            comment=row['comment'],
            primary_key=row['primary_key']
        )
        for row in columns
    ]

    return column_objects


def read_postgresql_db(host, port, user, password, database, schema):
    schema = schema or 'public'

    with psycopg2.connect(database=database, user=user, password=password, host=host, port=port,
                          cursor_factory=RealDictCursor) as connection:
        with connection.cursor() as cursor:
            tables = get_all_tables_pg(cursor, schema)

            table_list = []
            for table in tables:
                all_columns_pg = get_all_columns_pg(cursor, table['table_name'], schema)
                table_list.append(
                    Table(name=table['table_name'], columns=all_columns_pg, comment=table['table_comment']))

            return Database(name=database, tables=table_list)


@cli.command(name='doc')
@click.pass_context
@option("--jdbc", "-j", help="jdbc url for host port database")
@option('--output', '-o', help='output file', default='db-doc.docx', show_default=True)
@option("--dbtype", "-t", type=click.Choice(['mysql', 'postgresql', 'doris']), help="database type", default="mysql")
@option("--host", "-h", help="database host")
@option("--port", "-p", help="database port")
@option("--user", "-u", help="database user")
@option("--password", "-pwd", help="database password")
@option("--schema", "-s", help="database schema")
@option("--database", "-d", help="database name")
@option("--open", help="open file after generate", is_flag=True, default=True)
@option("--template", help="ms word template file", default="default.docx")
def db_doc(ctx, jdbc, output, dbtype, host, port, user, password, schema, database, open, template):
    """
    生成数据库文档
    """
    if is_file_in_use(output):
        raise click.ClickException(f"文件: {output} 已被占用, 请关闭文件后再试")

    if not host and not port and not jdbc and not database:
        use_jdbc = survey.routines.inquire("使用jdbc链接提供数据库信息? ", default=True)
        if use_jdbc:
            jdbc = survey.routines.input("请输入jdbc url: ")

    if jdbc:
        # jdbc:mysql://localhost:3306/test
        m = re.match(r'jdbc:(\w+):\/\/([\w\.-]+):(\d+)\/(\w+)', jdbc)
        if m:
            dbtype, host, port, database = m.groups()
        else:
            raise click.ClickException("jdbc url 格式不正确")

    if not host:
        host = survey.routines.input("请输入数据库主机地址: ")
        # 如果用户输入的是 host:port
        if ':' in host:
            host, port = host.split(':')

    if not port:
        port = survey.routines.numeric("请输入数据库端口: ")

    if not user:
        user = survey.routines.input("请输入数据库用户名: ")

    if not password:
        password = survey.routines.conceal("请输入数据库密码: ")

    if not database:
        database = survey.routines.input("请输入数据库名称: ")

    click.echo(f'开始生成数据库文档: {dbtype} {host}:{port}/{database} -> {output}')

    if dbtype == 'mysql' or dbtype == 'doris':
        db = read_mysql_db(host, port, user, password, database)

    elif dbtype == 'postgresql':
        db = read_postgresql_db(host, port, user, password, database, schema)
    else:
        click.echo(f"不支持的数据库类型: {dbtype}")
        return

    gen_file(template, output, db)

    if open:
        os.startfile(output)


def get_all_tables(cursor):
    cursor.execute("show tables")
    tables = cursor.fetchall()
    return [list(table.values())[0] for table in tables]


def get_type(type):
    # get type info from mysql type use regex
    return re.match(r'(\w+)(\((\d+)(,(\d+))?\))?', type).groups()[0]


def get_length(param):
    return re.match(r'(\w+)(\((\d+)(,(\d+))?\))?', param).groups()[2]


def get_decimal(param):
    return re.match(r'(\w+)(\((\d+)(,(\d+))?\))?', param).groups()[4]


def get_all_columns(cursor, table):
    cursor.execute("show full columns from " + table)
    columns = cursor.fetchall()
    columns_ = [
        Column(table=table, name=column['Field'], type=get_type(column['Type']), length=get_length(column['Type']),
               decimal=get_decimal(column['Type']),
               nullable=column['Null'] == 'YES',
               default=column['Default'] if column['Default'] is not None else '',
               comment=column['Comment'] if column['Comment'] is not None else '', ) for column in columns]

    # get primary key
    cursor.execute(f"show index from {table}")
    indexs = cursor.fetchall()

    for index in indexs:
        for column in columns_:
            if index['Key_name'] == 'PRIMARY' and index['Column_name'] == column.name:
                column.primary_key = True
                break

    return columns_


def is_file_in_use(filename):
    if not os.path.exists(filename):
        return False

    try:
        with open(filename, 'w') as file:
            return False  # 文件未被占用
    except IOError:
        return True  # 文件被占用


if __name__ == '__main__':
    cli()
