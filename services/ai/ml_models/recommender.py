import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from typing import List, Dict, Tuple, Optional
import pickle
import os
from django.conf import settings


class NeuralCollaborativeFiltering:
    """
    Neural Collaborative Filtering (NCF) model for product recommendations
    Combines MLP and GMF (Generalized Matrix Factorization) approaches
    """

    def __init__(self, num_users: int, num_items: int, embedding_dim: int = 64):
        self.num_users = num_users
        self.num_items = num_items
        self.embedding_dim = embedding_dim
        self.model = None
        self.user_mapping = {}
        self.item_mapping = {}
        self.reverse_user_mapping = {}
        self.reverse_item_mapping = {}

    def build_model(self, mlp_layers: List[int] = None, dropout_rate: float = 0.2):
        """Build the NCF model with GMF and MLP components"""
        if mlp_layers is None:
            mlp_layers = [256, 128, 64]

        # User input
        user_input = keras.Input(shape=(1,), name='user_id')
        user_embedding_gmf = layers.Embedding(
            input_dim=self.num_users,
            output_dim=self.embedding_dim,
            name='user_embedding_gmf'
        )(user_input)
        user_embedding_gmf = layers.Flatten()(user_embedding_gmf)

        user_embedding_mlp = layers.Embedding(
            input_dim=self.num_users,
            output_dim=self.embedding_dim,
            name='user_embedding_mlp'
        )(user_input)
        user_embedding_mlp = layers.Flatten()(user_embedding_mlp)

        # Item input
        item_input = keras.Input(shape=(1,), name='item_id')
        item_embedding_gmf = layers.Embedding(
            input_dim=self.num_items,
            output_dim=self.embedding_dim,
            name='item_embedding_gmf'
        )(item_input)
        item_embedding_gmf = layers.Flatten()(item_embedding_gmf)

        item_embedding_mlp = layers.Embedding(
            input_dim=self.num_items,
            output_dim=self.embedding_dim,
            name='item_embedding_mlp'
        )(item_input)
        item_embedding_mlp = layers.Flatten()(item_embedding_mlp)

        # GMF path
        gmf_vector = layers.Multiply()([user_embedding_gmf, item_embedding_gmf])

        # MLP path
        mlp_vector = layers.Concatenate()([user_embedding_mlp, item_embedding_mlp])
        for layer_size in mlp_layers:
            mlp_vector = layers.Dense(layer_size, activation='relu')(mlp_vector)
            mlp_vector = layers.Dropout(dropout_rate)(mlp_vector)

        # Combine GMF and MLP
        combined_vector = layers.Concatenate()([gmf_vector, mlp_vector])
        output = layers.Dense(1, activation='sigmoid')(combined_vector)

        # Create model
        self.model = keras.Model(
            inputs=[user_input, item_input],
            outputs=output
        )

        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', tf.keras.metrics.AUC()]
        )

        return self.model

    def train(self, interactions: np.ndarray, epochs: int = 10,
              batch_size: int = 256, validation_split: float = 0.2):
        """Train the NCF model"""
        user_ids = interactions[:, 0]
        item_ids = interactions[:, 1]
        labels = interactions[:, 2]

        history = self.model.fit(
            x=[user_ids, item_ids],
            y=labels,
            batch_size=batch_size,
            epochs=epochs,
            validation_split=validation_split,
            verbose=1
        )

        return history

    def predict(self, user_id: int, item_ids: List[int], top_k: int = 10) -> List[Tuple[int, float]]:
        """Predict scores for items for a given user"""
        # Convert to internal IDs if needed
        internal_user_id = self.user_mapping.get(str(user_id), user_id)

        # Create arrays for prediction
        user_array = np.full(len(item_ids), internal_user_id)
        item_array = np.array([self.item_mapping.get(str(i), i) for i in item_ids])

        # Predict
        predictions = self.model.predict([user_array, item_array], verbose=0)

        # Get top K
        item_scores = [(item_ids[i], float(predictions[i][0])) for i in range(len(item_ids))]
        item_scores.sort(key=lambda x: x[1], reverse=True)

        return item_scores[:top_k]

    def save_model(self, filepath: str):
        """Save the model and mappings"""
        self.model.save(filepath)

        # Save mappings
        mappings = {
            'user_mapping': self.user_mapping,
            'item_mapping': self.item_mapping,
            'reverse_user_mapping': self.reverse_user_mapping,
            'reverse_item_mapping': self.reverse_item_mapping,
            'num_users': self.num_users,
            'num_items': self.num_items,
            'embedding_dim': self.embedding_dim
        }

        with open(f"{filepath}_mappings.pkl", 'wb') as f:
            pickle.dump(mappings, f)

    def load_model(self, filepath: str):
        """Load the model and mappings"""
        self.model = keras.models.load_model(filepath)

        # Load mappings
        with open(f"{filepath}_mappings.pkl", 'rb') as f:
            mappings = pickle.load(f)

        self.user_mapping = mappings['user_mapping']
        self.item_mapping = mappings['item_mapping']
        self.reverse_user_mapping = mappings['reverse_user_mapping']
        self.reverse_item_mapping = mappings['reverse_item_mapping']
        self.num_users = mappings['num_users']
        self.num_items = mappings['num_items']
        self.embedding_dim = mappings['embedding_dim']


class ContentBasedRecommender:
    """Content-based filtering using item features and embeddings"""

    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self.item_embeddings = {}
        self.item_features = {}

    def add_item_embedding(self, item_id: str, embedding: np.ndarray, features: Dict = None):
        """Add or update item embedding"""
        self.item_embeddings[item_id] = embedding
        if features:
            self.item_features[item_id] = features

    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings"""
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        return dot_product / (norm1 * norm2 + 1e-8)

    def find_similar_items(self, item_id: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Find similar items based on embedding similarity"""
        if item_id not in self.item_embeddings:
            return []

        target_embedding = self.item_embeddings[item_id]
        similarities = []

        for other_id, other_embedding in self.item_embeddings.items():
            if other_id != item_id:
                similarity = self.compute_similarity(target_embedding, other_embedding)
                similarities.append((other_id, similarity))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


class HybridRecommender:
    """Hybrid recommendation system combining multiple approaches"""

    def __init__(self):
        self.ncf_model = None
        self.content_based = ContentBasedRecommender()
        self.weights = {
            'collaborative': 0.5,
            'content_based': 0.3,
            'popularity': 0.2
        }

    def set_ncf_model(self, ncf_model: NeuralCollaborativeFiltering):
        """Set the collaborative filtering model"""
        self.ncf_model = ncf_model

    def get_recommendations(self, user_id: str, context: Dict = None,
                           top_k: int = 10) -> List[Dict]:
        """Get hybrid recommendations"""
        recommendations = {}

        # Collaborative filtering recommendations
        if self.ncf_model:
            cf_recs = self._get_cf_recommendations(user_id, context, top_k * 2)
            for item_id, score in cf_recs:
                recommendations[item_id] = recommendations.get(item_id, 0) + score * self.weights['collaborative']

        # Content-based recommendations
        if context and 'current_item' in context:
            cb_recs = self.content_based.find_similar_items(context['current_item'], top_k * 2)
            for item_id, score in cb_recs:
                recommendations[item_id] = recommendations.get(item_id, 0) + score * self.weights['content_based']

        # Sort and return top K
        sorted_recs = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
        return [{'item_id': item_id, 'score': score} for item_id, score in sorted_recs[:top_k]]

    def _get_cf_recommendations(self, user_id: str, context: Dict, top_k: int) -> List[Tuple[str, float]]:
        """Get collaborative filtering recommendations"""
        # This would interact with the NCF model
        # Placeholder implementation
        return []

    def set_weights(self, collaborative: float = 0.5, content_based: float = 0.3,
                    popularity: float = 0.2):
        """Adjust the weights for different recommendation strategies"""
        total = collaborative + content_based + popularity
        self.weights = {
            'collaborative': collaborative / total,
            'content_based': content_based / total,
            'popularity': popularity / total
        }
