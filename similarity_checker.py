# similarity_checker.py

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from text_processor import clean_text

def find_similar_issues(new_title: str, new_description: str, issues_df: pd.DataFrame, top_n: int = 5):
    """
    Находит задачи, похожие на новую, на основе анализа заголовков и описаний.

    :param new_title: Название новой задачи.
    :param new_description: Описание новой задачи.
    :param issues_df: DataFrame с существующими задачами (колонки: 'key', 'summary', 'description').
    :param top_n: Количество самых похожих задач для вывода.
    :return: DataFrame с похожими задачами.
    """
    if issues_df.empty:
        return pd.DataFrame()

    # 1. Предобработка текстов
    cleaned_new_title = clean_text(new_title)
    cleaned_new_description = clean_text(new_description)

    issues_df['cleaned_summary'] = issues_df['summary'].apply(clean_text)
    issues_df['cleaned_description'] = issues_df['description'].apply(clean_text)

    all_similarities = []
    
    # 2. Поиск по Заголовкам (summary)
    summary_corpus = list(issues_df['cleaned_summary']) + [cleaned_new_title]
    
    vectorizer_summary = TfidfVectorizer()
    tfidf_summary = vectorizer_summary.fit_transform(summary_corpus)
    
    cosine_sim_summary = cosine_similarity(tfidf_summary[-1], tfidf_summary[:-1])
    
    for i, similarity in enumerate(cosine_sim_summary[0]):
        all_similarities.append({
            'key': issues_df.iloc[i]['key'],
            'summary': issues_df.iloc[i]['summary'],
            'similarity': similarity,
            'found_in': 'заголовку'
        })
        
    # 3. Поиск по Описаниям (description)
    description_corpus = list(issues_df['cleaned_description']) + [cleaned_new_description]
    
    vectorizer_desc = TfidfVectorizer()
    tfidf_desc = vectorizer_desc.fit_transform(description_corpus)
    
    cosine_sim_desc = cosine_similarity(tfidf_desc[-1], tfidf_desc[:-1])
    
    for i, similarity in enumerate(cosine_sim_desc[0]):
        all_similarities.append({
            'key': issues_df.iloc[i]['key'],
            'summary': issues_df.iloc[i]['summary'],
            'similarity': similarity,
            'found_in': 'описанию'
        })

    # 4. Объединение и сортировка результатов
    if not all_similarities:
        return pd.DataFrame()

    similar_issues_df = pd.DataFrame(all_similarities)
    
    # Удаление дубликатов по 'key', оставляя запись с наибольшим 'similarity'
    similar_issues_df = similar_issues_df.sort_values('similarity', ascending=False).drop_duplicates('key').reset_index(drop=True)
    
    # Фильтрация задач с нулевой схожестью и сортировка
    similar_issues_df = similar_issues_df[similar_issues_df['similarity'] > 0].sort_values('similarity', ascending=False)
    
    return similar_issues_df.head(top_n)

def calculate_similarity(df, threshold=0.8):
    """
    Вычисляет схожесть текстов задач с использованием TF-IDF и косинусного сходства.
    """
    if 'full_text' not in df.columns or df.empty:
        return []

    tfidf_vectorizer = TfidfVectorizer(stop_words='english') # Можно добавить русские стоп-слова
    tfidf_matrix = tfidf_vectorizer.fit_transform(df['full_text'])

    cosine_sim_matrix = cosine_similarity(tfidf_matrix)
    
    duplicates = []
    
    # Поиск дубликатов
    for i in range(len(cosine_sim_matrix)):
        for j in range(i + 1, len(cosine_sim_matrix)):
            if cosine_sim_matrix[i][j] > threshold:
                duplicates.append({
                    "issue_1": df.iloc[i]['key'],
                    "issue_2": df.iloc[j]['key'],
                    "similarity": cosine_sim_matrix[i][j]
                })
                
    return sorted(duplicates, key=lambda x: x['similarity'], reverse=True)