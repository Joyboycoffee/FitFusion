import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Input

# Sample training data (Replace with real dataset)
X_train = np.array([[160, 50], [170, 70], [180, 85], [150, 45], [175, 80]])  # [Height (cm), Weight (kg)]
y_train = np.array([0, 1, 2, 0, 2])  # Labels for body types (example: 0 = Ectomorph, 1 = Mesomorph, 2 = Endomorph)

# Define the model
model = Sequential([
    Input(shape=(2,)),  # Input layer (Height, Weight)
    Dense(8, activation='relu'),
    Dense(8, activation='relu'),
    Dense(3, activation='softmax')  # 3 output classes
])

# Compile the model
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

# Train the model
model.fit(X_train, y_train, epochs=50, verbose=1)

# Save the model
model.save("body_model.h5")

print("✅ Model training complete! `body_model.h5` has been saved.")
