"""Small MLP model with standardized angle/voltage inputs."""
from __future__ import annotations
from .core import limit_pwm


def train_model(x, y):
    from sklearn.neural_network import MLPRegressor
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    # Architecture and hyperparameters are EXAMPLES; the thesis does not specify them.
    model = make_pipeline(StandardScaler(), MLPRegressor(
        hidden_layer_sizes=(32, 16), max_iter=1200, random_state=42,
        early_stopping=False, learning_rate_init=0.003))
    model.fit(x, y)
    return model


def predict_pwm(model, angle_deg: float, voltage_v: float) -> int:
    return limit_pwm(float(model.predict([[angle_deg, voltage_v]])[0]))
