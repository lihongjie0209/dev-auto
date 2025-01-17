import os
import re
from dataclasses import dataclass

import click
import psycopg2
import pymysql.cursors
import survey
from click import option
from docxtpl import DocxTemplate
from psycopg2.extras import RealDictCursor


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


def exclude_table(table, include, exclude):

    if include:
        for i in include:
            if re.match(i, table):
                return False
    if exclude:
        for e in exclude:
            if re.match(e, table):
                return True

    return False


def read_mysql_db(host, port, user, password, database, schema, include, exclude):
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
                if exclude_table(table, include, exclude):
                    continue
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


def get_all_columns_kb(cursor, table, schema):
    # 执行SQL查询语句
    cursor.execute(f"""
    
    
    with my_columns as (
    
    SELECT current_database()::information_schema.sql_identifier                                                                           AS table_catalog, nc.nspname::information_schema.sql_identifier                                                                                   AS table_schema, c.relname::information_schema.sql_identifier                                                                                    AS table_name, a.attname::information_schema.sql_identifier                                                                                    AS column_name, a.attnum::information_schema.cardinal_number                                                                                    AS ordinal_position, CASE
    WHEN a.attgenerated = ''::"char" THEN pg_get_expr(ad.adbin, ad.adrelid)
    ELSE NULL::text
    END::information_schema.character_data                                                                                      AS column_default, CASE
                                                                                                                                                       WHEN a.attnotnull OR t.typtype = 'd'::"char" AND t.typnotnull THEN 'NO'::text
           ELSE 'YES'::text
END::information_schema
.yes_or_no                                                                                           AS is_nullable,
       CASE
           WHEN t.typtype = 'd'::"char" THEN
               CASE
                   WHEN bt.typelem <> 0::oid AND bt.typlen = '-1'::integer THEN 'ARRAY'::text
                   WHEN nbt.nspname = 'pg_catalog'::name THEN format_type(t.typbasetype, NULL::integer)
                   ELSE 'USER-DEFINED'::text
END
ELSE
               CASE
                   WHEN t.typelem <> 0::oid AND t.typlen = '-1'::integer THEN 'ARRAY'::text
                   WHEN nt.nspname = 'pg_catalog'::name THEN format_type(a.atttypid, NULL::integer)
                   ELSE 'USER-DEFINED'::text
END
END::information_schema
.character_data                                                                                      AS data_type,


       (CASE WHEN (information_schema._pg_truetypmod(a.*, t.*) = '-1'::integer) THEN NULL::integer WHEN (information_schema._pg_truetypid(a.*, t.*) = ANY (ARRAY[(1042)::oid, (1043)::oid])) THEN (information_schema._pg_truetypmod(a.*, t.*) - 4) WHEN (information_schema._pg_truetypid(a.*, t.*) = ANY (ARRAY[(1560)::oid, (1562)::oid])) THEN information_schema._pg_truetypmod(a.*, t.*) ELSE NULL::integer END)::information_schema.cardinal_number         AS character_maximum_length,


(CASE information_schema._pg_truetypid(a.*, t.*) WHEN 21 THEN 16 WHEN 23 THEN 32 WHEN 20 THEN 64 WHEN 1700 THEN CASE WHEN (information_schema._pg_truetypmod(a.*, t.*) = '-1'::integer) THEN NULL::integer ELSE (((information_schema._pg_truetypmod(a.*, t.*) - 4) >> 16) & 65535) END WHEN 700 THEN 24 WHEN 701 THEN 53 ELSE NULL::integer END)::information_schema.cardinal_number       AS numeric_precision,

(CASE WHEN (information_schema._pg_truetypid(a.*, t.*) = ANY (ARRAY[(21)::oid, (23)::oid, (20)::oid, (700)::oid, (701)::oid])) THEN 2 WHEN (information_schema._pg_truetypid(a.*, t.*) = (1700)::oid) THEN 10 ELSE NULL::integer END)::information_schema.cardinal_number       AS numeric_precision_radix,

(CASE WHEN (information_schema._pg_truetypid(a.*, t.*) = ANY (ARRAY[(21)::oid, (23)::oid, (20)::oid])) THEN 0 WHEN (information_schema._pg_truetypid(a.*, t.*) = (1700)::oid) THEN CASE WHEN (information_schema._pg_truetypmod(a.*, t.*) = '-1'::integer) THEN NULL::integer ELSE ((information_schema._pg_truetypmod(a.*, t.*) - 4) & 65535) END ELSE NULL::integer END)::information_schema.cardinal_number       AS numeric_scale,
(CASE WHEN (information_schema._pg_truetypid(a.*, t.*) = (1082)::oid) THEN 0 WHEN (information_schema._pg_truetypid(a.*, t.*) = ANY (ARRAY[(1083)::oid, (1114)::oid, (1184)::oid, (1266)::oid])) THEN CASE WHEN (information_schema._pg_truetypmod(a.*, t.*) < 0) THEN 6 ELSE information_schema._pg_truetypmod(a.*, t.*) END WHEN (information_schema._pg_truetypid(a.*, t.*) = (1186)::oid) THEN CASE WHEN ((information_schema._pg_truetypmod(a.*, t.*) < 0) OR ((information_schema._pg_truetypmod(a.*, t.*) & 65535) = 65535)) THEN 6 ELSE (information_schema._pg_truetypmod(a.*, t.*) & 65535) END ELSE NULL::integer END)::information_schema.cardinal_number       AS datetime_precision,


       NULL::integer::information_schema.cardinal_number                                                                               AS interval_precision,
       NULL::name::information_schema.sql_identifier                                                                                   AS character_set_catalog,
       NULL::name::information_schema.sql_identifier                                                                                   AS character_set_schema,
       NULL::name::information_schema.sql_identifier                                                                                   AS character_set_name,
       CASE
           WHEN nco.nspname IS NOT NULL THEN current_database()
           ELSE NULL::name
END::information_schema
.sql_identifier                                                                                      AS collation_catalog,
       nco.nspname::information_schema.sql_identifier                                                                                  AS collation_schema,
       co.collname::information_schema.sql_identifier                                                                                  AS collation_name,
       CASE
           WHEN t.typtype = 'd'::"char" THEN current_database()
           ELSE NULL::name
END::information_schema
.sql_identifier                                                                                      AS domain_catalog,
       CASE
           WHEN t.typtype = 'd'::"char" THEN nt.nspname
           ELSE NULL::name
END::information_schema
.sql_identifier                                                                                      AS domain_schema,
       CASE
           WHEN t.typtype = 'd'::"char" THEN t.typname
           ELSE NULL::name
END::information_schema
.sql_identifier                                                                                      AS domain_name,
       current_database()::information_schema.sql_identifier                                                                           AS udt_catalog,
       COALESCE(nbt.nspname, nt.nspname)::information_schema.sql_identifier                                                            AS udt_schema,
       COALESCE(bt.typname, t.typname)::information_schema.sql_identifier                                                              AS udt_name,
       NULL::name::information_schema.sql_identifier                                                                                   AS scope_catalog,
       NULL::name::information_schema.sql_identifier                                                                                   AS scope_schema,
       NULL::name::information_schema.sql_identifier                                                                                   AS scope_name,
       NULL::integer::information_schema.cardinal_number                                                                               AS maximum_cardinality,
       a.attnum::information_schema.sql_identifier                                                                                     AS dtd_identifier,
       'NO'::character varying::information_schema.yes_or_no                                                                           AS is_self_referencing,
       CASE
           WHEN a.attidentity = ANY (ARRAY ['a'::"char", 'd'::"char"]) THEN 'YES'::text
           ELSE 'NO'::text
END::information_schema
.yes_or_no                                                                                           AS is_identity,
       CASE a.attidentity
           WHEN 'a'::"char" THEN 'ALWAYS'::text
           WHEN 'd'::"char" THEN 'BY DEFAULT'::text
           ELSE NULL::text
END::information_schema
.character_data                                                                                      AS identity_generation,
       seq.seqstart::information_schema.character_data                                                                                 AS identity_start,
       seq.seqincrement::information_schema.character_data                                                                             AS identity_increment,
       seq.seqmax::information_schema.character_data                                                                                   AS identity_maximum,
       seq.seqmin::information_schema.character_data                                                                                   AS identity_minimum,
       CASE
           WHEN seq.seqcycle THEN 'YES'::text
           ELSE 'NO'::text
END::information_schema
.yes_or_no                                                                                           AS identity_cycle,
       CASE
           WHEN a.attgenerated <> ''::"char" THEN 'ALWAYS'::text
           ELSE 'NEVER'::text
END::information_schema
.character_data                                                                                      AS is_generated,
       CASE
           WHEN a.attgenerated <> ''::"char" THEN pg_get_expr(ad.adbin, ad.adrelid)
           ELSE NULL::text
END::information_schema
.character_data                                                                                      AS generation_expression,
       CASE
           WHEN (c.relkind = ANY (ARRAY ['r'::"char", 'p'::"char"])) OR
                (c.relkind = ANY (ARRAY ['v'::"char", 'f'::"char"])) AND
                pg_column_is_updatable(c.oid::regclass, a.attnum, false) THEN 'YES'::text
           ELSE 'NO'::text
END::information_schema
.yes_or_no                                                                                           AS is_updatable
FROM pg_attribute a
         LEFT JOIN pg_attrdef ad ON a.attrelid = ad.adrelid AND a.attnum = ad.adnum
         JOIN (pg_class c
    JOIN pg_namespace nc ON c.relnamespace = nc.oid) ON a.attrelid = c.oid
         JOIN (pg_type t
    JOIN pg_namespace nt ON t.typnamespace = nt.oid) ON a.atttypid = t.oid
         LEFT JOIN (pg_type bt
    JOIN pg_namespace nbt ON bt.typnamespace = nbt.oid) ON t.typtype = 'd'::"char" AND t.typbasetype = bt.oid
         LEFT JOIN (pg_collation co
    JOIN pg_namespace nco ON co.collnamespace = nco.oid)
                   ON a.attcollation = co.oid AND (nco.nspname <> 'pg_catalog'::name OR co.collname <> 'default'::name)
         LEFT JOIN (pg_depend dep
    JOIN pg_sequence seq ON dep.classid = 'pg_class'::regclass::oid AND dep.objid = seq.seqrelid AND
                            dep.deptype = 'i'::"char")
                   ON dep.refclassid = 'pg_class'::regclass::oid AND dep.refobjid = c.oid AND dep.refobjsubid = a.attnum
WHERE NOT pg_is_other_temp_schema(nc.oid)
  AND a.attnum > 0
  AND NOT a.attisdropped
  AND (c.relkind = ANY (ARRAY ['r'::"char", 'v'::"char", 'f'::"char", 'p'::"char"]))
  AND (pg_has_role(c.relowner, 'USAGE'::text) OR
       has_column_privilege(c.oid, a.attnum, 'SELECT, INSERT, UPDATE, REFERENCES'::text))
    
    )
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
            my_columns c
        LEFT JOIN 
            pg_description d ON d.objoid = c.table_name::regclass AND d.objsubid = c.ordinal_position
        WHERE 
            c.table_schema = '{schema}'
            AND c.table_name = '{table}'
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
            comment=row['comment'] or '',
            primary_key=row['primary_key']
        )
        for row in columns
    ]

    return column_objects



def get_all_columns_pg(cursor, table, schema):
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
            AND c.table_name = '{table}'
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


def read_postgresql_db(host, port, user, password, database, schema, include, exclude):
    schema = schema or 'public'

    with psycopg2.connect(database=database, user=user, password=password, host=host, port=port,
                          cursor_factory=RealDictCursor) as connection:
        with connection.cursor() as cursor:

            update_schema(cursor, schema)

            tables = get_all_tables_pg(cursor, schema)

            table_list = []
            for table in tables:

                if exclude_table(table['table_name'], include, exclude):
                    continue

                all_columns_pg = get_all_columns_pg(cursor, table['table_name'], schema)
                table_list.append(
                    Table(name=table['table_name'], columns=all_columns_pg, comment=table['table_comment']))

            return Database(name=database, tables=table_list)


def read_kingbase_db(host, port, user, password, database, schema, include, exclude):
    schema = schema or 'public'

    with psycopg2.connect(database=database, user=user, password=password, host=host, port=port,
                          cursor_factory=RealDictCursor) as connection:
        with connection.cursor() as cursor:


            update_schema(cursor, schema)

            tables = get_all_tables_pg(cursor, schema)

            table_list = []
            for table in tables:
                if exclude_table(table['table_name'], include, exclude):
                    continue
                all_columns = get_all_columns_kb(cursor, table['table_name'], schema)
                table_list.append(
                    Table(name=table['table_name'], columns=all_columns, comment=table['table_comment']))

            return Database(name=database, tables=table_list)


def update_schema(cursor, schema):
    cursor.execute("SELECT current_schema()")
    click.echo("current_schema is : " + cursor.fetchone()['current_schema'])
    set_cmd = f"SET search_path TO \"{schema}\",public"
    cursor.execute(set_cmd)
    click.echo(f"execute: {set_cmd}")


def normalize_dbtype(dbtype):
    # kingbase8 -> kingbase
    if dbtype.startswith('kingbase'):
        return 'kingbasees'
    return dbtype


@cli.command(name='doc')
@click.pass_context
@option("--jdbc", "-j", help="jdbc url for host port database")
@option('--output', '-o', help='output file', default='db-doc.docx', show_default=True)
@option("--dbtype", "-t", type=click.Choice(['mysql', 'postgresql', 'doris', 'kingbasees']), help="database type", default="mysql")
@option("--host", "-h", help="database host")
@option("--port", "-p", help="database port")
@option("--user", "-u", help="database user")
@option("--password", "-pwd", help="database password")
@option("--schema", "-s", help="database schema")
@option("--database", "-d", help="database name")
@option("--open", help="open file after generate", is_flag=True, default=True)
@option("--template", help="ms word template file", default="default.docx")
@option("--include", help="include tables support regex", multiple=True)
@option("--exclude", help="exclude tables support regex", multiple=True)
def db_doc(ctx, jdbc, output, dbtype, host, port, user, password, schema, database, open, template, include, exclude):
    """
    生成数据库文档
    """

    ensure_file(output)
    output = os.path.abspath(output)


    if not host and not port and not jdbc and not database:
        use_jdbc = survey.routines.inquire("使用jdbc链接提供数据库信息? ", default=True)
        if use_jdbc:
            jdbc = survey.routines.input("请输入jdbc url: ")

    if jdbc:
        # jdbc:mysql://localhost:3306/test
        m = re.match(r'jdbc:(\w+):\/\/([\w\.-]+):(\d+)\/(\w+)', jdbc)
        if m:
            dbtype, host, port, database = m.groups()
            dbtype = normalize_dbtype(dbtype)
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
        db = read_mysql_db(host, port, user, password, database, schema, include, exclude)

    elif dbtype == 'postgresql' :
        db = read_postgresql_db(host, port, user, password, database, schema, include, exclude)
    elif dbtype == 'kingbasees':
        db = read_kingbase_db(host, port, user, password, database, schema, include, exclude)
    else:
        click.echo(f"不支持的数据库类型: {dbtype}")
        return

    gen_file(template, output, db)

    click.echo(f"文件生成成功: {output}")
    if open:
        os.startfile(output)


def ensure_file(output):
    if is_file_in_use(output):
        raise click.ClickException(f"文件: {output} 已被占用, 请关闭文件后再试")


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
