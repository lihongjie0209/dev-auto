import glob
import re
from dataclasses import dataclass
from email.policy import default

import click
import survey
from click import argument, option
from lxml import etree

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

            ts = cursor.execute("show table status")
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


@cli.command(name='doc')
@click.pass_context
@option("--jdbc", "-j", help="jdbc url for host port database")
@option('--output', '-o', help='output file', default='db-doc.docx', show_default=True)
@option("--dbtype", "-t", type=click.Choice(['mysql']), help="database type", default="mysql")
@option("--host", "-h", help="database host")
@option("--port", "-p", help="database port")
@option("--user", "-u", help="database user")
@option("--password", "-pwd", help="database password")
@option("--database", "-d", help="database name")
@option("--open", help="open file after generate", is_flag=True, default=True)
@option("--template", help="ms word template file", default="default.docx")
def db_doc(ctx, jdbc, output, dbtype, host, port, user, password, database, open, template):
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

    if dbtype == 'mysql':
        db = read_mysql_db(host, port, user, password, database)
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
