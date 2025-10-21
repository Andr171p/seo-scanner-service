from typing import Final, Literal

import re

import nltk
import numpy as np
from embeddings_service.langchain import RemoteHTTPEmbeddings
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..settings import settings

nltk.download("stopwords")
nltk.download("wordnet")

CHUNK_SIZE, CHUNK_OVERLAP = 1024, 10
# Минимальное число кластеров
MIN_CLUSTER_SIZE = 2
# Ключевая метрика для кластеризации
HDBSCAN_METRIC = "euclidian"

RANDOM_STATE = 42
# Минимальное значение токена для пред обработки текста
MIN_TOKEN = 2
# Минимальная длина предложения для извлечения ключевых слов
MIN_SENTENCE_LENGTH = 10
# Загрузка стоп-слов для русского языка (слова несущие малую смысловую нагрузку)
STOPWORDS: Final[list[str]] = list(set(stopwords.words("russian")))

embeddings: Final[Embeddings] = RemoteHTTPEmbeddings(base_url=settings.embeddings.base_url)


def preprocess_text(text: str) -> str:
    """Предобработка текста: очистка, лемматизация, удаление стоп-слов.

    :param text: Текст для обработки.
    :return Пред обработанный текст.
    """
    lemmatizer = WordNetLemmatizer()
    text = text.lower()
    text = re.sub(r"[^а-яёa-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    tokens = word_tokenize(text)
    processed_tokens: list[str] = [
        lemmatizer.lemmatize(token)
        for token in tokens
        if token not in STOPWORDS and len(token) > MIN_TOKEN
    ]
    return " ".join(processed_tokens)


def split_text(
        text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP
) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap, length_function=len
    )
    return splitter.split_text(text)


def vectorize_text(
        texts: list[str], ngram_range: tuple[int, int] = (1, 2), n_components: int = 50
) -> list[list[float]]:
    """Векторизация текстов с помощью TF-IDF и уменьшения размерности"""
    tfidf_vectorizer = TfidfVectorizer(
        max_features=10000,
        min_df=2,
        max_df=0.8,
        stop_words=list(STOPWORDS),
        ngram_range=ngram_range
    )
    tfidf_matrix = tfidf_vectorizer.fit_transform(texts)
    # Уменьшение размерности с помощью SVD
    if n_components and n_components < tfidf_matrix.shape[1]:
        svd = TruncatedSVD(n_components=n_components, random_state=42)
        vectors = svd.fit_transform(tfidf_matrix)
    else:
        vectors = tfidf_matrix.toarray()
    return vectors.tolist()


def _get_similarity_matrix(
        chunks1: list[str], chunks2: list[str], method: Literal["tf-idf", "embeddings"] = "tf-idf"
) -> np.ndarray:
    match method:
        case "tf-idf":
            vectorizer = TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 2),
                stop_words=STOPWORDS
            )
            tfidf_matrix = vectorizer.fit_transform(chunks1 + chunks2)
            vectors1, vectors2 = tfidf_matrix[:len(chunks1)], tfidf_matrix[len(chunks1):]
            return cosine_similarity(vectors1, vectors2)
        case "embeddings":
            vectors = embeddings.embed_documents(chunks1 + chunks2)
            vectors1, vectors2 = vectors[:len(chunks1)], vectors[len(chunks1):]
            return cosine_similarity(vectors1, vectors2)


def compare_texts(
        text1: str,
        text2: str,
        method: Literal["tf-idf", "embeddings"] = "tf-idf",
        similarity_strategy: Literal["max", "mean", "median", "std"] = "max"
) -> float:
    """Сравнивает семантическую релевантность двух текстов"""
    chunks1, chunks2 = split_text(text1), split_text(text2)
    similarity_matrix = _get_similarity_matrix(chunks1, chunks2, method)
    match similarity_strategy:
        case "max":
            similarity_score = np.max(similarity_matrix)
        case "mean":
            similarity_score = np.mean(similarity_matrix)
        case "median":
            similarity_score = np.median(similarity_matrix)
        case "std":
            similarity_score = np.std(similarity_matrix)
        case _:
            similarity_score = np.nan
    return float(similarity_score)
