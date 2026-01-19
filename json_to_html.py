import json
import sys

class Node:
    """木構造のノード"""
    def __init__(self, node_type="line", key=None, value=None, href=None, css_class=None):
        self.node_type = node_type  # "line" or "section"
        self.key = key
        self.value = value
        self.href = href
        self.css_class = css_class
        self.children = []
    
    def add_child(self, child):
        self.children.append(child)
        return child
    
    def __repr__(self):
        return f"Node(type={self.node_type}, key={self.key}, value={self.value}, class={self.css_class}, children={len(self.children)})"


def parse_json_to_tree(data):
    """JSONデータを木構造に変換"""
    nodes = []
    
    if isinstance(data, list):
        # 配列 = セクション
        section_node = Node(node_type="section")
        for item in data:
            child_nodes = parse_json_to_tree(item)
            if isinstance(child_nodes, list):
                for child in child_nodes:
                    section_node.add_child(child)
            else:
                section_node.add_child(child_nodes)
        return section_node
    
    elif isinstance(data, dict):
        # 辞書 = 一行の項目
        css_class = data.get("class", None)  # class属性を取得
        
        for key, value in data.items():
            if key == "class":
                # class属性はスキップ（他のキーで使用）
                continue
            
            if key == "item":
                # ・ アイテム
                if isinstance(value, dict):
                    if "link" in value:
                        # ・ <a>リンク</a>
                        link_data = value["link"]
                        node = Node(
                            node_type="line",
                            key="item_link",
                            value=link_data.get("name"),
                            href=link_data.get("href"),
                            css_class=css_class
                        )
                        nodes.append(node)
                    else:
                        # ・ キー : 値
                        for k, v in value.items():
                            node = Node(
                                node_type="line",
                                key="item_keyvalue",
                                value=k + (" : " + v if v else ""),
                                css_class=css_class
                            )
                            nodes.append(node)
                else:
                    # ・ 値
                    node = Node(
                        node_type="line",
                        key="item",
                        value=value,
                        css_class=css_class
                    )
                    nodes.append(node)
            
            elif key == "link":
                # リンク
                link_data = value
                node = Node(
                    node_type="line",
                    key="link",
                    value=link_data.get("name"),
                    href=link_data.get("href"),
                    css_class=css_class
                )
                nodes.append(node)

            elif key == "text":
                # text : 値
                node = Node(
                    node_type="line",
                    key="text",
                    value=value,
                    css_class=css_class
                )
                nodes.append(node)
            
            elif value is None:
                # キー :
                node = Node(
                    node_type="line",
                    key="header",
                    value=key,
                    css_class=css_class
                )
                nodes.append(node)
            
            elif isinstance(value, list):
                # キー : [セクション]
                header_node = Node(
                    node_type="line",
                    key="header",
                    value=key,
                    css_class=css_class
                )
                nodes.append(header_node)
                
                section_node = parse_json_to_tree(value)
                nodes.append(section_node)
            
            elif isinstance(value, dict):
                # キー : {...}
                if "link" in value:
                    # キー : <a>リンク</a>
                    link_data = value["link"]
                    node = Node(
                        node_type="line",
                        key="keyvalue_link",
                        value=key + " : " + link_data.get("name"),
                        href=link_data.get("href"),
                        css_class=css_class
                    )
                    nodes.append(node)
                else:
                    # キー : (ネストされた辞書を展開)
                    header_node = Node(
                        node_type="line",
                        key="header",
                        value=key,
                        css_class=css_class
                    )
                    nodes.append(header_node)
                    
                    child_nodes = parse_json_to_tree(value)
                    if isinstance(child_nodes, list):
                        section_node = Node(node_type="section")
                        for child in child_nodes:
                            section_node.add_child(child)
                        nodes.append(section_node)
                    else:
                        nodes.append(child_nodes)
            
            elif isinstance(value, str):
                # キー : 値
                node = Node(
                    node_type="line",
                    key="keyvalue",
                    value=key + " : " + value,
                    css_class=css_class
                )
                nodes.append(node)
    
    elif isinstance(data, str):
        # 文字列
        node = Node(
            node_type="line",
            key="text",
            value=data
        )
        nodes.append(node)
    
    return nodes if len(nodes) != 1 else nodes[0]


def node_to_html(node, indent_level=0):
    """木構造のノードをHTMLに変換"""
    html = ""
    indent = "  " * indent_level
    
    # class属性を生成
    class_attr = f' class="{node.css_class}"' if node.css_class else ''
    
    if node.node_type == "section":
        # セクション
        html += f"{indent}<div class=\"indent\">\n"
        for child in node.children:
            html += node_to_html(child, indent_level + 1)
        html += f"{indent}</div>\n"
    
    elif node.node_type == "line":
        # 一行の項目
        if node.key == "item":
            # ・ 値
            html += f"{indent}<span>・ </span><span{class_attr}>{node.value}</span><br>\n"
        
        elif node.key == "item_link":
            # ・ <a>リンク</a>
            html += f'{indent}<span>・ </span>\n'
            html += f'{indent}<a href="{node.href}"{class_attr}>\n'
            html += f'{indent}{node.value}\n'
            html += f'{indent}</a>\n'
        
        elif node.key == "item_keyvalue":
            # ・ キー : 値
            html += f"{indent}<span>・ </span><span{class_attr}>{node.value}</span><br>\n"
        
        elif node.key == "header":
            # キー :
            html += f"{indent}<span{class_attr}>{node.value}</span> :\n"
        
        elif node.key == "keyvalue":
            # キー : 値
            html += f"{indent}<span{class_attr}>{node.value}</span><br>\n"
        
        elif node.key == "keyvalue_link":
            # キー : <a>リンク</a>
            parts = node.value.split(" : ")
            html += f'{indent}<span{class_attr}>{parts[0]}</span> : <a href="{node.href}">{parts[1]}</a>\n'
        
        elif node.key == "link":
            # 参考 : <a>リンク</a>
            html += f'{indent}参考 : <a href="{node.href}"{class_attr}>{node.value}</a>\n'
        
        elif node.key == "text":
            # 文字列
            html += f"{indent}<span{class_attr}>{node.value}</span><br>\n"
    
    return html


def json_to_html(json_data, output_file="output.html"):
    """JSONデータからHTMLファイルを生成"""
    
    # JSONを木構造に変換
    tree = parse_json_to_tree(json_data)
    
    # HTMLヘッダー
    html = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>Minecraft Mod構成 1.20.1</title>
<meta name="keywords" content="Minecraft,Mod,1.20.1,バニラ拡張">
<meta name="description" content="Minecraft 1.20.1のMod構成とキー設定">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="style.css">
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
</head>
<body>
<div id="outer">
<header>
<div class="header-inner">
<h1>Minecraft Mod構成 1.20.1</h1>
<p>バニラをより豊かにするMod構成とその使い方</p>
</div>
</header>
<div id="content">
<div class="inner">
"""

    # 木構造をHTMLに変換
    if isinstance(tree, list):
        for node in tree:
            if node.node_type == "line" and node.key == "header":
                # トップレベルセクション
                html += f"  <div>\n"
                class_attr = f' class="{node.css_class}"' if node.css_class else ''
                html += f"    <span{class_attr}>{node.value}</span> :\n"
            elif node.node_type == "section":
                html += "    <div class=\"indent\">\n"
                for child in node.children:
                    html += node_to_html(child, 3)
                html += "    </div>\n"
                html += "  </div>\n\n"
    else:
        html += node_to_html(tree, 1)

    # HTMLフッター
    html += """</div>
<aside>
<div class="left-title">サイドバータイトル</div>
<div class="link">
  <ul>
  <li>記事ページへのリンク</li>
  <li>記事ページへのリンク</li>
  </ul>
</div>
</aside>
</div>
<footer>© 2010 あなたのホームページ</footer>
</div>
</body>
<script>
  const addHtmlToId = function (idname, path) {
    $(function () {
      $.ajaxSetup({
        cache: false
      });
      $(idname).load(path);
    });
  }
  addHtmlToId("#modlist_base", "./ModList_Base.html")
</script>
</html>
"""

    # ファイルに書き込み
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
