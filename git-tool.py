import os
from email.policy import default

import click
import gitlab
import prompt_toolkit
from click import option, argument

from git import Repo, InvalidGitRepositoryError
import survey
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
import json


def all_branches(repo):
    branches = repo.branches
    return [b.name for b in branches]


@click.group()
@option('--repo', '-r', default='.', help='git repository path', type=click.Path(exists=True))
@click.pass_context
def cli(ctx, repo):
    try:
        ctx.obj = Repo(repo)
    except InvalidGitRepositoryError as e:
        raise click.ClickException(f"不是一个有效的git仓库: {repo}") from e


@cli.command()
@option('--source', '-s', help='source branch')
@option('--push', '-p', is_flag=True, help='push branch', default=True)
@click.pass_context
def feature(ctx, source, push):
    """
    创建新的feature分支

    """
    repo = ctx.obj

    branches = all_branches(repo)

    # 选中默认分支为 main / master
    branches = sorted(branches, key=lambda x: x == 'main' or x == 'master', reverse=True)

    source_branch = source if source else branches[survey.routines.select("选择源分支: ", options=branches)]

    feature_name = survey.routines.input("输入新的feature分支名称: ")

    repo.git.checkout(source_branch)

    # pull source branch

    repo.git.pull()

    # create new feature branch

    repo.git.checkout('-b', f'feature/{feature_name}')

    # push feature branch

    if push:
        repo.git.push('-u', 'origin', f'feature/{feature_name}')
    else:
        click.echo(f"请手动push分支 feature/{feature_name}")
    # print success message

    click.echo(f"新的feature分支feature/{feature_name}创建成功, 源分支为{source_branch}")


@cli.command()
@option('--source', '-s', help='source branch')
@option('--push', '-p', is_flag=True, help='push branch', default=True)
@click.pass_context
def hotfix(ctx, source, push):
    """
     创建新的hotfix分支

     """

    repo = ctx.obj

    branches = all_branches(repo)

    # 选中默认分支为 main / master
    branches = source if source else sorted(branches, key=lambda x: x == 'prod' or x == 'prd', reverse=True)

    source_branch = branches[survey.routines.select("选择源分支: ", options=branches)]

    hotfix_name = survey.routines.input("输入新的hotfix分支名称: ")

    repo.git.checkout(source_branch)

    # pull source branch

    repo.git.pull()

    # create new feature branch

    repo.git.checkout('-b', f'hotfix/{hotfix_name}')

    # push feature branch

    if push:
        repo.git.push('-u', 'origin', f'hotfix/{hotfix_name}')
    else:
        click.echo(f"请手动push分支 hotfix/{hotfix_name}")
    # print success message

    click.echo(f"新的hotfix分支hotfix/{hotfix_name}创建成功, 源分支为{source_branch}")

    pass


@cli.command()
@option('--source', '-s', help='source branch')
@option('--target', '-t', help='target branch')
@option('--push', '-p', is_flag=True, help='push branch', default=True)
@click.pass_context
def rebase(ctx, source, target, push):
    """
    rebase分支

    """
    repo = ctx.obj

    branches = all_branches(repo)

    # 如果当前分支为feature分支, 则默认rebase main or master

    # 如果当前分支为hotfix分支, 则默认rebase prod or prd

    source_branch = source if source else repo.active_branch.name
    target_branch = target

    if not target_branch:
        if source_branch.startswith('feature/'):
            target_branch = find_main(repo, branches)
        elif source_branch.startswith('hotfix/'):
            target_branch = find_prod(repo, branches)
        else:
            #         未知分支 异常退出
            raise Exception("请指定目标分支")

    if not target_branch:
        raise Exception("未找到目标分支")

    if not source or not target:
        confirm = survey.routines.inquire(f"请确认rebase分支 {source_branch} <- {target_branch}  ", default=True)
        if not confirm:
            click.echo("取消rebase分支")
            return
    else:
        click.echo(f"开始rebase分支 {source_branch} <- {target_branch}")

    repo.git.checkout(source_branch)

    repo.git.pull()

    repo.git.rebase(target_branch)
    if push:
        repo.git.push('origin', source_branch, '-f')
    else:
        click.echo(f"请手动push分支 {source_branch}")
    click.echo(f"分支rebase成功 {source_branch} <- {target_branch}")


def find_prod(repo, branches):
    if 'prod' in branches and 'prd' in branches:
        # 判断最后一次提交的时间， 选择最新的分支
        prod = repo.branches['prod']
        prd = repo.branches['prd']
        if prod.commit.committed_date > prd.commit.committed_date:
            return 'prod'
        else:
            return 'prd'

    return 'prod' if 'prod' in branches else 'prd' if 'prd' in branches else ''


def find_main(repo, branches):
    if 'main' in branches and 'master' in branches:
        # 判断最后一次提交的时间， 选择最新的分支
        main = repo.branches['main']
        master = repo.branches['master']
        if main.commit.committed_date > master.commit.committed_date:
            return 'main'
        else:
            return 'master'

    return 'main' if 'main' in branches else 'master' if 'master' in branches else ''


@cli.command()
@option('--source', '-s', help='source branch')
@option('--target', '-t', help='target branch')
@option('--push', '-p', is_flag=True, help='push branch', default=True)
@click.pass_context
def merge(ctx, source, target, push):
    """
    合并分支


    """
    repo = ctx.obj

    branches = all_branches(repo)

    # 如果当前分支为feature分支, 则默认合并到dev分支

    # 如果当前分支为hotfix分支, 则默认合并到prod分支

    # 如果当前分支为prod分支, 则默认合并到main分支

    source_branch = source if source else repo.active_branch.name
    target_branch = target

    if not target_branch:
        if source_branch.startswith('feature/'):
            target_branch = 'dev' if 'dev' in branches else ''
        elif source_branch.startswith('hotfix/'):
            target_branch = 'prod' if 'prod' in branches else 'prd' if 'prd' in branches else ''
        elif source_branch == 'prod':
            target_branch = 'main' if 'main' in branches else 'master' if 'master' in branches else ''
        else:
            #         未知分支 异常退出
            raise Exception("请指定目标分支")

    if not target_branch:
        raise Exception("未找到目标分支")

    if not source or not target:
        confirm = survey.routines.inquire(f"请确认合并分支 {source_branch} -> {target_branch}  ", default=True)
        if not confirm:
            click.echo("取消合并分支")
            return
    else:

        click.echo(f"开始合并分支 {source_branch} -> {target_branch}")

    repo.git.checkout(target_branch)

    repo.git.pull()

    repo.git.merge(source_branch)

    if push:
        repo.git.push('origin', target_branch)
    else:
        click.echo(f"请手动push分支 {target_branch}")

    click.echo(f"分支合并成功 {source_branch} -> {target_branch}")



@cli.command(name="sb")
@option('--source', '-s', help='source branch')
@option('--push', '-p', is_flag=True, help='push branch', default=True)
@click.pass_context
def create_standard_branches(ctx, source,  push):
    """
    创建标准分支 master dev prev prod
    """
    repo = ctx.obj

    branches = all_branches(repo)

    targets = ['master', 'dev', 'prev', 'prod']

    # 排除已经存在的分支

    targets = [t for t in targets if t not in branches]


    if not targets:
        click.echo("标准分支已经存在")
        return
    indexes  = survey.routines.basket("选择需要创建的分支: ", options=targets)

    targets = [targets[i] for i in indexes]

    if not source:
        source = find_main(repo, branches)

    if not source:
        source = branches[survey.routines.select("请选择源分支: ", options=branches)]

    for target in targets:
        repo.git.checkout(source)
        repo.git.pull()
        repo.git.checkout('-b', target)
        if push:
            repo.git.push('-u', 'origin', target)
        else:
            click.echo(f"请手动push分支 {target}")
        click.echo(f"新的分支{target}创建成功, 源分支为{source}")


def load_config():
    """加载配置文件"""
    config_path = os.path.expanduser('~/.git-tool.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    """保存配置文件"""
    config_path = os.path.expanduser('~/.git-tool.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

@cli.command(name="clone")
@option('--url', '-u', help='gitlab url')
@option('--token', '-t', help='gitlab token')
@option('--namespace', '-n', help='gitlab namespace')
@option('--dir', '-d', help='destination directory')
@option('--ssh', is_flag=True, help='use ssh protocol', default=True)
@click.pass_context
def clone(ctx, url, token, namespace, dir, ssh):
    """
    从gitlab clone 仓库
    """
    # 加载配置
    config = load_config()
    
    if not url:
        url = os.getenv('GITLAB_URL') or config.get('gitlab_url') or survey.routines.input("请输入gitlab url: ")
    
    if not token:
        token = os.getenv('GITLAB_TOKEN') or config.get('gitlab_token') or survey.routines.input("请输入gitlab token: ")
    
    if not dir:
        dir = os.getenv('GITLAB_DIR') or config.get('gitlab_dir') or survey.routines.input("请输入目标目录: ")

    # 保存新的配置
    if url != config.get('gitlab_url') or token != config.get('gitlab_token'):
        config['gitlab_url'] = url
        config['gitlab_token'] = token
        config['gitlab_dir'] = dir
        save_config(config)

    gl = gitlab.Gitlab(url=url, private_token=token, keep_base_url=True)
    
    # 搜索项目
    search_term = survey.routines.input("请输入要搜索的仓库名称: ")
    projects = gl.search('projects', search_term)
    
    if not projects:
        click.echo("未找到匹配的仓库")
        return
        
    # 格式化项目列表供选择
    project_options = []
    for p in projects:
        project = gl.projects.get(p['id'])  # 获取完整的项目信息
        project_options.append(f"{project.path_with_namespace} ({project.description or '无描述'})")
    
    selected_index = survey.routines.select("请选择要克隆的仓库: ", options=project_options)
    selected_project = gl.projects.get(projects[selected_index]['id'])
    
    # 确定克隆目录
    if not dir:
        dir = os.getcwd()
    
    clone_path = os.path.join(dir, selected_project.path)
    confirm = survey.routines.inquire(f"是否克隆到目录 {clone_path}?", default=True)
    if not confirm:
        clone_path = survey.routines.input("请输入目标目录: ")

    
    
    # 执行克隆
    clone_url = selected_project.ssh_url_to_repo if ssh else selected_project.http_url_to_repo
    click.echo(f"正在克隆仓库 {selected_project.path_with_namespace} 到 {clone_path}")
    click.echo(f"使用{('SSH' if ssh else 'HTTP')}协议: {clone_url}")
    Repo.clone_from(clone_url, clone_path)
    click.echo(f"仓库克隆完成")


if __name__ == '__main__':
    cli()
