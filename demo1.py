from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style

if __name__ == "__main__":
    # 创建自动建议对象，通过历史记录为用户提供自动建议
    auto_suggest = AutoSuggestFromHistory()

    # 定义自动补全选项
    completer = WordCompleter(['搜索', '查找', '查询'], ignore_case=True)

    # 定义样式
    style = Style.from_dict({
        # User input (default text).
        '':          '#ff0066',
        # Prompt.
        'pound':     '#00aa00',
    })

    # 创建提示会话对象
    session = PromptSession('搜索：', style=style, completer=completer, auto_suggest=auto_suggest)

    while True:
        try:
            # 获取用户输入
            user_input = session.prompt()
            print(f'您输入的是：{user_input}')
        except KeyboardInterrupt:
            # 按Ctrl+C退出
            break
        except EOFError:
            # 按Ctrl+D退出
            break