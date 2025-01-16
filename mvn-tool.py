import glob

import click
from click import argument
from lxml import etree

import os

common_dep = [

    {
        "groupId": "org.springframework.boot",
        "artifactId": "spring-boot-starter-test",
        "scope": "test"
    },
    {
        "groupId": "org.instancio",
        "artifactId": "instancio-junit",
        "version": "5.2.1",
        "scope": "test"
    },
    {
        "groupId": "org.testcontainers",
        "artifactId": "kafka",
        "scope": "test"
    },

    {
        "groupId": "org.testcontainers",
        "artifactId": "mysql",
        "scope": "test"
    }, {

        "groupId": "io.vavr",
        "artifactId": "vavr",
        "version": "0.10.5"
    }

]


@click.group()
@argument('repo', default='.', type=click.Path(exists=True))
@click.pass_context
def cli(ctx, repo):
    ctx.obj = repo


def all_pom_file(repo):
    # 递归查找所有的pom文件
    return glob.glob(f'{repo}/**/pom.xml', recursive=True)


def add_common_dep(pom):
    click.echo(f"add common dep to {pom}")
    filtered_dep = []
    #     read pom file with lxml
    tree = etree.parse(pom)
    root = tree.getroot()
    dependencies = root.find('{http://maven.apache.org/POM/4.0.0}dependencies')
    if dependencies is None:
        dependencies = etree.Element('dependencies')
        root.append(dependencies)

    # if dep exists, skip
    for dep in dependencies:
        artifactId = dep.find('{http://maven.apache.org/POM/4.0.0}artifactId')
        groupId = dep.find('{http://maven.apache.org/POM/4.0.0}groupId')

        if artifactId is not None and groupId is not None:
            #         test if dep is in common_dep
            for common in common_dep:
                if common['artifactId'] == artifactId.text and common['groupId'] == groupId.text:
                    click.echo(f"skip {groupId.text}:{artifactId.text}")
                    break
            else:
                filtered_dep.append(dep)

    for dep in common_dep:
        dependency = etree.Element('dependency')
        for k, v in dep.items():
            child = etree.Element(k)
            child.text = v
            dependency.append(child)
        dependencies.append(dependency)
        click.echo(f"add {dep['groupId']}:{dep['artifactId']}")
    tree.write(pom, pretty_print=True, xml_declaration=True, encoding='UTF-8')


@cli.command()
@click.pass_context
def dep(ctx):
    """
    给pom文件中添加常用的依赖
    """
    repo = ctx.obj
    pom_files = all_pom_file(repo)
    for pom in pom_files:
        if '-bussiness' in pom or '-start' in pom:
            add_common_dep(pom)


if __name__ == '__main__':
    cli()
