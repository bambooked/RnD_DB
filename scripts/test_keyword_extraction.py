import re

def extract_meaningful_keywords(text: str):
    """意味のあるキーワードを抽出"""
    # 一般的でない単語を抽出
    stopwords = {
        # 日本語助詞・動詞・形容詞など
        'に', 'を', 'が', 'は', 'で', 'と', 'の', 'だ', 'である', 'です', 'ます', 'した', 'する', 'される',
        'から', 'まで', 'より', 'など', 'こと', 'もの', 'について', 'に関する', 'がしたい', 'したい',
        # 学術系の一般的な単語（あまりにも広範囲で使われる単語）
        '研究', '分析', 'データ', '情報', '利用', '評価', '手法', '開発', '検討', '提案', '教えて',
        'ファイル', '含まれ', '可能', '想定', '考え', 'られ', '推測', '目的',
        # 英語一般語
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'about'
    }

    # 英数字混合キーワードを抽出（ESG, AI, MLなど）
    keywords = []

    # 3文字以上の英数字キーワードを抽出
    english_keywords = re.findall(r'[A-Za-z0-9]{2,}', text)
    keywords.extend([kw.lower() for kw in english_keywords])

    # 2文字以上の日本語キーワードを抽出
    japanese_keywords = re.findall(r'[あ-ん]{2,}|[ア-ン]{2,}|[一-龯]{2,}', text)
    keywords.extend(japanese_keywords)

    # ストップワードを除去
    meaningful_keywords = [kw for kw in keywords if kw not in stopwords and len(kw) >= 2]

    return list(set(meaningful_keywords))  # 重複除去

query = "LLMのバイアスに関する研究を教えて"
keywords = extract_meaningful_keywords(query)

print("=" * 60)
print("キーワード抽出テスト")
print("=" * 60)
print(f"\nクエリ: {query}")
print(f"\n抽出されたキーワード: {keywords}")
print(f"キーワード数: {len(keywords)}")

# jbbqのsummaryサンプル
jbbq_summary = """このデータセット「jbbq」は、多様な個人属性に関する情報を収集・提供することを目的としています。
社会学、心理学、公衆衛生学といった分野における研究に広く活用されることが想定されます。
特定の属性を持つ集団における健康格差の分析、社会的な受容度や偏見の研究、あるいは多様性を考慮した政策立案の基礎データとしての利用などが考えられます。"""

print(f"\n\njbbqのsummary（抜粋）:\n{jbbq_summary[:100]}...")

# summaryに各キーワードが含まれているかチェック
print(f"\n\nキーワード一致チェック:")
for kw in keywords:
    if kw in jbbq_summary.lower():
        print(f"  ✅ '{kw}' → 一致")
    else:
        print(f"  ❌ '{kw}' → 不一致")
