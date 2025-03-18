

import cv2
import numpy as np
from tensorflow.keras.models import load_model

model = load_model("body_model.h5")  # Load pre-trained model

def classify_body(image_path):
    image = cv2.imread(image_path)
    image = cv2.resize(image, (128, 128))
    image = np.expand_dims(image, axis=0) / 255.0

    prediction = model.predict(image)
    labels = ["Ectomorph", "Mesomorph", "Endomorph"]
    return labels[np.argmax(prediction)]
