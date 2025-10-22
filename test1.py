import json

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

with open("tyumen-soft.json", encoding="utf-8") as file:
    data = json.load(file)


# print(data)

pages = data["pages"]

md_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")]
)

rec_splitter = RecursiveCharacterTextSplitter(
    chunk_overlap=20, chunk_size=1500, length_function=len
)


page1 = pages[0]

text = page1["content"]["text"]

docs = md_splitter.split_text(text)

docs = rec_splitter.split_documents(docs)

CHUNK_TEMPLATE = """META: h1 - {h1}
{text}
"""

for doc in docs:
    text = CHUNK_TEMPLATE.format(h1=doc.metadata.get("h1", ""), text=doc.page_content)
    print(text)
