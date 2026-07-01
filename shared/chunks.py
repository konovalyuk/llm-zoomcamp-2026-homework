from gitsource import chunk_documents

CHUNK_SIZE = 2000
CHUNK_STEP = 1000


def chunk_lessons(documents):
    return chunk_documents(documents, size=CHUNK_SIZE, step=CHUNK_STEP)
