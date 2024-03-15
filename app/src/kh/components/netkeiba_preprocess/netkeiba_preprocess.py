import pandas as pd
from sklearn.preprocessing import LabelEncoder
import numpy as np
from google.cloud import bigquery
from datetime import datetime
import argparse
import pandas_gbq

def _class_mapping(row):
    """
    Maps the class label based on the given row.

    Args:
        row (str): The row to be mapped.

    Returns:
        int: The mapped class label.

    """
    mappings = {'障害':0, 'G1': 10, 'G2': 9, 'G3': 8, '(L)': 7, 'オープン': 7,'OP': 7, '3勝': 6, '1600': 6, '2勝': 5, '1000': 5, '1勝': 4, '500': 4, '新馬': 3, '未勝利': 1}
    for key, value in mappings.items():
        if key in row:
            return value
    return 0  # If no mapping is found, return 0

def get_data_from_bigquery(project_id, table_name, update_time_threshold):
    """
    Get data from BigQuery based on the specified project ID, table name, and update time threshold.

    Args:
        project_id (str): The ID of the BigQuery project.
        table_name (str): The name of the BigQuery table.
        update_time_threshold (str): The update time threshold in the format 'YYYY-MM-DD HH:MM:SS'.

    Returns:
        pandas.DataFrame: The data retrieved from BigQuery.

    """
    client = bigquery.Client(project=project_id)

    # SQL query
    query = f"""
    SELECT *
    FROM `{project_id}.{table_name}`
    WHERE TIMESTAMP(update_at) >= TIMESTAMP('{update_time_threshold}')
    """

    # Run the query
    query_job = client.query(query)

    # Convert the results into a pandas DataFrame
    df = query_job.to_dataframe()

    print(f'Length of the dataframe: {len(df)}')

    return df

def preprocess(df):
    # 基準とする年度
    yearStart = 2010
    #for for_year in yearList:
    #    var_path = "data/" + str(for_year) + "_new.csv"
    #    var_data = pd.read_csv(
    #        var_path,
    #        encoding="SHIFT-JIS",
    #        header=0,
    #        parse_dates=['日付'], 
    #        date_parser=lambda x: pd.to_datetime(x, format='%Y年%m月%d日')
    #    )
    #    # '着順'カラムの値を数値に変換しようとして、エラーが発生する場合はNaNにする
    #    var_data['着順'] = pd.to_numeric(var_data['着順'], errors='coerce')
    #    # NaNの行を削除する
    #    var_data = var_data.dropna(subset=['着順'])
    #    # 必要であれば、'着順'カラムのデータ型を整数に変換する
    #    var_data['着順'] = var_data['着順'].astype(int)
    
    #    df.append(var_data)
    # DataFrameの結合
    df_combined = df

    # 空文字列をNaNに置き換えます。
    df_combined.replace('', np.nan, inplace=True)

    # NaNを含む行を削除します。
    df_combined.dropna(subset=['run_time'], inplace=True)

    # 既存のコード：run_timeを秒に変換
    time_parts = df_combined['run_time'].str.split(':', expand=True)
    seconds = time_parts[0].astype(float) * 60 + time_parts[1].str.split('.', expand=True)[0].astype(float) + time_parts[1].str.split('.', expand=True)[1].astype(float) / 10
    # 前方補完
    seconds = seconds.fillna(method='ffill')
    
    # 平均と標準偏差を計算
    mean_seconds = seconds.mean()
    std_seconds = seconds.std()
    
    # 標準化を行う
    df_combined['run_time'] = -((seconds - mean_seconds) / std_seconds)
    
    # 外れ値の処理：-3より小さい値は-3に、2.5より大きい値は2に変換
    df_combined['run_time'] = df_combined['run_time'].apply(lambda x: -3 if x < -3 else (2 if x > 2.5 else x))
    
    # 2回目の標準化の前に再度平均と標準偏差を計算
    mean_seconds_2 = df_combined['run_time'].mean()
    std_seconds_2 = df_combined['run_time'].std()
    
    # 2回目の標準化
    df_combined['run_time'] = (df_combined['run_time'] - mean_seconds_2) / std_seconds_2
    print('1回目平均' + str(mean_seconds))
    print('2回目平均' + str(mean_seconds_2))
    print('1回目標準偏差' + str(std_seconds))
    print('2回目標準偏差' + str(std_seconds_2))
    
    # データを格納するDataFrameを作成
    time_df = pd.DataFrame({
        'Mean': [mean_seconds, mean_seconds_2],
        'Standard Deviation': [std_seconds, std_seconds_2]
    })
    # indexに名前を付ける
    time_df.index = ['First Time', 'Second Time']
    # DataFrameをCSVファイルとして出力
    # time_df.to_csv('config/standard_deviation.csv')
    
    #pass_orderの平均を出す
    pas = df_combined['pass_order'].str.split('-', expand=True)
    df_combined['pass_order'] = pas.astype(float).mean(axis=1)
    
    # mapを使ったラベルの変換
    df_combined['class'] = df_combined['class'].apply(_class_mapping)          
    sex_mapping = {'牡':0, '牝': 1, 'セ': 2}
    df_combined['gender'] = df_combined['gender'].map(sex_mapping)
    shiba_mapping = {'芝': 0, 'ダ': 1, '障': 2}
    df_combined['turf_or_dirt'] = df_combined['turf_or_dirt'].map(shiba_mapping)
    mawari_mapping = {'右': 0, '左': 1, '芝': 2, '直': 2}
    df_combined['lap'] = df_combined['lap'].map(mawari_mapping)
    baba_mapping = {'良': 0, '稍': 1, '重': 2, '不': 3}
    df_combined['racecourse'] = df_combined['racecourse'].map(baba_mapping)
    tenki_mapping = {'晴': 0, '曇': 1, '小': 2, '雨': 3, '雪': 4}
    df_combined['weather'] = df_combined['weather'].map(tenki_mapping)
    print("データ変換：完了")
    print("近5走取得：開始")
    # '馬'と'日付'に基づいて降順にソート
    df_combined.sort_values(by=['horse', 'date'], ascending=[True, False], inplace=True)
    
    features = ['horse_number', 'jockey', 'load', 'odds', 'weight', 'weight_change', 'rise', 'pass_order', 'rank', 'distance', 'class', 'run_time', 'turf_or_dirt', 'weather','racecourse']
    #斤量、周り
    # 同じ馬の過去5レースの情報を新しいレース結果にマージ
    for i in range(1, 6):
        df_combined[f'date{i}'] = df_combined.groupby('horse')['date'].shift(-i)
        for feature in features:
            df_combined[f'{feature}{i}'] = df_combined.groupby('horse')[feature].shift(-i)
    
    # 同じ馬のデータで欠損値を補完
    for feature in features:
        for i in range(1, 6):
            df_combined[f'{feature}{i}'] = df_combined.groupby('horse')[f'{feature}{i}'].fillna(method='ffill')
    
    # race_id と 馬 でグルーピングし、各特徴量の最新の値を取得
    df_combined = df_combined.groupby(['race_id', 'horse'], as_index=False).last()
    
    # race_idでソート
    df_combined.sort_values(by='race_id', ascending=False, inplace=True)
    
    print("近5走取得：終了")
    # '---' をNaNに置き換える
    df_combined.replace('---', np.nan, inplace=True)
    print("日付変換：開始")
    # 'distance'と'distance1'をfloat型に変換します。
    df_combined['distance'] = df_combined['distance'].astype(float)
    df_combined['distance1'] = df_combined['distance1'].astype(float)
    df_combined['distance2'] = df_combined['distance2'].astype(float)
    df_combined['distance3'] = df_combined['distance3'].astype(float)
    df_combined['distance4'] = df_combined['distance4'].astype(float)
    df_combined['distance5'] = df_combined['distance5'].astype(float)
    # 'date'と'date1'を日付型に変換します。
    df_combined['date'] = pd.to_datetime(df_combined['date'], format='%Y年%m月%d日')
    df_combined['date1'] = pd.to_datetime(df_combined['date1'], format='%Y年%m月%d日')
    df_combined['date2'] = pd.to_datetime(df_combined['date2'], format='%Y年%m月%d日')
    df_combined['date3'] = pd.to_datetime(df_combined['date3'], format='%Y年%m月%d日')
    df_combined['date4'] = pd.to_datetime(df_combined['date4'], format='%Y年%m月%d日')
    df_combined['date5'] = pd.to_datetime(df_combined['date5'], format='%Y年%m月%d日')
    #距離差と日付差を計算
    df_combined = df_combined.assign(
        distance_diff = df_combined['distance'] - df_combined['distance1'],
        date_diff = (df_combined['date'] - df_combined['date1']).dt.days,
        distance_diff1 = df_combined['distance1'] - df_combined['distance2'],
        date_diff1 = (df_combined['date1'] - df_combined['date2']).dt.days,
        distance_diff2 = df_combined['distance2'] - df_combined['distance3'],
        date_diff2 = (df_combined['date2'] - df_combined['date3']).dt.days,
        distance_diff3 = df_combined['distance3'] - df_combined['distance4'],
        date_diff3 = (df_combined['date3'] - df_combined['date4']).dt.days,
        distance_diff4 = df_combined['distance4'] - df_combined['distance5'],
        date_diff4 = (df_combined['date4'] - df_combined['date5']).dt.days
    )
    
    # 斤量に関連する列を数値に変換し、変換できないデータはNaNにします。
    kinryo_columns = ['load', 'load1', 'load2', 'load3', 'load4','load5']
    for col in kinryo_columns:
        df_combined[col] = pd.to_numeric(df_combined[col], errors='coerce')
    
    # 平均斤量を計算します。
    df_combined['average_load'] = df_combined[kinryo_columns].mean(axis=1)
    
    # 騎手の勝率
    jockey_win_rate = df_combined.groupby('jockey')['rank'].apply(lambda x: (x==1).sum() / x.count()).reset_index()
    jockey_win_rate.columns = ['jockey', 'jockey_win_rate']
    # jockey_win_rate.to_csv('calc_rate/jockey_win_rate.csv', index=False)
    # '騎手'をキーにしてdf_combinedとjockey_win_rateをマージする
    df_combined = pd.merge(df_combined, jockey_win_rate, on='jockey', how='left')
    
    #日付
    # 日付カラムから年、月、日を抽出
    df_combined['year'] = df_combined['date'].dt.year
    df_combined['month'] = df_combined['date'].dt.month
    df_combined['day'] = df_combined['date'].dt.day
    # (年-yearStart)*365 + 月*30 + 日 を計算し新たな '日付'カラムを作成
    df_combined['date'] = (df_combined['year'] - yearStart) * 365 + df_combined['month'] * 30 + df_combined['day']
    
    df_combined['year'] = df_combined['date1'].dt.year
    df_combined['month'] = df_combined['date1'].dt.month
    df_combined['day'] = df_combined['date1'].dt.day
    df_combined['date1'] = (df_combined['year'] - yearStart) * 365 + df_combined['month'] * 30 + df_combined['day']
    
    df_combined['year'] = df_combined['date2'].dt.year
    df_combined['month'] = df_combined['date2'].dt.month
    df_combined['day'] = df_combined['date2'].dt.day
    df_combined['date2'] = (df_combined['year'] - yearStart) * 365 + df_combined['month'] * 30 + df_combined['day']
    
    df_combined['year'] = df_combined['date3'].dt.year
    df_combined['month'] = df_combined['date3'].dt.month
    df_combined['day'] = df_combined['date3'].dt.day
    df_combined['date3'] = (df_combined['year'] - yearStart) * 365 + df_combined['month'] * 30 + df_combined['day']
    
    df_combined['year'] = df_combined['date4'].dt.year
    df_combined['month'] = df_combined['date4'].dt.month
    df_combined['day'] = df_combined['date4'].dt.day
    df_combined['date4'] = (df_combined['year'] - yearStart) * 365 + df_combined['month'] * 30 + df_combined['day']
    
    df_combined['year'] = df_combined['date5'].dt.year
    df_combined['month'] = df_combined['date5'].dt.month
    df_combined['day'] = df_combined['date5'].dt.day
    df_combined['date5'] = (df_combined['year'] - yearStart) * 365 + df_combined['month'] * 30 + df_combined['day']
    
    # 不要となった 'year', 'month', 'day' カラムを削除
    df_combined.drop(['year', 'month', 'day'], axis=1, inplace=True)
    print("日付変換：終了")
    
    categorical_features = ['horse', 'jockey', 'race_name', 'event', 'place_name', 'jockey1', 'jockey2', 'jockey3', 'jockey4', 'jockey5']  # カテゴリカル変数の列名を指定してください
    
    # ラベルエンコーディング
    for i, feature in enumerate(categorical_features):
        print(f"\rProcessing feature {i+1}/{len(categorical_features)}", end="")
        le = LabelEncoder()
        df_combined[feature] = le.fit_transform(df_combined[feature])
    
    return df_combined

def load_df_to_bigquery(df, table_id, project_id):
    pandas_gbq.to_gbq(df, table_id, project_id, if_exists='append')

if __name__ == "__main__":
    # Parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--update_time_threshold', type=str, required=True, help='Update time threshold.')
    args = parser.parse_args()
    update_time_threshold = datetime.strptime(args.update_time_threshold, '%Y-%m-%d %H:%M:%S')

    # Preprocess the data
    # 1. Export the raw data from BigQuery
    raw_df = get_data_from_bigquery('keiba-hacke', 'kh.raw_netkeiba_race', update_time_threshold)
    print(raw_df.head(10))
    # 2. Preprocess the data
    preprocessed_df = preprocess(raw_df)
    print(preprocessed_df.head(10))
    # 3. Load the preprocessed data to BigQuery
    load_df_to_bigquery(preprocessed_df, 'kh.dm_netkeiba_race', 'keiba-hacke')