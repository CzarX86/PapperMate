import chromadb
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ContractVectorStore:
    """Gerencia o armazenamento e busca de vetores de contratos usando ChromaDB."""

    def __init__(self, path: str = "./chroma_db"):
        """Inicializa o cliente ChromaDB e a coleção de contratos."""
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(name="contract_embeddings")
        logger.info(f"✅ ChromaDB inicializado em {path} com coleção 'contract_embeddings'.")

    def add_contract_embedding(self, id: str, embedding: List[float], metadata: Optional[Dict[str, Any]] = None):
        """Adiciona o embedding de um contrato à coleção."""
        try:
            self.collection.add(
                documents=[""],  # Documento vazio, pois o foco é o embedding e metadados
                embeddings=[embedding],
                metadatas=[metadata] if metadata else [{}],
                ids=[id]
            )
            logger.info(f"✅ Embedding do contrato {id} adicionado ao ChromaDB.")
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar embedding {id} ao ChromaDB: {e}")

    def search_similar_contracts(self, query_embedding: List[float], n_results: int = 5) -> List[Dict[str, Any]]:
        """Busca contratos similares com base em um embedding de consulta."""
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['metadatas', 'distances']
            )
            logger.info(f"🔍 Busca por similaridade no ChromaDB retornou {len(results['ids'][0])} resultados.")
            
            # Formata os resultados
            formatted_results = []
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        "id": results['ids'][0][i],
                        "distance": results['distances'][0][i],
                        "metadata": results['metadatas'][0][i]
                    })
            return formatted_results
        except Exception as e:
            logger.error(f"❌ Erro na busca por similaridade no ChromaDB: {e}")
            return []

    def get_contract_embedding(self, id: str) -> Optional[List[float]]:
        """Recupera o embedding de um contrato pelo ID."""
        try:
            results = self.collection.get(ids=[id], include=['embeddings'])
            if results and results['embeddings']:
                return results['embeddings'][0]
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao recuperar embedding {id} do ChromaDB: {e}")
            return None

    def delete_contract_embedding(self, id: str):
        """Deleta o embedding de um contrato pelo ID."""
        try:
            self.collection.delete(ids=[id])
            logger.info(f"🗑️ Embedding do contrato {id} deletado do ChromaDB.")
        except Exception as e:
            logger.error(f"❌ Erro ao deletar embedding {id} do ChromaDB: {e}")

    def count_embeddings(self) -> int:
        """Retorna o número total de embeddings na coleção."""
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"❌ Erro ao contar embeddings no ChromaDB: {e}")
            return 0

    def get_supplier_embeddings(self, supplier_name: str) -> List[Dict[str, Any]]:
        """Recupera todos os embeddings e metadados para um fornecedor específico."""
        try:
            results = self.collection.get(
                where={
                    "supplier": supplier_name
                },
                include=['embeddings', 'metadatas', 'documents']
            )
            logger.info(f"🔍 Recuperados {len(results['ids'])} embeddings para o fornecedor '{supplier_name}'.")
            
            formatted_results = []
            for i in range(len(results['ids'])):
                formatted_results.append({
                    "id": results['ids'][i],
                    "embedding": results['embeddings'][i],
                    "metadata": results['metadatas'][i]
                })
            return formatted_results
        except Exception as e:
            logger.error(f"❌ Erro ao recuperar embeddings para o fornecedor '{supplier_name}' do ChromaDB: {e}")
            return []
