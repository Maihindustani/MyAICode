from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import os
import numpy as np
import faiss
import chromadb
from torch import embedding
from typing import List, Any

class EmbeddingManager:
    def __init__(self, model):
        self.model = model

    def generate_embeddings(self, texts):
        return self.model.encode(texts)
class RAGApp:
    def __init__(self):
        self.pdf_folder = "langChainforRAG/pdfs"  # Folder containing PDFs
        self.documents = []
        self.chunks = []
        self.embeddings = None
        self.model = None
        
        self.load_data()  # automatically loads PDFs
    
    def load_data(self):
        if os.path.exists(self.pdf_folder) and os.path.isdir(self.pdf_folder):
            print("Loading PDFs from folder...")
            dir_loader = DirectoryLoader(
                self.pdf_folder,
                glob="**/*.pdf",
                show_progress=True,
                loader_cls=PyPDFLoader
            )
            self.documents = dir_loader.load()
            print(f"{len(self.documents)} documents loaded.")
            
            if self.documents:
                self.chunk_data()
        else:
            print(f"PDF folder does not exist: {self.pdf_folder}. Please create it and add PDFs.")
    
    def chunk_data(self, chunk_size=500, overlap=200):
        print("Chunking documents...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            length_function=len,
            separators=["\n\n","\n","."," ",""]
        )
        split_docs = text_splitter.split_documents(self.documents)
        self.chunks = split_docs  # ✅ Store chunks
        
        print(f"{len(self.chunks)} text chunks created.")
        if self.chunks:
            print(f"Content of first chunk:\n{self.chunks[0].page_content[:800]}")
        
        self.load_model()
    
    def load_model(self):
        print("Loading embedding model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Model loaded successfully.")
        self.generate_embeddings()
    

    def generate_embeddings(self):
        
        embedding_manager = EmbeddingManager(self.model)
        texts = [chunk.page_content for chunk in self.chunks]
        embeddings = embedding_manager.generate_embeddings(texts)

        print(f"Generated {len(embeddings)} embeddings")
        
        # Call another class
        vector_store=VectorStore()
        
        # VectorStore.add_documents(self,self.chunks,self.embeddings)
        # self is automatically passed while calling in function 
        vector_store.add_documents(self.chunks,embeddings)
        print(vector_store)
        rag_retriver=retrieve(vector_store,embedding_manager)
        results=rag_retriver.retrieve("The tiger laughed")
        print(results)

class VectorStore:
    def __init__(self, collection_name: str = "pdf_documents", persist_directory: str = "../data/vectorstore"):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self.initialize_store()
    def initialize_store(self):
        try:
            print("Initializing ChromaDB vector store...")
            os.makedirs(self.persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
            print(self.collection.name)
        except Exception as e:
            print(f"Error initializing vector store: {e}")
            raise
    def add_documents(self, documents: List[Any], embeddings: np.ndarray):
        try:
            print(f"Adding {len(documents)} documents to vector store...")

            ids=[]
            metadatas=[]
            documents_text=[]
            embeddings_list=[]
            for i , (doc,embedding) in enumerate(zip(documents,embeddings)):
                doc_id=f"doc_{i}"
                ids.append(doc_id)
                
                # prepare metadata
                metadata=dict(doc.metadata)
                metadata['doc_index']=i
                metadata['content_length']=len(doc.page_content)
                metadatas.append(metadata)
                
                documents_text.append(doc.page_content)
                
                embeddings_list.append(embedding.tolist())
                
                try:
                   self.collection.add(
                       ids=ids,
                       embeddings=embeddings_list,
                       metadatas=metadatas,
                       documents=documents_text
                   ) 
                   print(f"successfully added {len(documents)}" )
                   print(f"Total documents in collection  {self.collection.count}" )
                   
                  
                except Exception as e:
                    print(e)
            
        except Exception as e:
            print(f"Error adding documents to vector store: {e}")
            raise

     
class retrieve:
    def __init__(self,vector_store:VectorStore,embedding_manager):
        self.vector_store=vector_store
        self.embedding_manager=embedding_manager
        
    def retrieve(self,query:str,top_k:int=1,score_threshold:float=0.0)->List[dict[str,Any]]:
        query_embedding=self.embedding_manager.generate_embeddings([query])[0]
        try:
          results= self.vector_store.collection.query(
               query_embeddings=[query_embedding.tolist()],
               n_results=top_k
            )
        
          retrieveddocs=[]
          if results['documents'] and results['documents'][0]:
              documents=results['documents'][0]
              metadatas=results['metadatas'][0]
              distances=results['distances'][0]
              ids=results['ids'][0]
              
              for i,(doc_id,document,metadata,distance) in enumerate(zip(ids,documents,metadatas,distances)):
                  
                  similarity_score=1-distance
                  if similarity_score>=score_threshold:
                      retrieveddocs.append({
                          'id':doc_id,
                          'content':document,
                          'similarity_score':similarity_score,
                          'distance':distance,
                        #   'rank':rank+1
                      })
              print(f"retrieved documents {len(documents)}")
          else:
               print("no documents")
          return retrieveddocs
       
        except Exception as e:
            print(f"error during retrieval {e}")
            return []
            
              
              
          
        
if __name__ == "__main__":
    # app = RAGApp()
    # VectorStore=VectorStore()
    # VectorStore
    app=RAGApp()