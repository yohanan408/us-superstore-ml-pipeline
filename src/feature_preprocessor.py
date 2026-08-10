import numpy as np
import pandas as pd

from src.logger_config import logger

CONTINUOUS_FEATURES = ["Sales", "Quantity", "Discount", "Processing_Time_Days"]


def _build_rename_map(feature_columns):
    rename_map = {}
    for column in feature_columns:
        rename_map[column.replace(" ", "_")] = column
    return rename_map


def transform_and_align_features(payload_dict, feature_columns, scaler):
    if not isinstance(payload_dict, dict):
        raise TypeError("payload_dict must be a dictionary")

    logger.info("Transforming incoming checkout payload")

    incoming = pd.DataFrame([payload_dict])

    renamed = incoming.rename(columns=_build_rename_map(feature_columns))
    logger.info("Renamed incoming keys to match training columns")

    template = pd.DataFrame(
        np.zeros((1, len(feature_columns)), dtype=float), columns=feature_columns
    )

    for column in feature_columns:
        if column in renamed.columns:
            template[column] = renamed[column].to_numpy()

    continuous_columns = [c for c in CONTINUOUS_FEATURES if c in feature_columns]
    if continuous_columns:
        scaled = scaler.transform(template[continuous_columns])
        template[continuous_columns] = scaled
        logger.info("Scaled continuous fields via fitted RobustScaler")

    aligned = template[feature_columns].reset_index(drop=True)
    logger.info("Payload matrix aligned to model column sequence")
    return aligned
