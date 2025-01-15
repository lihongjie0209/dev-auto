
import click
from click import option, argument

from git import Repo, InvalidGitRepositoryError
import survey


def all_branches(repo):
    branches = repo.branches
    return [b.name for b in branches]


@click.group()
@argument('repo', default='.', type=click.Path(exists=True))
@click.pass_context
def cli(ctx, repo):
    try:
        ctx.obj = Repo(repo)
    except InvalidGitRepositoryError as e:
        raise click.ClickException(f"不是一个有效的git仓库: {repo}") from e


@cli.command()
@option('--source', '-s', help='source branch')
@option('--push', '-p', is_flag=True, help='push branch', default=False)
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
@option('--push', '-p', is_flag=True, help='push branch', default=False)
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
@option('--push', '-p', is_flag=True, help='push branch', default=False)
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
@option('--push', '-p', is_flag=True, help='push branch', default=False)
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


if __name__ == '__main__':
    cli()
