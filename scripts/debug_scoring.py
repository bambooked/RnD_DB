import sqlite3
import re

def extract_meaningful_keywords(text: str):
    """意味のあるキーワードを抽出"""
    stopwords = {
        'に', 'を', 'が', 'は', 'で', 'と', 'の', 'だ', 'である', 'です', 'ます', 'した', 'する', 'される',
        'から', 'まで', 'より', 'など', 'こと', 'もの', 'について', 'に関する', 'がしたい', 'したい',
        '研究', '分析', 'データ', '情報', '利用', '評価', '手法', '開発', '検討', '提案', '教えて',
        'ファイル', '含まれ', '可能', '想定', '考え', 'られ', '推測', '目的',
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'about'
    }

    keywords = []
    english_keywords = re.findall(r'[A-Za-z0-9]{2,}', text)
    keywords.extend([kw.lower() for kw in english_keywords])

    japanese_keywords = re.findall(r'[あ-ん]{2,}|[ア-ン]{2,}|[一-龯]{2,}', text)
    keywords.extend(japanese_keywords)

    meaningful_keywords = [kw for kw in keywords if kw not in stopwords and len(kw) >= 2]

    return list(set(meaningful_keywords))

query = "LLMのバイアスに関する研究を教えて"
important_keywords = extract_meaningful_keywords(query)

print("=" * 60)
print("スコアリング デバッグ")
print("=" * 60)
print(f"\nクエリ: {query}")
print(f"抽出キーワード: {important_keywords}")

conn = sqlite3.connect('agent/database/research_data.db')
cursor = conn.cursor()
cursor.execute("SELECT name, description, summary FROM datasets WHERE name = 'jbbq'")
name, description, summary = cursor.fetchone()

dataset_text = f"{name} {description or ''} {summary or ''}".lower()

print(f"\n{name}データセットのスコア計算:")
print(f"  description: {description[:50]}...")

relevance_score = 0

# 重要キーワードでの完全一致
for keyword in important_keywords:
    if keyword in dataset_text:
        relevance_score += 3
        print(f"  ✅ 重要キーワード '{keyword}' 一致 → +3 (total: {relevance_score})")
    else:
        print(f"  ❌ 重要キーワード '{keyword}' 不一致")

# データセット名での部分一致
if any(keyword in name.lower() for keyword in important_keywords):
    relevance_score += 5
    print(f"  ✅ データセット名一致 → +5 (total: {relevance_score})")
else:
    print(f"  ❌ データセット名不一致")

# 元のクエリでの部分一致
query_lower = query.lower()
for word in query_lower.split():
    if len(word) > 2 and word in dataset_text:
        relevance_score += 1
        print(f"  ✅ クエリ単語 '{word}' 一致 → +1 (total: {relevance_score})")

print(f"\n最終スコア: {relevance_score}")
print(f"閾値5 {'以上' if relevance_score >= 5 else '未満'} → {'表示' if relevance_score >= 5 else '非表示'}")

conn.close()
