import re
def transform_league_name(league_name):
        """
        标准化联赛名称
        移除括号内容及特殊字符,并转为小写
        """
        if not league_name:
            return ''

        # 移除各种括号及括号内的内容
        league_name = re.sub(r'\([^)]*\)', '', league_name)  # 圆括号 ()
        league_name = re.sub(r'\[[^\]]*\]', '', league_name)  # 方括号 []
        league_name = re.sub(r'\{[^}]*\}', '', league_name)  # 花括号 {}
        league_name = re.sub(r'<[^>]*>', '', league_name)     # 尖括号 <>

        # 移除引号类字符
        league_name = league_name.replace('"', '')
        league_name = league_name.replace("'", '')
        league_name = league_name.replace('`', '')

        # 移除特殊符号
        league_name = league_name.replace('.', ' ')
        league_name = league_name.replace(',', ' ')
        league_name = league_name.replace('-', '')
        league_name = league_name.replace('_', '')
        league_name = league_name.replace('\\', '')
        league_name = league_name.replace('/', '')
        league_name = league_name.replace('&', '')
        league_name = league_name.replace('+', '')
        league_name = league_name.replace('*', '')
        league_name = league_name.replace('#', '')
        league_name = league_name.replace('@', '')
        league_name = league_name.replace('|', '')
        league_name = league_name.replace('~', '')
        league_name = league_name.replace('–', '')  # en dash
        league_name = league_name.replace('—', '')  # em dash

        # 移除所有空格
        league_name = league_name.replace(' ', '')

        # 转为小写并去除首尾空格
        league_name = league_name.lower()
        league_name = league_name.strip()

        return league_name

if __name__ == "__main__":
    print(transform_league_name("Primera A, Clausura"))
    