import pandas as pd
import numpy as np  
import datetime
import faiss
from sentence_transformers import SentenceTransformer
import time

def chunk_text(text, chunk_size=100):
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
    # chunks = []
    # for i in range(0,len(words), chunk_size):
    #     chunk = " ".join(words[i:i+chunk_size])
    #     chunks.append(chunk)
    # return chunks
def main():
    # start_time = time.time()
    print("Loading CMDB data and processing...")
    # Load the Excel file
    df = pd.read_excel(r'C:\\Users\\shravantogarla\\Downloads\\Automation\\allwindowserverscmdb.xlsx',engine='openpyxl')
    texts = (
    df[['Name','Used for','Supported by','Fully qualified domain name','Operating System','Operational status']].fillna('').astype(str).agg(' '.join, axis=1).tolist()
    )
    # texts = df[['Name','Used for','Supported by']].fillna('').apply(lambda row: ' '.join(row.astype(str)), axis=1).tolist()

    all_chunks = [chunk for text in texts for chunk in chunk_text(text, chunk_size=100)]

    # all_chunks = []
    # for text in texts:
    #     chunks = chunk_text(text)
    #     all_chunks.extend(chunks)
    # print(all_chunks)
    model=SentenceTransformer('all-MiniLM-L6-v2')
    embeddings=model.encode(all_chunks)
    
    # to increase performance:-
    # embeddings = model.encode(
    # all_chunks,
    # batch_size=32,
    # show_progress_bar=True
    # )
    embeddings=np.array(embeddings).astype("float32")
    dimension=embeddings.shape[1]
    # index = faiss.IndexFlatL2(dimension)
    # It is replaced with below
    index = faiss.IndexHNSWFlat(dimension, 32)
    index.hnsw.efConstruction = 40
    index.add(embeddings)
    query=input("Enter your search i.e any windows server name: ")
    if query:
        query_embedding=model.encode([query]).astype("float32")
        k=3
        distances, results = index.search(query_embedding, k)  
        table_data = [all_chunks[idx] for idx in results[0]]
        df_results = pd.DataFrame(table_data, columns=["Result"])
        print(df_results)
        # for i, idx in enumerate(results[0]):
        #     # print(f"Result {i+1} (distance {distances[0][i]:.4f}):")
        #     # print("Chunk:", all_chunks[idx])
        #     print(all_chunks[idx])
        #     print("-"*80)
    # end_time = time.time()
    # print(f"Total execution time: {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
   main()