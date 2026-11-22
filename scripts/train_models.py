import json
import time
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / 'data' / 'raw'
MODELS_DIR = PROJECT_ROOT / 'models'
METADATA_DIR = MODELS_DIR / 'metadata'

DROPPED_COLS = ['num_outbound_cmds']
CATEGORICAL_COLS = ['protocol_type', 'service', 'flag']


def split_features_and_target(df):
    # Нормальный трафик переводим в 0, любую атаку в 1
    y = (df['labels'].astype(str).str.strip().str.lower() != 'normal').astype(int)
    X = df.drop(columns=['labels'])
    return X, y


def make_preprocessor(numeric_cols):
    # Константный столбец отбрасываем, числа масштабируем, категории кодируем
    return ColumnTransformer(
        transformers=[
            ('drop_const', 'drop', DROPPED_COLS),
            ('num', StandardScaler(), numeric_cols),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL_COLS),
        ]
    )


def build_models(numeric_cols):
    # Используем лучшие параметры, подобранные в ноутбуке model_training.ipynb
    return {
        'logistic_regression': {
            'display_name': 'Logistic Regression',
            'description': 'Линейный классификатор (быстрая базовая модель, C=10.0)',
            'is_default': False,
            'params': {'C': 10.0, 'max_iter': 2000, 'random_state': 42},
            'pipeline': Pipeline([
                ('prep', make_preprocessor(numeric_cols)),
                ('clf', LogisticRegression(C=10.0, max_iter=2000, random_state=42)),
            ]),
        },
        'knn': {
            'display_name': 'K-Nearest Neighbors (KNN)',
            'description': 'Метод k ближайших соседей (высокая точность, n_neighbors=5)',
            'is_default': False,
            'params': {'n_neighbors': 5},
            'pipeline': Pipeline([
                ('prep', make_preprocessor(numeric_cols)),
                ('clf', KNeighborsClassifier(n_neighbors=5, n_jobs=-1)),
            ]),
        },
        'mlp': {
            'display_name': 'Multilayer Perceptron (MLP)',
            'description': 'Многослойный перцептрон (лучший Recall и F1 для атак)',
            'is_default': True,
            'params': {
                'hidden_layer_sizes': [128, 64],
                'max_iter': 40,
                'early_stopping': True,
                'n_iter_no_change': 5,
                'random_state': 42,
            },
            'pipeline': Pipeline([
                ('prep', make_preprocessor(numeric_cols)),
                ('clf', MLPClassifier(
                    hidden_layer_sizes=(128, 64),
                    max_iter=40,
                    early_stopping=True,
                    n_iter_no_change=5,
                    random_state=42,
                )),
            ]),
        },
    }


def evaluate_on_test(pipeline, X_test, y_test):
    start_time = time.time()
    y_pred = pipeline.predict(X_test)
    predict_time = round(time.time() - start_time, 3)

    return {
        'accuracy': round(float(accuracy_score(y_test, y_pred)), 4),
        'precision_attack': round(float(precision_score(y_test, y_pred, pos_label=1)), 4),
        'recall_attack': round(float(recall_score(y_test, y_pred, pos_label=1)), 4),
        'f1_attack': round(float(f1_score(y_test, y_pred, pos_label=1)), 4),
        'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
        'predict_time_sec': predict_time,
    }


def save_feature_schema(X_train, numeric_cols):
    known_categories = {}
    for col in CATEGORICAL_COLS:
        known_categories[col] = sorted(X_train[col].astype(str).str.strip().unique().tolist())

    schema = {
        'expected_features': list(X_train.columns),
        'dropped_features': DROPPED_COLS,
        'numeric_features': numeric_cols,
        'categorical_features': CATEGORICAL_COLS,
        'target_column': 'labels',
        'class_mapping': {'0': 'Normal', '1': 'Attack'},
        'known_categories': known_categories,
    }

    schema_path = METADATA_DIR / 'feature_schema.json'
    with schema_path.open('w', encoding='utf-8') as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)

    print(f'Сохранена схема признаков: {schema_path}')


def main():
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    print('Загрузка обучающей и тестовой выборок...')
    df_train = pd.read_csv(RAW_DIR / 'kdd_train.csv')
    df_test = pd.read_csv(RAW_DIR / 'kdd_test.csv')

    X_train, y_train = split_features_and_target(df_train)
    X_test, y_test = split_features_and_target(df_test)

    numeric_cols = [
        col for col in X_train.columns
        if col not in DROPPED_COLS and col not in CATEGORICAL_COLS
    ]

    save_feature_schema(X_train, numeric_cols)

    models_config = build_models(numeric_cols)
    models_info = {}

    for model_id, cfg in models_config.items():
        print(f'\nОбучение модели: {cfg["display_name"]}...')
        t0 = time.time()
        pipeline = cfg['pipeline']
        pipeline.fit(X_train, y_train)
        train_time = round(time.time() - t0, 2)

        metrics = evaluate_on_test(pipeline, X_test, y_test)

        model_folder = MODELS_DIR / model_id
        model_folder.mkdir(parents=True, exist_ok=True)
        model_path = model_folder / 'model.joblib'

        # Сохраняем весь пайплайн целиком со сжатием, чтобы файл занимал меньше места
        joblib.dump(pipeline, model_path, compress=3)
        file_size_mb = round(model_path.stat().st_size / (1024 * 1024), 2)

        # Проверяем, что сохранённая модель сразу загружается и делает предсказания
        loaded_model = joblib.load(model_path)
        sample_preds = loaded_model.predict(X_test.head(5))
        assert len(sample_preds) == 5

        models_info[model_id] = {
            'model_id': model_id,
            'display_name': cfg['display_name'],
            'description': cfg['description'],
            'is_default': cfg['is_default'],
            'supports_proba': hasattr(pipeline, 'predict_proba'),
            'model_path': f'{model_id}/model.joblib',
            'file_size_mb': file_size_mb,
            'params': cfg['params'],
            'metrics_test': metrics,
            'train_time_sec': train_time,
            'trained_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

        print(
            f'Готово: F1(Attack)={metrics["f1_attack"]}, '
            f'Recall(Attack)={metrics["recall_attack"]}, '
            f'размер={file_size_mb} МБ, время обучения={train_time} с'
        )

    info_path = METADATA_DIR / 'models_info.json'
    with info_path.open('w', encoding='utf-8') as f:
        json.dump(models_info, f, ensure_ascii=False, indent=2)

    print(f'\nВсе модели и метаданные сохранены в: {MODELS_DIR}')


if __name__ == '__main__':
    main()