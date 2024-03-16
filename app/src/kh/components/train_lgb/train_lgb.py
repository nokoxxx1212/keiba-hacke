import lightgbm as lgb
import pandas as pd
from sklearn.metrics import roc_curve,roc_auc_score
import numpy as np
import os
import datetime
from pandas.io import gbq
from google.cloud import storage
import argparse
from google.cloud import bigquery

def get_train_data(project_id, table_name, year_start, year_end):
    client = bigquery.Client(project=project_id)

    # SQL query
    query = f"""
    SELECT *
    FROM `{table_name}`
    WHERE year >= {year_start} AND year <= {year_end}
    """

    # Run the query
    query_job = client.query(query)

    # Convert the results into a pandas DataFrame
    df = query_job.to_dataframe()

    print(f'Length of the dataframe: {len(df)}')

    return df

def _split_date(df, test_size):
    sorted_id_list = df.sort_values('date').index.unique()
    train_id_list = sorted_id_list[:round(len(sorted_id_list) * (1-test_size))]
    test_id_list = sorted_id_list[round(len(sorted_id_list) * (1-test_size)):]
    train = df.loc[train_id_list]
    test = df.loc[test_id_list]
    return train, test

def train(df):
    """
    Trains a LightGBM model using the given dataframe.

    Args:
        df (pandas.DataFrame): The input dataframe containing the training data.

    Returns:
        str: The file path of the saved model.
    """
    # データの読み込み
    data = df
    #rankを変換
    # rankを整数に変換
    data['rank'] = data['rank'].astype(int)
    data['rank'] = data['rank'].map(lambda x: 1 if x<4 else 0)

    # データ型の変換
    cols_to_convert = ['race_id', 'horse_number', 'age', 'update_at', 'horse_number1', 'odds1', 'rise1', 'rank1', 'horse_number2', 'odds2', 'rise2', 'rank2', 'horse_number3', 'odds3', 'rise3', 'rank3', 'horse_number4', 'odds4', 'rise4', 'rank4', 'horse_number5', 'odds5', 'rise5', 'rank5']
    for col in cols_to_convert:
        data[col] = pd.to_numeric(data[col], errors='coerce')
    
    # 特徴量とターゲットの分割
    train, test = _split_date(data, 0.3)
    X_train = train.drop(['rank','odds','popularity','rise','run_time','pass_order'], axis=1)
    y_train = train['rank']
    X_test = test.drop(['rank','odds','popularity','rise','run_time','pass_order'], axis=1)
    y_test = test['rank']
    
    # LightGBMデータセットの作成
    train_data = lgb.Dataset(X_train, label=y_train)
    valid_data = lgb.Dataset(X_test, label=y_test)
    
    params={
        'num_leaves':32, # default=32
        'min_data_in_leaf':190, # default=190
        'class_weight':'balanced',
        'random_state':100
    }
    
    # モデルの学習
    print("Training the model...")
    lgb_clf = lgb.LGBMClassifier(**params)
    lgb_clf.fit(X_train, y_train)
    y_pred_train = lgb_clf.predict_proba(X_train)[:,1]
    y_pred = lgb_clf.predict_proba(X_test)[:,1]
    print("Model training complete.")
    
    #モデルの評価
    #print(roc_auc_score(y_train,y_pred_train))
    print(roc_auc_score(y_test,y_pred))
    total_cases = len(y_test)  # テストデータの総数
    TP = (y_test == 1) & (y_pred >= 0.5)  # True positives
    FP = (y_test == 0) & (y_pred >= 0.5)  # False positives
    TN = (y_test == 0) & (y_pred < 0.5)  # True negatives
    FN = (y_test == 1) & (y_pred < 0.5)  # False negatives
    
    TP_count = sum(TP)
    FP_count = sum(FP)
    TN_count = sum(TN)
    FN_count = sum(FN)
    
    accuracy_TP = TP_count / total_cases * 100
    misclassification_rate_FP = FP_count / total_cases * 100
    accuracy_TN = TN_count / total_cases * 100
    misclassification_rate_FN = FN_count / total_cases * 100
    
    print("Total cases:", total_cases)
    print("True positives:", TP_count, "(", "{:.2f}".format(accuracy_TP), "%)")
    print("False positives:", FP_count, "(", "{:.2f}".format(misclassification_rate_FP), "%)")
    print("True negatives:", TN_count, "(", "{:.2f}".format(accuracy_TN), "%)")
    print("False negatives:", FN_count, "(", "{:.2f}".format(misclassification_rate_FN), "%)")
    
    # True Positives (TP): 実際に1で、予測も1だったもの
    # False Positives (FP): 実際は0だが、予測では1だったもの
    # True Negatives (TN): 実際に0で、予測も0だったもの
    # False Negatives (FN): 実際は1だが、予測では0だったもの

    # モデルの保存
    # 現在の日時を取得し、それを文字列に変換します
    now = datetime.datetime.now()
    dir_name = "model/" + str(now.strftime('%Y%m%d%H%M'))
    # ディレクトリを作成します
    os.makedirs(dir_name, exist_ok=True)
    # モデルを保存します
    model_path = f'{dir_name}/model.txt'
    lgb_clf.booster_.save_model(model_path)

    # 特徴量の重要度を取得
    importance = lgb_clf.feature_importances_
    
    # 特徴量の名前を取得
    feature_names = X_train.columns
    
    # 特徴量の重要度を降順にソート
    indices = np.argsort(importance)[::-1]
    
    # 特徴量の重要度を降順に表示
    for f in range(X_train.shape[1]):
        print("%2d) %-*s %f" % (f + 1, 30, feature_names[indices[f]], importance[indices[f]]))
    
    return model_path

def upload_model_to_gcs(local_file_path, gcs_file_path, bucket_name):
    # GCSクライアントを作成します
    client = storage.Client()

    # バケットを取得します
    bucket = client.get_bucket(bucket_name)

    # ファイルをGCSにアップロードします
    blob = bucket.blob(gcs_file_path)
    blob.upload_from_filename(local_file_path)

if __name__ == "__main__":
    # Parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--year_start', type=int, required=True, help='Start year.')
    parser.add_argument('--year_end', type=int, required=True, help='End year.')
    args = parser.parse_args()
    year_start = args.year_start
    year_end = args.year_end

    # トレーニングデータ取得
    train_data_df = get_train_data('keiba-hacke', 'kh.dm_netkeiba_race', year_start, year_end)

    # Run the training
    model_path = train(train_data_df)

    # GCSにモデルをアップロード
    # ローカルと同じパスに保存
    upload_model_to_gcs(model_path, model_path, "dev-kh-gcs-bucket")
    # latestモデルとして保存
    upload_model_to_gcs(model_path, "model/latest/model.txt", "dev-kh-gcs-bucket")