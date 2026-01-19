import json
import sys

class Node:
    def __init__(self, data, css_class=None, is_section=False):
        self.children = []
        self.content = ""
        self.css_class = css_class
        self.is_item = False
        self.is_section = is_section
        
        if not is_section:
            self._parse_data(data)
        else:
            self.children = data

    def _parse_data(self, data):
        if isinstance(data, dict):
            self.css_class = data.get("class", self.css_class)
            self.is_item = "item" in data
            parts = []
            for k, v in data.items():
                if k == "class": continue
                
                if k == "item" or k == "text":
                    res = self._dispatch_value(v)
                    if res: parts.append(res)
                elif k == "link":
                    parts.append(self._format_link(v))
                else:
                    val = self._dispatch_value(v)
                    if val:
                        # key : value 全体をcontentにする
                        parts.append(f"{k} : {val}")
                    else:
                        # key : null の場合、「key :」までをcontentにする
                        # これでクラス適用のspan内に「 :」が含まれる
                        parts.append(f"{k} :")
            
            self.content = " ".join(parts)
        else:
            self.content = str(data)

    def _dispatch_value(self, v):
        if v is None: return None
        if isinstance(v, dict):
            if "link" in v: return self._format_link(v["link"])
            inner = [f"{sk}: {self._dispatch_value(sv)}" for sk, sv in v.items() if sv]
            return ", ".join(inner) if inner else None
        return str(v)

    def _format_link(self, l):
        if not l: return ""
        return f'<a href="{l.get("href")}">{l.get("name")}</a>'

def parse_json_to_tree(data, css_class=None):
    if isinstance(data, list):
        nodes = []
        for item in data:
            if isinstance(item, list):
                section_content = parse_json_to_tree(item, css_class)
                nodes.append(Node(section_content, css_class, is_section=True))
            else:
                nodes.append(Node(item, css_class))
        return nodes
    return [Node(data, css_class)]

def node_to_html(node, indent_level=0):
    indent = "  " * indent_level
    
    if node.is_section:
        # リストに由来するインデントブロック
        html = f"{indent}<div class=\"indent\">\n"
        for child in node.children:
            html += node_to_html(child, indent_level + 2)
        html += f"{indent}</div>\n"
    else:
        # 辞書や文字列に由来する「1行」の div
        if not node.content: return ""
        
        class_attr = f' class="{node.css_class}"' if node.css_class else ''
        # item の場合は行頭に「・ 」を置く
        prefix = "・ " if node.is_item else ""
        
        # 子（リスト）を持っている場合は見出しとして「 :」を添える
        suffix = " :" if node.children else ""
        
        # 1行を丸ごと div で包む
        html = f"{indent}<div{class_attr}>{prefix}{node.content}{suffix}</div>\n"
            
    return html

def json_to_html(json_data, output_file="output.html"):
    """JSONデータからHTMLファイルを生成"""
    
    # JSONを木構造に変換
    tree = parse_json_to_tree(json_data)
    
    # HTMLヘッダー (省略せずそのまま維持)
    html = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>Minecraft Mod構成 1.20.1</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div id="outer">
<header>
<div class="header-inner">
<h1>Minecraft Mod構成 1.20.1</h1>
</div>
</header>
<div id="content">
<div class="inner">
"""

    # --- 修正箇所: treeの型に関わらず再帰的にHTML化 ---
    if isinstance(tree, list):
        for node in tree:
            html += node_to_html(node, 1)
    else:
        html += node_to_html(tree, 1)

    # HTMLフッター
    html += """</div>
</div>
<footer>© 2010 あなたのホームページ</footer>
</div>
</body>
</html>
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"HTMLファイルを生成しました: {output_file}")


# 使用例
if __name__ == "__main__":
    # コマンドライン引数の処理
    if len(sys.argv) < 2:
        print("使用方法: python json_to_html.py <入力JSONファイル> [出力HTMLファイル]")
        print("例: python json_to_html.py mod_config.json minecraft_mod_config.html")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'output.html'
    
    # JSONファイルを読み込み
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # HTMLを生成
        json_to_html(data, output_file)
    except FileNotFoundError:
        print(f"エラー: ファイル '{input_file}' が見つかりません")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"エラー: '{input_file}' は有効なJSONファイルではありません")
        sys.exit(1)
