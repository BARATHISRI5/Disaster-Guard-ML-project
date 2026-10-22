"""
DisasterGuard — CNN Flood Classifier (TensorFlow/Keras)

Binary classifier: flood vs no-flood from 256x256 satellite image patches.
Architecture: 4 Conv2D layers → MaxPool → Dropout(0.3) → Dense(256) → Sigmoid
"""

import os
import numpy as np


def build_cnn_model(input_shape=(256, 256, 3)):
    """
    Build the flood detection CNN.
    Architecture: Conv2D(32) → Conv2D(64) → Conv2D(128) → Conv2D(128) → Dense(256) → Sigmoid
    """
    try:
        from tensorflow import keras
        from tensorflow.keras import layers
    except ImportError:
        print("⚠️  TensorFlow not installed. Using mock model.")
        return None

    model = keras.Sequential([
        layers.Input(shape=input_shape),
        # Block 1
        layers.Conv2D(32, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        # Block 2
        layers.Conv2D(64, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        # Block 3
        layers.Conv2D(128, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        # Block 4
        layers.Conv2D(128, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        # Classifier head
        layers.Flatten(),
        layers.Dropout(0.3),
        layers.Dense(256, activation="relu"),
        layers.Dropout(0.3),
        layers.Dense(1, activation="sigmoid"),
    ])

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-4),
        loss="binary_crossentropy",
        metrics=["accuracy"]
    )
    model.summary()
    return model


def create_data_augmentation():
    """Create data augmentation pipeline for training."""
    try:
        from tensorflow.keras import layers
        return layers.Sequential([
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.1),
            layers.RandomBrightness(0.2),
            layers.RandomContrast(0.2),
        ])
    except ImportError:
        return None


def train_model(model, X_train, y_train, X_val, y_val, epochs=30, batch_size=16,
                save_path="models/flood_cnn_model.h5"):
    """Train the CNN model with data augmentation."""
    try:
        from tensorflow import keras
    except ImportError:
        print("⚠️  TensorFlow not available. Skipping training.")
        return None

    callbacks = [
        keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=3),
        keras.callbacks.ModelCheckpoint(save_path, save_best_only=True),
    ]

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks,
    )

    print(f"✅ Model saved to {save_path}")
    return history


def evaluate_model(model, X_test, y_test):
    """Evaluate model and print confusion matrix."""
    try:
        from sklearn.metrics import confusion_matrix, classification_report
    except ImportError:
        print("⚠️  scikit-learn not available.")
        return None

    y_pred = (model.predict(X_test) > 0.5).astype(int).flatten()
    print("\n📊 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["No Flood", "Flood"]))
    print("📊 Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    return {"predictions": y_pred, "accuracy": (y_pred == y_test).mean()}


def load_cnn_model(model_path="models/flood_cnn_model.h5"):
    """Load a trained CNN model from disk."""
    try:
        from tensorflow import keras
        if os.path.exists(model_path):
            return keras.models.load_model(model_path)
        print(f"⚠️  Model file not found: {model_path}")
        return None
    except ImportError:
        return None


def predict_flood_probability(model, image_patch):
    """
    Predict flood probability for a single image patch.
    Returns float 0-1 (flood risk).
    """
    if model is None:
        return mock_cnn_prediction()
    patch = np.expand_dims(image_patch, axis=0) if image_patch.ndim == 3 else image_patch
    return float(model.predict(patch, verbose=0)[0][0])


def mock_cnn_prediction(district=None):
    """Generate realistic mock CNN predictions for demo."""
    risk_map = {
        "Thoothukudi": 0.82, "Chennai": 0.45, "Nagapattinam": 0.68,
        "Tirunelveli": 0.55, "Cuddalore": 0.72, "Ramanathapuram": 0.38,
        "Kanyakumari": 0.25, "Villupuram": 0.60, "Thanjavur": 0.35,
        "Madurai": 0.22, "Trichy": 0.28, "Coimbatore": 0.15,
    }
    if district and district in risk_map:
        return risk_map[district] + np.random.uniform(-0.05, 0.05)
    return float(np.clip(np.random.beta(2, 5), 0, 1))
