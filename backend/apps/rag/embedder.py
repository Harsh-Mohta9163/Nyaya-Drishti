import logging
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

logger = logging.getLogger(__name__)

class InLegalBERTEmbeddingFunction(EmbeddingFunction):
    """
    ChromaDB compatible Embedding Function using InLegalBERT.
    """
    def __init__(self, model_name="law-ai/InLegalBERT", device=None):
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = device
            
        logger.info(f"Loading {model_name} for ChromaDB embeddings on {self.device}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()

    def _mean_pooling(self, model_output, attention_mask):
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

    def __call__(self, input: Documents) -> Embeddings:
        """
        Embeds a list of texts. Note: Input documents should already be chunked 
        to fit within 512 tokens.
        """
        embeddings = []
        batch_size = 16
        
        for i in range(0, len(input), batch_size):
            batch = input[i:i+batch_size]
            encoded_input = self.tokenizer(batch, padding=True, truncation=True, max_length=512, return_tensors='pt').to(self.device)
            
            with torch.no_grad():
                model_output = self.model(**encoded_input)
                
            sentence_embeddings = self._mean_pooling(model_output, encoded_input['attention_mask'])
            sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)
            
            # ChromaDB expects a list of list of floats
            embeddings.extend(sentence_embeddings.cpu().numpy().tolist())
            
        return embeddings

def chunk_text(text: str, tokenizer, max_tokens: int = 512, overlap: int = 128) -> list[str]:
    """
    Splits text into overlapping chunks using the tokenizer.
    """
    tokens = tokenizer.encode(text, add_special_tokens=False)
    
    if len(tokens) <= max_tokens:
        return [text]
        
    chunks = []
    stride = max_tokens - overlap
    
    for i in range(0, len(tokens), stride):
        chunk_tokens = tokens[i:i + max_tokens]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)
        
    return chunks
