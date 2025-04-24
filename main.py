import sys
import os
import imghdr
import time

from getopt import getopt

from steganography import Steganography

ACCEPTED_FORMATS = ['jpeg', 'png']

s = Steganography()


def main():
    action = None
    img_path = None
    message = None
    password = None

    # 读取参数
    if len(sys.argv) > 1:
        # 如果命令行中包含执行动作
        if sys.argv[1].lower() in ['encode', 'decode']:
            action = sys.argv[1].lower()
            opts, _ = getopt(sys.argv[2:], "i:f:m:p:b:e:")

            for opt in opts:
                if opt[0] == '-i':
                    img_path = opt[1]
                    if not is_valid_image(img_path):
                        exit()

                elif opt[0] == '-f':
                    path = opt[1]
                    if not is_valid_textfile(path):
                        exit()
                    with open(path, 'r', encoding='utf-8') as file:
                        message = file.read()

                elif opt[0] == '-m':
                    message = opt[1]

                elif opt[0] == '-p':
                    password = opt[1]

                elif opt[0] == '-b':
                    bits = opt[1]
                    if bits.isnumeric() and int(bits) <= 8:
                        s.BITS = int(bits)
                    else:
                        print('\033[0;31m无效的位数。\033[0m')
                        exit()

                elif opt[0] == '-e':
                    padding = opt[1]
                    if padding.isnumeric():
                        s.EOF_LENGTH = int(padding)
                    else:
                        print('\033[0;31m无效的填充长度。\033[0m')
                        exit()

        # 无指定动作
        else:
            opts, _ = getopt(sys.argv[1:], "b:e:")
            for opt in opts:
                if opt[0] == '-b':
                    bits = opt[1]
                    if bits.isnumeric() and int(bits) <= 8:
                        s.BITS = int(bits)
                    else:
                        print('\033[0;31m无效的位数。\033[0m')
                        exit()

                elif opt[0] == '-e':
                    padding = opt[1]
                    if padding.isnumeric():
                        s.EOF_LENGTH = int(padding)
                    else:
                        print('\033[0;31m无效的填充长度。\033[0m')
                        exit()

            if not ('bits' in locals() or 'padding' in locals()):
                print_help()
                exit()


    if not action:
        action = choose_action()

    # 加密
    if action == 'encode':
        if not img_path:
            img_path = choose_image(ACCEPTED_FORMATS)

        if not message:
            message = choose_message()

        if not password:
            password = choose_password('是否需要加密消息？')

        print('\n\033[1;2m正在加密...\033[0m')

        outfile_name = s.encode(img_path, message, password)

        print('\033[1;32m图片加密成功！\033[0m')
        print(f'\n加密后的图片为：\033[1m{outfile_name}\033[0m\n')

    # 解密
    elif action == 'decode':
        if not img_path:
            img_path = choose_image(['png'])

        if not password:
            password = choose_password('消息是否加密？')

        print('\n\033[1;2m正在解密...\033[0m')

        decoded_message = s.decode(img_path, password)

        print('\033[1;32m图片解密成功！\033[0m')
        print(f'\n\033[1m隐藏的消息如下：\033[0m')
        print(decoded_message, '\n')


def choose_action() -> str:
    """询问用户选择的操作（加密、解密）。

    返回:
        action (str): 用户选择的操作。
    """
    while True:
        print("""
\033[1m请选择操作：\033[0m
    [1]\033[0;3m 加密\033[0m
    [2]\033[0;3m 解密\033[0m
    [3]\033[0;3m 设置\033[0m
    [4]\033[0;3m 帮助\033[0m
    [0]\033[0;3m 退出\033[0m
    """)

        a = None
        while a not in ['1', '2', '3', '4', '0']:
            a = input('> ')

        if a == '0':
            exit()
        elif a == '1':
            return 'encode'
        elif a == '2':
            return 'decode'
        elif a == '3':
            settings()
        elif a == '4':
            print_help()
            exit()


def settings():
    """显示设置菜单。"""
    while True:
        print("""
\033[1m设置：\033[0m
    [1]\033[0;3m 修改隐藏信息的位数\033[0m
    [2]\033[0;3m 修改消息填充的长度\033[0m
    [0]\033[0;3m 退出\033[0m
            """)

        s_input = None
        while s_input not in ['1', '2', '0']:
            s_input = input('> ')

        if s_input == '0':
            exit()
        elif s_input == '1':
            choose_bits()
            break
        elif s_input == '2':
            choose_padding()
            break


def choose_bits():
    """询问用户用于隐藏消息的位数并进行更新。"""
    while True:
        n = input("\n\033[1m请输入用于隐藏消息的位数：\033[0;2m(默认值为2; 最大8; 0退出)\033[0m ")

        if n == '0':
            exit()
        elif n.isnumeric() and int(n) <= 8:
            s.BITS = int(n)
            print('\033[0;32m隐藏消息的位数更新成功！\033[0m')
            break


def choose_padding():
    """询问用户消息填充的零的数量并进行更新。"""
    while True:
        n = input("\n\033[1m请输入消息填充中零的数量：\033[0;2m(默认值为16; 0退出)\033[0m ")

        if n == '0':
            exit()
        elif n.isnumeric():
            s.EOF_LENGTH = int(n)
            print('\033[0;32m消息填充长度更新成功！\033[0m')
            break


def choose_image(accepted_formats: list) -> str:
    """询问用户图片路径。

    参数:
        accepted_formats (list): 可接受的图片格式列表。

    返回:
        img_path (str): 选择的图片路径。
    """
    while True:
        path = input('\n\033[1m请输入图片路径：\033[0;2m(0退出)\033[0m ')

        if path == '0':
            exit()

        elif is_valid_image(path, accepted_formats):
            time.sleep(0.5)
            print('\033[0;32m✓ 图片有效。\033[0m')
            time.sleep(0.5)
            break

    return path


def is_valid_image(image_path: str, accepted_formats: list = ACCEPTED_FORMATS) -> bool:
    """验证用户给定的图片路径是否有效。

    参数:
        image_path (str): 图片路径。
        accepted_formats (list): 可接受的图片格式列表。

    返回:
        is_valid (bool): 图片是否有效。
    """
    if not os.path.isfile(image_path):
        print(f'\033[0;31m文件 "{os.path.abspath(image_path)}" 不存在。\033[0m')
        return False

    elif imghdr.what(image_path) not in accepted_formats:
        print(f'\033[0;31m文件 "{image_path}" 格式无效。\033[0m')
        print(f'\033[0;31m可接受的格式：', ', '.join(accepted_formats), '\033[0m')
        return False

    return True


def choose_message() -> str:
    """询问用户选择消息内容。

    返回:
        message (str): 用户输入的消息。
    """
    while True:
        print("""
\033[1m请选择消息类型：\033[0m
    [1]\033[0;3m 文字\033[0m
    [2]\033[0;3m 文本文件\033[0m
    [0]\033[0;3m 退出\033[0m
""")
        m = None
        while m not in ['1', '2', '0']:
            m = input('> ')

        if m == '0':
            exit()

        elif m == '1':
            text = input('\n\033[1m请输入消息：\033[0;2m(0退出)\033[0m ')
            if text == '0':
                exit()

            return text

        elif m == '2':
            while True:
                path = input('\n\033[1m请输入文本文件路径：\033[0;2m(0退出)\033[0m ')

                if path == '0':
                    exit()

                elif is_valid_textfile(path):
                    time.sleep(0.5)
                    print('\033[0;32m✓ 文本文件有效。\033[0m')
                    time.sleep(0.5)
                    break

            with open(path, 'r', encoding='utf-8') as file:
                return file.read()


def is_valid_textfile(textfile_path: str) -> bool:
    """验证用户给定的文本文件路径是否有效。

    参数:
        textfile_path (str): 文本文件路径。

    返回:
        is_valid (bool): 文件路径是否有效。
    """
    if not os.path.isfile(textfile_path):
        print(f'\033[0;31m文件 "{os.path.abspath(textfile_path)}" 不存在。\033[0m')
        return False

    elif not textfile_path.endswith('.txt'):
        print(f'\033[0;31m文件 "{textfile_path}" 不是 .txt 文件。\033[0m')
        return False

    return True


def choose_password(message: str) -> str:
    """询问用户输入加密密码。

    参数:
        message (str): 提示信息。

    返回:
        password (str | None): 用户输入的密码。
    """
    while True:
        print(f"""
\033[1m{message}\033[0m
    [1]\033[0;3m 是\033[0m
    [2]\033[0;3m 否\033[0m
    [0]\033[0;3m 退出\033[0m
""")
        p = None
        while p not in ['1', '2', '0']:
            p = input('> ')

        if p == '0':
            exit()

        elif p == '1':
            password = input('\n\033[1m请输入密码：\033[0;2m(0退出)\033[0m ')
            if password == '0':
                exit()

            return password

        elif p == '2':
            return None


def print_help():
    """打印帮助信息。"""
    print(f"""
\033[1m隐写术\033[0m

本程序允许您使用 LSB 算法在图片中隐藏消息，利用图片像素的最低有效位来存储数据。
更多信息请查看 GitHub 仓库：https://github.com/francesco-dorati/steganograpy

\033[1m用法：\033[0m
    {sys.argv[0]} [encode [-i 图片路径] [-f 文本文件 | -m 消息] [-p 密码]] [-b 位数] [-e 填充长度]
    {sys.argv[0]} [decode [-i 图片路径] [-p 密码]] [-b 位数] [-e 填充长度]

\033[1m参数：\033[0m
    -i 图片路径      要加密/解密的图片路径。
    -f 文本文件      要隐藏的文本文件 (.txt)。
    -m 消息          要隐藏的消息内容。
    -p 密码          用于加密/解密隐藏消息的密码。
    -b 位数          用于隐藏消息的图片像素位数。
    -e 填充长度      消息结束标识的填充长度（零的数量）。
    """)



if __name__ == '__main__':
    main()