class Steganography:
    try:
        from PIL import Image
    except ImportError:
        print('Missing packages, run `python3 -m pip install --upgrade -r requirements.txt`')
        exit(1)

    def __init__(self, eof=16, bits=2):
        """初始化隐写术对象

        参数:
            eof (int, optional): 隐藏消息末尾的零的数量。默认为 16。
            bits (int, optional): 用于隐藏消息的位数。默认为 2。
        """
        self.EOF_LENGTH = eof
        self.BITS = bits

    def encode(self, img_path: str, text: str, password: str = None) -> str:
        """使用 LSB 算法将文本隐藏在图片中。

        参数:
            img_path (str): 图片路径。
            text (str): 要隐藏的文本。
            password (str, optional): 用于加密文本的密码。默认为 None。

        返回:
            out_name (str): 生成的隐藏消息图片的文件名。
        """
        out_name = 'out.png'

        # 加载图片
        img = self.Image.open(img_path)
        out = self.Image.new("RGBA", img.size, 0xffffff)

        # 加密
        if password:
            # 增加错误处理，避免解码过程中因非法字节报错
            text = self.__encrypt(text, password)

        # 文本转换为二进制
        binary = list(self.__to_binary(text) + ('0' * self.EOF_LENGTH))

        # 遍历图片像素
        width, height = img.size
        for x in range(width):
            for y in range(height):
                # 读取像素
                if img.format == 'PNG':
                    r, g, b, a = img.getpixel((x, y))
                else:
                    r, g, b = img.getpixel((x, y))

                # 修改像素
                new_colors = []
                for color in (r, g, b):
                    if not binary:
                        new_colors.append(color)
                        continue

                    binary_color = bin(color)[:-self.BITS]
                    for _ in range(self.BITS):
                        if binary:
                            binary_color += binary.pop(0)
                        else:
                            binary_color += '0'

                    new_colors.append(int(binary_color, 2))

                # 将修改后的像素写入新图片
                if img.format == 'PNG':
                    out.putpixel((x, y), (*new_colors, a))
                else:
                    out.putpixel((x, y), (*new_colors, 255))

        # 保存新图片
        out.save(out_name)

        # 关闭图片
        img.close()
        out.close()

        return out_name

    def decode(self, img_path: str, password: str = None) -> str:
        """从图片中提取隐藏消息。

        参数:
            img_path (str): 包含隐藏消息的图片路径。
            password (str, optional): 隐藏消息的加密密码。默认为 None。

        返回:
            message (str): 隐藏消息文本。
        """
        binary = ''

        # 加载图片
        img = self.Image.open(img_path)

        # 检查图片格式
        if img.format != 'PNG':
            print('无效的图片格式。')
            exit(1)

        # 遍历图片像素
        width, height = img.size
        has_message_ended = False
        for x in range(width):
            for y in range(height):
                # 获取像素值
                r, g, b, _ = img.getpixel((x, y))

                # 从像素值中提取消息二进制信息
                for color in (r, g, b):
                    binary += format(color, '#010b')[-self.BITS:]
                    has_message_ended = binary[-self.EOF_LENGTH:] == ('0' * self.EOF_LENGTH)
                    if has_message_ended:
                        break
                if has_message_ended:
                    break
            if has_message_ended:
                break

        # 移除填充
        text = self.__to_text(binary[:-self.EOF_LENGTH])

        # 解密
        if password:
            text = self.__decrypt(text, password)

        return text

    def __to_binary(self, text: str) -> str:
        """将文本转换为二进制字符串。

        参数:
            text (str): 要转换的文本。

        返回:
            binary (str): 文本对应的二进制字符串。
        """
        binary = ''
        encoded_text = text.encode('utf-8', errors='replace')
        for word in encoded_text:
            binary += format(word, '#010b')[2:]
        return binary

    def __to_text(self, binary: str) -> str:
        """将二进制字符串转换为文本。

        参数:
            binary (str): 二进制字符串。

        返回:
            text (str): 对应的文本。
        """
        text = ''
        while binary:
            byte = binary[:8]
            try:
                char = chr(int(byte, 2))
            except Exception:
                char = '?'
            text += char
            binary = binary[8:]
        return text

    def __encrypt(self, text: str, password: str) -> str:
        """使用 SHA256 对文本进行加密。

        参数:
            text (str): 要加密的文本。
            password (str): 加密密码。

        返回:
            encrypted_text (str): 加密后的文本。
        """
        try:
            import base64
            from cryptography.fernet import Fernet
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        except ImportError:
            print('缺少必要的包，请运行 `python3 -m pip install --upgrade -r requirements.txt`')
            exit(1)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'',
            iterations=100000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8', errors='replace')))
        try:
            encrypted_bytes = Fernet(key).encrypt(text.encode('utf-8', errors='replace'))
            # Fernet 加密返回的是 base64 格式的 bytes，可安全解码为 UTF-8
            return encrypted_bytes.decode('utf-8', errors='replace')
        except Exception as e:
            print('加密时发生错误:', e)
            exit(1)

    def __decrypt(self, encrypted_text: str, password: str) -> str:
        """使用 SHA256 解密已加密的文本。

        参数:
            encrypted_text (str): 已加密的文本。
            password (str): 解密密码。

        返回:
            text (str): 解密后的文本。
        """
        try:
            import base64
            from cryptography.fernet import Fernet, InvalidToken
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        except ImportError:
            print('缺少必要的包，请运行 `python3 -m pip install --upgrade -r requirements.txt`')
            exit(1)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'',
            iterations=100000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8', errors='replace')))
        try:
            decrypted_bytes = Fernet(key).decrypt(encrypted_text.encode('utf-8', errors='replace'))
            return decrypted_bytes.decode('utf-8', errors='replace')
        except InvalidToken:
            print('密码错误。')
            exit(1)
        except Exception as e:
            print('解密时发生错误:', e)
            exit(1)