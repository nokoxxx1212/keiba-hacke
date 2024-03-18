import argparse
import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import os
from google.cloud import storage
import pandas_gbq
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from datetime import datetime

def create_netkeiba_url_potential(year_start, year_end):
    """
    Create a DataFrame with potential netkeiba URLs for scraping.

    Args:
        year_start (int): The starting year for scraping.
        year_end (int): The ending year for scraping.

    Returns:
        pd.DataFrame: DataFrame containing the potential netkeiba URLs.
    """

    # Create an empty DataFrame
    netkeiba_url_potential_df = pd.DataFrame(columns=['url', 'current_race_id', 'racecourse_i', 'place', 'race_number_i', 'year'])
    # ①競馬場ごとにループ（10競馬場）
    for year in range(year_start, year_end+1):
        racecourse_list=["01","02","03","04","05","06","07","08","09","10"]
        # racecourse_list=["01"]
        for racecourse_i in range(len(racecourse_list)):
            place = ""
            if racecourse_list[racecourse_i] == "01":
                place = "札幌"
            elif racecourse_list[racecourse_i] == "02":
                place = "函館"
            elif racecourse_list[racecourse_i] == "03":
                place = "福島"
            elif racecourse_list[racecourse_i] == "04":
                place = "新潟"
            elif racecourse_list[racecourse_i] == "05":
                place = "東京"
            elif racecourse_list[racecourse_i] == "06":
                place = "中山"
            elif racecourse_list[racecourse_i] == "07":
                place = "中京"
            elif racecourse_list[racecourse_i] == "08":
                place = "京都"
            elif racecourse_list[racecourse_i] == "09":
                place = "阪神"
            elif racecourse_list[racecourse_i] == "10":
                place = "小倉"    
            # ②開催回数ごとにループ（6回）
            for session_number_i in range(6+1):
                # ③開催日数分ループ（12日）
                for event_date_i in range(12+1):
                    race_id = ''
                    if event_date_i<9:
                        race_id = str(year)+racecourse_list[racecourse_i]+"0"+str(session_number_i+1)+"0"+str(event_date_i+1)
                        url1="https://db.netkeiba.com/race/"+race_id
                    else:
                        race_id = str(year)+racecourse_list[racecourse_i]+"0"+str(session_number_i+1)+"0"+str(event_date_i+1)
                        url1="https://db.netkeiba.com/race/"+race_id
                    # event_date_iの更新をbreakするためのカウンター
                    event_date_i_BreakCounter = 0
                    # ④レース数分ループ（12R）
                    for race_number_i in range(12):
                        if race_number_i<9:
                            url=url1+str("0")+str(race_number_i+1)
                            current_race_id = race_id+str("0")+str(race_number_i+1)
                        else:
                            url=url1+str(race_number_i+1)
                            current_race_id = race_id+str(race_number_i+1)
                        # add the URL to the DataFrame
                        netkeiba_url_potential_df.loc[len(netkeiba_url_potential_df)] = [url, current_race_id, racecourse_i, place, race_number_i, year]
    print(f'Length of netkeiba_url_potential_df: {len(netkeiba_url_potential_df)}')
    return netkeiba_url_potential_df

def export_bq_to_gcs(dataset_id, table_id, column_names, gcs_bucket, destination_blob_name):
    """
    Export a BigQuery table to a Google Cloud Storage bucket.

    Args:
        dataset_id (str): The ID of the BigQuery dataset.
        table_id (str): The ID of the BigQuery table.
        column_names (list): A list of column names to export from the table.
        gcs_bucket (str): The name of the Google Cloud Storage bucket.
        destination_blob_name (str): The name of the destination blob in the bucket.

    Returns:
        None
    """

    # Initialize BigQuery and Storage clients
    bq_client = bigquery.Client()
    storage_client = storage.Client()

    # Specify the BigQuery table
    table_ref = bq_client.dataset(dataset_id).table(table_id)

    # Construct a BigQuery client object.
    client = bigquery.Client()

    # Check if the table exists
    try:
        client.get_table(table_ref)  # Make an API request.
    except NotFound:
        print("Table {}:{} does not exist.".format(dataset_id, table_id))
        return

    # Set up the query (will only get the 'column_names' from the table)
    # query = f"SELECT {', '.join(column_names)} FROM `{table_ref.dataset_id}.{table_ref.table_id}`"
    query = f"SELECT {', '.join([f'`{name}`' for name in column_names])} FROM `{table_ref.dataset_id}.{table_ref.table_id}`"

    # Execute the query and convert the results to a pandas DataFrame
    df = client.query(query).to_dataframe()

    # Save the DataFrame to a csv file
    df.to_csv('temp.csv', index=False)

    # Specify the GCS bucket
    bucket = storage_client.get_bucket(gcs_bucket)

    # Name of the destination blob
    blob = bucket.blob(destination_blob_name)

    # Upload the local file to the bucket
    blob.upload_from_filename('temp.csv')

def download_read_netkeiba_url_scraped_csv_from_gcs(bucket_name, source_blob_name, destination_file_name):
    """
    Download a CSV file from a GCS bucket and read it into a DataFrame.

    Args:
    bucket_name (str): The name of the GCS bucket.
    source_blob_name (str): The name of the blob in the GCS bucket.
    destination_file_name (str): The name of the file to save the downloaded CSV.

    Returns:
    pd.DataFrame: DataFrame containing the data from the downloaded CSV file.
    """
    # Create a client
    storage_client = storage.Client()
    # Get the bucket
    bucket = storage_client.bucket(bucket_name)
    # Get the blob
    blob = bucket.blob(source_blob_name)

    # Check if the file exists
    if blob.exists():
        # Download the file
        blob.download_to_filename(destination_file_name)

        # If the file exists, read it into a DataFrame
        if os.path.exists(destination_file_name):
            netkeiba_url_scraped_df = pd.read_csv(destination_file_name)
            print(f'Length of netkeiba_url_scraped_df: {len(netkeiba_url_scraped_df)}')
            return netkeiba_url_scraped_df
    else:
        print(f"The file {source_blob_name} does not exist in the bucket {bucket_name}.")
        # Return an empty DataFrame
        return pd.DataFrame()

def remove_scraped_urls(netkeiba_url_potential_df, netkeiba_url_scraped_df):
    """
    Remove scraped URLs from the potential URLs DataFrame.

    Args:
        netkeiba_url_potential_df (pd.DataFrame): DataFrame containing the potential URLs.
        netkeiba_url_scraped_df (pd.DataFrame): DataFrame containing the scraped URLs.

    Returns:
        pd.DataFrame: DataFrame with the scraped URLs removed.
    """
    # Check if netkeiba_url_scraped_df is not None and not empty
    if netkeiba_url_scraped_df is not None and not netkeiba_url_scraped_df.empty:
        # Remove rows in netkeiba_url_potential_df that are also in netkeiba_url_scraped_df
        netkeiba_url_unique_df = netkeiba_url_potential_df[~netkeiba_url_potential_df['url'].isin(netkeiba_url_scraped_df['url'])]
        print(f'Length of netkeiba_url_unique_df: {len(netkeiba_url_unique_df)}')
        return netkeiba_url_unique_df
    else:
        print("netkeiba_url_scraped_df is None or empty. Returning netkeiba_url_potential_df as is.")
        return netkeiba_url_potential_df

def scrape_netkeiba_data(netkeiba_url_unique_df):
    # Initialize a list to store the responses
    race_data_all = []
    #取得するデータのヘッダー情報を先に追加しておく
    # race_data_all.append(['race_id','馬','騎手','馬番','走破時間','オッズ','通過順','着順','体重','体重変化','性','齢','斤量','上がり','人気','レース名','日付','開催','クラス','芝orダート','距離','回り','馬場','天気','場id','場名', 'update_at'])
    race_data_all.append(['race_id', 'horse', 'jockey', 'horse_number', 'run_time', 'odds', 'pass_order', 'rank', 'weight', 'weight_change', 'gender', 'age', 'load', 'rise', 'popularity', 'race_name', 'date', 'event', 'class', 'turf_or_dirt', 'distance', 'lap', 'racecourse', 'weather', 'place_id', 'place_name', 'update_at'])

    # Loop over each row in the DataFrame
    for _, row in netkeiba_url_unique_df.iterrows():
        print(f'Processing loop {_} of {len(netkeiba_url_unique_df)}')
        url = row['url']
        current_race_id = row['current_race_id']
        racecourse_i = row['racecourse_i']
        place = row['place']
        race_number_i = row['race_number_i']
        year = row['year']
        try:
            r=requests.get(url)
        #リクエストを投げすぎるとエラーになることがあるため
        #失敗したら10秒待機してリトライする
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            print("Retrying in 10 seconds...")
            time.sleep(10)  # 10秒待機
            r=requests.get(url)
        #バグ対策でdecode
        soup = BeautifulSoup(r.content.decode("euc-jp", "ignore"), "html.parser")
        soup_span = soup.find_all("span")
        # テーブルを指定
        main_table = soup.find("table", {"class": "race_table_01 nk_tb_common"})
    
        # テーブル内の全ての行を取得
        try:
            main_rows = main_table.find_all("tr")
        except:
            print('continue: ' + url)
            continue
    
        race_data = []
        for i, row in enumerate(main_rows[1:], start=1):# ヘッダ行をスキップ
            cols = row.find_all("td")
            #走破時間
            runtime=''
            try:
                runtime= cols[7].text.strip()
            except IndexError:
                runtime = ''
            soup_nowrap = soup.find_all("td",nowrap="nowrap",class_=None)
            #通過順
            pas = ''
            try:
                pas = str(cols[10].text.strip())
            except:
                pas = ''
            weight = 0
            weight_dif = 0
            #体重
            var = cols[14].text.strip()
            try:
                weight = int(var.split("(")[0])
                weight_dif = int(var.split("(")[1][0:-1])
            except ValueError:
                weight = 0
                weight_dif = 0
            weight = weight
            weight_dif = weight_dif
            #上がり
            last = ''
            try:
                last = cols[11].text.strip()
            except IndexError:
                last = ''
            #人気
            pop = ''
            try:
                pop = cols[13].text.strip()
            except IndexError:
                pop = ''
            
            #レースの情報
            try:
                var = soup_span[8]
                sur=str(var).split("/")[0].split(">")[1][0]
                rou=str(var).split("/")[0].split(">")[1][1]
                dis=str(var).split("/")[0].split(">")[1].split("m")[0][-4:]
                con=str(var).split("/")[2].split(":")[1][1]
                wed=str(var).split("/")[1].split(":")[1][1]
            except IndexError:
                try:
                    var = soup_span[7]
                    sur=str(var).split("/")[0].split(">")[1][0]
                    rou=str(var).split("/")[0].split(">")[1][1]
                    dis=str(var).split("/")[0].split(">")[1].split("m")[0][-4:]
                    con=str(var).split("/")[2].split(":")[1][1]
                    wed=str(var).split("/")[1].split(":")[1][1]
                except IndexError:
                    var = soup_span[6]
                    sur=str(var).split("/")[0].split(">")[1][0]
                    rou=str(var).split("/")[0].split(">")[1][1]
                    dis=str(var).split("/")[0].split(">")[1].split("m")[0][-4:]
                    con=str(var).split("/")[2].split(":")[1][1]
                    wed=str(var).split("/")[1].split(":")[1][1]
            soup_smalltxt = soup.find_all("p",class_="smalltxt")
            detail=str(soup_smalltxt).split(">")[1].split(" ")[1]
            date=str(soup_smalltxt).split(">")[1].split(" ")[0]
            clas=str(soup_smalltxt).split(">")[1].split(" ")[2].replace(u'\xa0', u' ').split(" ")[0]
            title=str(soup.find_all("h1")[1]).split(">")[1].split("<")[0]
            update_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
            race_data = [
                current_race_id,
                cols[3].text.strip(),#馬の名前
                cols[6].text.strip(),#騎手の名前
                cols[2].text.strip(),#馬番
                runtime,#走破時間
                cols[12].text.strip(),#オッズ,
                pas,#通過順
                cols[0].text.strip(),#着順
                weight,#体重
                weight_dif,#体重変化
                cols[4].text.strip()[0],#性
                cols[4].text.strip()[1],#齢
                cols[5].text.strip(),#斤量
                last,#上がり
                pop,#人気,
                title,#レース名
                date,#日付
                detail,
                clas,#クラス
                sur,#芝かダートか
                dis,#距離
                rou,#回り
                con,#馬場状態
                wed,#天気
                racecourse_i,#場
                place,
                update_at]
            # Append the list to the race_data_all
            race_data_all.append(race_data)

    print(f'Length of race_data_all: {len(race_data_all)}')
    return race_data_all

def load_df_to_bigquery(df, table_id, project_id):
    pandas_gbq.to_gbq(df, table_id, project_id, if_exists='append')
    # pandas_gbq.to_gbq(df, table_id, project_id=project_id, if_exists='replace')

if __name__ == "__main__":
    # Parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--year_start', type=int, required=True, help='Start year.')
    parser.add_argument('--year_end', type=int, required=True, help='End year.')
    args = parser.parse_args()
    year_start = args.year_start
    year_end = args.year_end

    # スクレイピング候補のURLを作成
    netkeiba_url_potential_df = create_netkeiba_url_potential(year_start, year_end)

    # スクレイピング済みのURLをBQから取得
    export_bq_to_gcs("kh", "netkeiba_url_scraped", ['url'], "dev-kh-gcs-bucket", "data/netkeiba_url_scraped.csv")
    netkeiba_url_scraped_df = download_read_netkeiba_url_scraped_csv_from_gcs("dev-kh-gcs-bucket", "data/netkeiba_url_scraped.csv", "netkeiba_url_scraped.csv")
    
    # 今回スクレイピングするURLを抽出
    netkeiba_url_unique_df = remove_scraped_urls(netkeiba_url_potential_df, netkeiba_url_scraped_df)

    # スクレイピングしてデータをBQに保存
    race_data_all = scrape_netkeiba_data(netkeiba_url_unique_df)
    column_names = race_data_all[0]
    race_data_all_df = pd.DataFrame(race_data_all[1:], columns=column_names)
    load_df_to_bigquery(race_data_all_df, 'kh.raw_netkeiba_race', 'keiba-hacke')
    load_df_to_bigquery(netkeiba_url_unique_df, 'kh.netkeiba_url_scraped', 'keiba-hacke')