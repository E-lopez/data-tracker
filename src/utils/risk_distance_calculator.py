import math
from services.non_defaulter_service import get_all_non_defaulters
import logging

logger = logging.getLogger(__name__)

class RiskDistanceCalculator:
    def __init__(self):
        self.non_defaulter_centroids = None
        self.feature_means = None
        self.feature_stds = None
        self.feature_cols = ['demographics', 'financialResponsibility', 'riskAversion', 'impulsivity', 
                            'futureOrientation', 'financialKnowledge', 'locusOfControl', 'socialInfluence', 
                            'resilience', 'familismo', 'respect', 'risk_level']
        self._initialize_model()
    
    def _calculate_mean_std(self, values):
        """Calculate mean and standard deviation"""
        n = len(values)
        if n == 0:
            return 0, 1
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n
        std = math.sqrt(variance) if variance > 0 else 1
        return mean, std
    
    def _euclidean_distance(self, point1, point2):
        """Calculate Euclidean distance between two points"""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(point1, point2)))
    
    def _simple_clustering(self, features, k=3):
        """Simple k-means clustering without sklearn"""
        if len(features) < k:
            return [features[i % len(features)] for i in range(k)]
        
        # Initialize centroids randomly
        centroids = features[:k]
        
        for _ in range(10):  # Max 10 iterations
            clusters = [[] for _ in range(k)]
            
            # Assign points to nearest centroid
            for point in features:
                distances = [self._euclidean_distance(point, centroid) for centroid in centroids]
                closest = distances.index(min(distances))
                clusters[closest].append(point)
            
            # Update centroids
            new_centroids = []
            for cluster in clusters:
                if cluster:
                    centroid = [sum(dim) / len(cluster) for dim in zip(*cluster)]
                    new_centroids.append(centroid)
                else:
                    new_centroids.append(centroids[len(new_centroids)])
            
            centroids = new_centroids
        
        return centroids
    
    def _initialize_model(self):
        """Initialize clustering model with non-defaulter data"""
        try:
            non_defaulters = get_all_non_defaulters()
            print(f"DEBUG: Retrieved {len(non_defaulters) if isinstance(non_defaulters, list) else 'ERROR'} non-defaulters")
            
            if isinstance(non_defaulters, dict) and 'error' in non_defaulters:
                print(f"DEBUG: Error loading non-defaulters: {non_defaulters['error']}")
                return False
            
            if len(non_defaulters) < 2:
                print(f"DEBUG: Only {len(non_defaulters)} non-defaulters available, need at least 2")
                return False
            
            # Extract and normalize features
            features = []
            feature_values = {col: [] for col in self.feature_cols}
            
            for nd in non_defaulters:
                feature_row = []
                for col in self.feature_cols:
                    value = nd.get(col, 0) or 0
                    feature_row.append(float(value))
                    feature_values[col].append(float(value))
                features.append(feature_row)
            
            # Calculate normalization parameters
            self.feature_means = []
            self.feature_stds = []
            for col in self.feature_cols:
                mean, std = self._calculate_mean_std(feature_values[col])
                self.feature_means.append(mean)
                self.feature_stds.append(std)
            
            # Normalize features
            normalized_features = []
            for feature_row in features:
                normalized_row = []
                for i, value in enumerate(feature_row):
                    normalized_value = (value - self.feature_means[i]) / self.feature_stds[i]
                    normalized_row.append(normalized_value)
                normalized_features.append(normalized_row)
            
            # Simple clustering
            k = min(3, max(2, len(non_defaulters) // 2))
            self.non_defaulter_centroids = self._simple_clustering(normalized_features, k)
            
            print(f"DEBUG: Successfully initialized risk calculator with {k} centroids")
            logger.info(f"Initialized risk distance calculator with {k} centroids")
            return True
            
        except Exception as e:
            print(f"DEBUG: Exception in risk calculator init: {str(e)}")
            logger.error(f"Error initializing risk distance calculator: {str(e)}")
            return False
    
    def calculate_risk_distance(self, user_scores):
        """Calculate risk distance for a single user"""
        try:
            if self.non_defaulter_centroids is None:
                return {'error': 'Risk distance calculator not initialized'}
            
            # Extract and normalize user features
            user_features = []
            for i, col in enumerate(self.feature_cols):
                value = float(user_scores.get(col, 0) or 0)
                normalized_value = (value - self.feature_means[i]) / self.feature_stds[i]
                user_features.append(normalized_value)
            
            # Calculate distances to all centroids
            distances = [self._euclidean_distance(user_features, centroid) 
                        for centroid in self.non_defaulter_centroids]
            
            # Get minimum distance and closest cluster
            min_distance = min(distances)
            closest_cluster = distances.index(min_distance)
            
            # Normalize distance to risk score (0-100)
            max_expected_distance = 5.0  # Empirical max for normalized features
            risk_score = min(100, (min_distance / max_expected_distance) * 100)
            
            # Risk categories
            if risk_score <= 20:
                risk_category = 'Very Low'
            elif risk_score <= 40:
                risk_category = 'Low'
            elif risk_score <= 60:
                risk_category = 'Medium'
            elif risk_score <= 80:
                risk_category = 'High'
            else:
                risk_category = 'Very High'
            
            return {
                'risk_distance': round(min_distance, 4),
                'risk_score': round(risk_score, 2),
                'risk_category': risk_category,
                'closest_cluster': closest_cluster
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk distance: {str(e)}")
            return {'error': f'Risk calculation error: {str(e)}'}

# Global instance
risk_calculator = None

def get_risk_calculator():
    """Lazy initialization of risk calculator"""
    global risk_calculator
    if risk_calculator is None:
        risk_calculator = RiskDistanceCalculator()
    elif risk_calculator.non_defaulter_centroids is None:
        # Try to re-initialize if it failed before
        risk_calculator._initialize_model()
    return risk_calculator