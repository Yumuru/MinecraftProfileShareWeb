import os
import json
import sys
from pathlib import Path

class Node:
    def __init__(self, data=None, is_section=False):
        self.children = []
        self.content = ""
        self.css_class = None
        self.is_item = False
        self.is_section = is_section
        
        if is_section:
            self.children = data if isinstance(data, list) else [data]
        else:
            self._parse_data(data)

    def _parse_data(self, data):
        if isinstance(data, dict):
            self.css_class = data.get("class")
            self.is_item = "item" in data
            
            # childrenがある場合、コンテナとして子を保持する
            if "children" in data:
                self.children.extend(parse_json_to_tree(data["children"]))

            parts = []
            for k, v in data.items():
                if k in ["class", "children"]: continue
                if k in ["item", "text"]:
                    res = self._dispatch_value(v)
                    if res: parts.append(res)
                elif k == "link":
                    parts.append(self._format_link(v))
                else:
                    val = self._dispatch_value(v)
                    if val: parts.append(f"{k} : {val}")
                    else: parts.append(f"{k} :")
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

def parse_json_to_tree(data):
    if isinstance(data, list):
        nodes = []
        for item in data:
            if isinstance(item, list):
                if nodes and not nodes[-1].is_section and not nodes[-1].children:
                    nodes[-1].children.extend(parse_json_to_tree(item))
                else:
                    section_content = parse_json_to_tree(item)
                    nodes.append(Node(section_content, is_section=True))
            else:
                nodes.append(Node(item))
        return nodes
    return [Node(data)]

def node_to_html(node, indent_level=0):
    indent = "  " * indent_level
    class_attr = f' class="{node.css_class}"' if node.css_class else ''
    
    # 1. セクション（リスト）
    if node.is_section:
        html = f"{indent}<div class=\"indent\">\n"
        for child in node.children:
            html += node_to_html(child, indent_level + 2)
        html += f"{indent}</div>\n"
        return html

    # 2. コンテナ（childrenをまとめるdiv）
    # contentが空で、childrenがある場合は、クラスを適用した器を作る
    if not node.content and node.children:
        html = f"{indent}<div{class_attr}>\n"
        for child in node.children:
            html += node_to_html(child, indent_level + 2)
        html += f"{indent}</div>\n"
        return html

    # 3. 通常の1行
    if not node.content: return ""
    
    prefix = "・ " if node.is_item else ""
    # ここから suffix (コロン足し算) を完全に削除したよ
    html = f"{indent}<div{class_attr}>{prefix}{node.content}</div>\n"
    
    # 子要素があれば、その直下にインデントブロックを作る
    if node.children:
        html += f"{indent}<div class=\"indent\">\n"
        for child in node.children:
            html += node_to_html(child, indent_level + 2)
        html += f"{indent}</div>\n"
        
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
<link rel="stylesheet" href="../docs/style.css">
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


if __name__ == "__main__":
    # 入力と出力のディレクトリ設定
    input_dir = Path('jsons')
    output_dir = Path('to_htmls')

    # 出力フォルダがなければ作成するよ
    output_dir.mkdir(parents=True, exist_ok=True)

    # jsonsフォルダが存在するかチェック
    if not input_dir.exists() or not input_dir.is_dir():
        print(f"エラー: フォルダ '{input_dir}' が見つかりません。")
        sys.exit(1)

    # フォルダ内の .json ファイルをループで処理
    json_files = list(input_dir.glob('*.json'))
    
    if not json_files:
        print("処理するJSONファイルが見つからなかったよ。")
        sys.exit(0)

    print(f"{len(json_files)} 個のファイルを処理するね！")

    for json_path in json_files:
        # 出力ファイル名を決定 (拡張子を .html に変えて output_dir へ)
        output_path = output_dir / json_path.with_suffix('.html').name
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # HTMLを生成
            json_to_html(data, str(output_path))
            print(f"成功: {json_path.name} -> {output_path.name}")
            
        except json.JSONDecodeError:
            print(f"エラー: '{json_path.name}' は有効なJSONじゃないみたい。")
        except Exception as e:
            print(f"予期せぬエラー ({json_path.name}): {e}")

    print("\n全部の処理が終わったよ！")
