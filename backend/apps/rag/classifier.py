import os
import logging
import numpy as np
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# Predefined legal domains and seed phrases
LEGAL_DOMAINS = {
    "criminal_law": "murder theft robbery criminal prosecution IPC CRPC penal code bail detention",
    "service_law": "government employee pension gratuity transfer posting promotion seniority dismissal",
    "tax_law": "income tax GST assessment commissioner appeal excise customs revenue",
    "property_law": "land acquisition eviction tenancy title deed property dispute rent control",
    "motor_vehicles": "accident compensation insurance claim motor vehicle tribunal MV act",
    "constitutional": "fundamental rights article 14 19 21 writ petition habeas corpus mandamus",
    "family_law": "divorce maintenance custody matrimonial marriage dissolution hindu law",
    "labour_law": "workman industrial dispute factory EPF ESI minimum wages trade union",
    "environmental": "pollution mining forest clearance environment national green tribunal",
    "commercial": "contract arbitration company insolvency bankruptcy corporate dispute recovery",
    "education": "admission university reservation quota examination degree UGC",
    "civil_procedure": "civil suit injunction decree specific performance CPC appeal limitation",
}

class LegalDomainClassifier:
    """
    Zero-shot semantic classifier using InLegalBERT.
    Computes centroids for predefined legal domains based on seed phrases,
    and assigns cases to domains based on text embedding similarity.
    Falls back to unsupervised K-Means clustering if confidence is low.
    """
    
    def __init__(self, model_name="law-ai/InLegalBERT", device=None):
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = device
            
        logger.info(f"Loading {model_name} on {self.device}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()
        
        # Precompute seed centroids
        self.domain_names = list(LEGAL_DOMAINS.keys())
        self.seed_embeddings = self._compute_seed_embeddings()
        
        self.kmeans = None
        self.kmeans_trained = False

    def _mean_pooling(self, model_output, attention_mask):
        token_embeddings = model_output[0] # First element of model_output contains all token embeddings
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

    def embed_texts(self, texts: list[str], batch_size: int = 16) -> np.ndarray:
        """Get 768-dim embeddings for a list of texts."""
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            encoded_input = self.tokenizer(batch, padding=True, truncation=True, max_length=512, return_tensors='pt').to(self.device)
            with torch.no_grad():
                model_output = self.model(**encoded_input)
            
            sentence_embeddings = self._mean_pooling(model_output, encoded_input['attention_mask'])
            # Normalize embeddings for cosine similarity
            sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)
            all_embeddings.append(sentence_embeddings.cpu().numpy())
            
        return np.vstack(all_embeddings)

    def _compute_seed_embeddings(self) -> np.ndarray:
        logger.info("Computing seed centroids...")
        phrases = [LEGAL_DOMAINS[d] for d in self.domain_names]
        return self.embed_texts(phrases)

    def train_kmeans(self, embeddings: np.ndarray, k: int = 100):
        """Train K-Means clustering as a fallback mechanism."""
        logger.info(f"Training K-Means with k={k}...")
        # Avoid crashing if we have fewer samples than clusters
        k = min(k, len(embeddings))
        self.kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        self.kmeans.fit(embeddings)
        self.kmeans_trained = True

    def classify_dataframe(self, df: pd.DataFrame, text_col: str = "text_to_classify", k: int = 100) -> pd.DataFrame:
        """
        Classifies all rows in a DataFrame. 
        Requires the DataFrame to have the specified text_col.
        Returns the DataFrame with 'area_of_law', 'confidence', and 'cluster_id' columns.
        """
        if text_col not in df.columns:
            raise ValueError(f"Column '{text_col}' not found in DataFrame.")
            
        # Fill NaNs with empty string
        texts = df[text_col].fillna("").tolist()
        
        logger.info(f"Embedding {len(texts)} texts...")
        embeddings = self.embed_texts(texts, batch_size=32)
        
        # 1. Zero-shot classification via cosine similarity to seeds
        logger.info("Computing semantic similarity to legal domains...")
        similarities = cosine_similarity(embeddings, self.seed_embeddings)
        
        best_indices = np.argmax(similarities, axis=1)
        confidences = np.max(similarities, axis=1)
        
        areas_of_law = [self.domain_names[idx] for idx in best_indices]
        
        # 2. Train K-Means on the actual dataset distribution
        self.train_kmeans(embeddings, k=k)
        cluster_ids = self.kmeans.predict(embeddings)
        
        df = df.copy()
        df['area_of_law'] = areas_of_law
        df['confidence'] = confidences
        df['cluster_id'] = cluster_ids
        
        # If confidence is very low (< 0.25), we mark area_of_law as "unknown" but retain cluster_id
        df.loc[df['confidence'] < 0.25, 'area_of_law'] = "unknown"
        
        return df
