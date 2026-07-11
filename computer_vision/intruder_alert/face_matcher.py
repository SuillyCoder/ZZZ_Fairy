import os, pickle, torch
import numpy as np
from facenet_pytorch import MTCNN, InceptionResnetV1
from config import BASE_DIR

#Set the reference path for the newly made .pkl model file
REFERENCE_EMBEDDINGS_PATH = os.path.join(
    BASE_DIR, "computer_vision", "intruder_alert", "reference_embeddings.pkl"
)

MATCH_THRESHOLD = 0.9

#Instantiate a class of a face matcher

class FaceMatcher:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu') #Set the GPU to be CUDA for running the model. Else, just the cpu
        self.mtcnn = MTCNN(image_size = 160, margin=20, device=self.device) #Set the mtcnn parameters
        self.resnet = InceptionResnetV1(pretrained='vggface2').eval().to(self.device) #InceptionResnet Model Loading
        self.reference_embeddings = self._load_reference_embeddings() #Set the reference embeddings that of the value of its own function's return

    #Initialize the _load_reference_embeddings function
    def _load_reference_embeddings(self):
        if not os.path.exists(REFERENCE_EMBEDDINGS_PATH): #If ever the filepath doesn't exist, raise an error
            raise FileNotFoundError( #Raise an error and prompt to run the model file first (build_reference_embeddings.py)
                "No reference_embeddings.pkl found. Run "
                "build_reference_embeddings.py first."
            )
        with open(REFERENCE_EMBEDDINGS_PATH, 'rb') as f:
            return pickle.load(f) #Return both embeddings for 'enzo' and 'rafiq'
    
    def get_embedding(self, pil_image): #Detect, crop, and embed a single face
        face_tensor = self.mtcnn(pil_image)
        if face_tensor is None: #If no face tensor exists: 
            return None
        with torch.no_grad():
            embedding = self.resnet(face_tensor.unsqueeze(0).to(self.device))
        return embedding.cpu().numpy()[0]
    
    def identity(self, pil_image): #Returns the identity of a person plus the respective euclidean distance
        embedding = self.get_embedding(pil_image)
        if embedding is None:
            return None, None
 
        best_identity, best_distance = "unknown", float("inf")
 
        for identity, ref_embeddings in self.reference_embeddings.items():
            for ref_embedding in ref_embeddings:
                distance = np.linalg.norm(embedding - ref_embedding)
                if distance < best_distance:
                    best_distance = distance
                    best_identity = identity
 
        if best_distance > MATCH_THRESHOLD:
            return "unknown", best_distance
 
        return best_identity, best_distance


    

