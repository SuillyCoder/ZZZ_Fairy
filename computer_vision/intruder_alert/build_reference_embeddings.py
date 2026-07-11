#Import the necessary libraries
import os, pickle, torch, sys
import numpy as np
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1

#Get the absolute file path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

#Import the necessary directories
from config import DATASET_DIR, VALIDATION_DIR, OUTPUT_PATH

MATCH_THRESHOLD = 0.9 #Must match face_matcher.py's runtime threshold
KNOWN_IDENTITIES = ["enzo", "rafiq"]

#Load the facenet models
def load_models(device):
    mtcnn = MTCNN(image_size=160, margin=20, device=device) #MTCNN Model Loading
    resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device) #InceptionResnet Model Loading
    return mtcnn, resnet #Return both the models

def embed_folder(folder_path, mtcnn, resnet, device):
    #Crop and embed every image in a folder.
    embeddings = [] #Have an array to store all the embeddings
    if not os.path.isdir(folder_path):
        return embeddings #Return the empty embeddings if the filepath isn't correct
    
    for filename in os.listdir(folder_path):
        image_path = os.path.join(folder_path, filename) #Extract the image path
        try:
            image = Image.open(image_path).convert("RGB") #Convert the images into RGB
        except Exception:
            print(f"Skipping unreadable file: {filename}") #Error reading files
            continue #Carry on
        face_tensor =  mtcnn(image) #Create a tensor object for a single face
        if face_tensor is None: #NO face tensor detected
            print(f"  No face detected, skipping: {filename}")
            continue #Carry on

        with torch.no_grad():
            embedding = resnet(face_tensor.unsqueeze(0).to(device))
        embeddings.append(embedding.cpu().numpy()[0])

    return embeddings #Return the full embedding array with all the embeddings

def build_reference_embeddings(mtcnn, resnet, device): #Using pre-trained face detection and recognizing models
    reference_embeddings = {} #Initialize the reference embeddings as empty
    for identity in KNOWN_IDENTITIES: 
        folder = os.path.join(DATASET_DIR, identity) #Acquire the folder path for a specific identity: 'enzo' and 'rafiq'
        print(f"Loading and embedding faces for '{identity}'...")
        embeddings = embed_folder(folder, mtcnn, resnet, device)
        print(f" ->{len(embeddings)} usable reference embeddings")
        reference_embeddings[identity] = embeddings #Single element of the reference embedding equal to an individial face embedding
    return reference_embeddings #Return all the reference embeddings

def validate(reference_embeddings, mtcnn, resnet, device):
    if not os.path.isdir(VALIDATION_DIR):
        print("No validation/ folder found — skipping accuracy check.")
        return None

    total, correct = 0,0 #Metrics for total images and correct classifications

    for expected_identity in os.listdir(VALIDATION_DIR):
        folder = os.path.join(VALIDATION_DIR, expected_identity)
        if not os.path.isdir(folder):
            continue #Continue if ever it's not in the folder 

        for filename in os.listdir(folder):
            image_path = os.path.join(folder, filename) #Extract the image path
            try:
                image = Image.open(image_path).convert("RGB") #Open and set the extracted image to a single instance
            except Exception:
                continue

            face_tensor = mtcnn(image) #Run the image through the MTCNN model
            if face_tensor is None:
                continue

            with torch.no_grad():
                embedding = resnet(face_tensor.unsqueeze(0).to(device)).cpu().numpy()[0]

            best_identity, best_distance = "unknown", float("inf")
            for identity, ref_list in reference_embeddings.items():
                for ref_embedding in ref_list:
                    distance = np.linalg.norm(embedding - ref_embedding) #Calculate for a single best distance
                    if distance < best_distance:
                        best_distance = distance #Set the best euclidean distance out of all the calculated ones
                        best_identity = identity #Set the best identity based on the calculated euclidean distances

            predicted = best_identity if best_distance <= MATCH_THRESHOLD else "unknown" #See if it matches or not
            total += 1
            if predicted == expected_identity:
                correct += 1
            else:
                print(
                    f"  Mismatch: expected '{expected_identity}', got '{predicted}' "
                    f"(distance={best_distance:.3f}) for {filename}"
                )
        if total == 0:
            print("Validation folder exists but contained no usable images.")
            return None
        
        accuracy = correct / total #Compute for the model accuracy and display
        print(f"\nValidation accuracy: {accuracy:.1%} ({correct}/{total})")
        return accuracy

def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    mtcnn, resnet = load_models(device) #Load the given models on to the device

    reference_embeddings = build_reference_embeddings(mtcnn, resnet, device)

    with open(OUTPUT_PATH, "wb") as f:
        pickle.dump(reference_embeddings, f)
    print(f"\nSaved reference embeddings to: {OUTPUT_PATH}")

    accuracy = validate(reference_embeddings, mtcnn, resnet, device)
    if accuracy is not None: 
        if accuracy >= 0.80:
            print(f"Model Accuracy: {accuracy}. Model is good for use")
        else:
            print(f"Model Accuracy: {accuracy}. Please adjust dataset and parameters to at least reach a total of 80%")

if __name__ == "__main__":
    main()
