# -*- coding: utf-8 -*-
import pandas as pd
import time
import datetime
import datetime
import requests
from bs4 import BeautifulSoup
import re
import numpy as np
import pickle
from sklearn.preprocessing import LabelEncoder
from datetime import timedelta
import argparse
import os

def read_html(url,n):
    r = requests.get(url)
    c = r.content
    df = pd.read_html(c)[n]
    return df

def get_tyoukyou_data(race_id):
    url = 'https://race.netkeiba.com/race/oikiri.html?race_id=' + str(race_id)
    df = read_html(url,0)
    
    return df

def scrape_race_info(soup,day):
    text_race_data = str(soup.find('div',attrs={'class':'RaceData01'}))
    race_data = soup.find('div',attrs={'class':'RaceData01'})
        
    whether_text = [text_race_data[text_race_data.find("天候")+3:text_race_data.find('<span class="Icon_Weather')]]
    course_type_text = [text_race_data[text_race_data.find("(")+1:text_race_data.find(")")]]
    ground_type_text = [race_data.find_all('span')[0].text]
    ground_state_text = [race_data.find_all('span')[2].text[race_data.find_all('span')[2].text.find(":")+1:]]

    race_info = ground_state_text+ ground_type_text + whether_text + course_type_text + day
    race_data2 = soup.find('div',attrs={'class':'RaceData02'})
    sub_texts = race_data2.text.split("\n")
    
    info_dict = {}

    title = soup.find('title').text

        
    if "500万" in sub_texts[5] or "1勝" in sub_texts[5] or "１勝" in sub_texts[5]:
        info_dict["class"] = "１勝"
    elif "1000万" in sub_texts[5] or "2勝" in sub_texts[5] or "２勝" in sub_texts[5]:
        info_dict["class"] = "２勝"
    elif "1600万" in sub_texts[5] or "3勝" in sub_texts[5] or "３勝" in sub_texts[5]:
        info_dict["class"] = "３勝"
    elif "オープン" in sub_texts[5]:
        info_dict["class"] = "オープン"
    elif "未勝利" in sub_texts[5]:
        info_dict["class"] = "未勝利"
    elif "新馬" in sub_texts[5]:
        info_dict["class"] = "新馬"
    else:
        info_dict["class"] = "不明"

    for text in race_info:
        if "芝" in text:
            info_dict["race_type"] = '芝'
        if "ダ" in text:
            info_dict["race_type"] = 'ダート'
        if "障" in text:
            info_dict["race_type"] = "障害"
        if "m" in text:
            info_dict["course_len"] = int(re.findall(r"\d+", text)[0])
        if text in ["良", "稍重", "重", "不良", "稍", "不"]:
            info_dict["ground_state"] = text
        if text in ["曇", "晴", "雨", "小雨", "小雪", "雪"]:
            info_dict["weather"] = text
        if "年" in text:
            info_dict["date"] = text
        if "右" in text:
            info_dict["course_type"] = "右"
        if "左" in text:
            info_dict["course_type"] = "左"
        if "直線" in text:
            info_dict["course_type"] = "直線"

    return info_dict

def scrape_id(soup,id_name):
    id_list = []

    if id_name == "horse":
        words  = soup.find_all("td", attrs={"class": "HorseInfo"})
        for word in words:
            id_list.append(word.find("a").get('href')[-10:])
    elif id_name == "jockey":
        words  = soup.find_all("td", attrs={"class": "Jockey"})
        for word in words:
            id_list.append(word.find("a").get('href')[-6:-1])
        
    return id_list

def make_horse_table(df):
    df_tmp = pd.DataFrame()
    df = df.rename(columns=lambda s: s.replace(" ",""))
    df_tmp["枠"] = df[("枠","枠")].values
    df_tmp["馬番"] = df[("馬番","馬番")].values
    df_tmp["馬名"] = df[("馬名","馬名")].values
    df_tmp["性齢"] = df[("性齢","性齢")].values
    df_tmp["斤量"] = df[("斤量","斤量")].values
    df_tmp["騎手"] = df[("騎手","騎手")].values
    df_tmp["厩舎"] = df[("厩舎","厩舎")].values
    df_tmp["馬体重(増減)"] = df[("馬体重(増減)","馬体重(増減)")].values

    return df_tmp

def scrape_race_span(race_id,df_length):
    url = "https://race.netkeiba.com/race/shutuba_past.html?race_id="+race_id+"&rf=shutuba_submenu"
    df = read_html(url,0)
    df = df.rename(columns=lambda s: s.replace(" ",""))
    df_tmp = pd.DataFrame()
    df_tmp["馬番"] = df["馬番"]
    texts = list(df["馬名"].values)
    race_span = []
    for text in texts:
        words = text.split( )
        flag = False
        for word in words:
            if "中" in word and "週" in word:
                race_span.append(int(word[1:-1]))
                flag = True
                continue
            elif "連闘" in word:
                race_span.append(1)
                flag = True
                continue
        if flag == False:
            race_span.append(0)
    if len(df) != df_length:
        flag = False
    else:
        flag = True
        df_tmp["span"] = race_span
    time.sleep(0.1)
    return df_tmp,flag

def scrape_race_predict(race_id_list, day):
    race_tables = {}
    race_infos = {}
    for race_id in race_id_list:
        
        url = "https://race.netkeiba.com/race/shutuba.html?race_id=" + race_id + "&rf=race_submenu"
        df = read_html(url,0)
        df = df.rename(columns=lambda s: s.replace(" ",""))
        table = make_horse_table(df)

        html = requests.get(url)
        html.encoding = "EUC-JP"
        soup = BeautifulSoup(html.text, "html.parser")

        horse_id_list = scrape_id(soup,"horse")
        jockey_id_list = scrape_id(soup,"jockey")

        if len(horse_id_list) != len(df) or len(jockey_id_list) != len(df):
            continue

        table["horse_id"] = horse_id_list
        table["jockey_id"] = jockey_id_list
        
        tyoukyou = get_tyoukyou_data(race_id)
        table['評価'] = tyoukyou['評価']
        table['評価ランク'] = tyoukyou['評価.1']

        info_dict = {}
        info_dict = scrape_race_info(soup,day)
        race_tables[race_id] = table
        race_infos[race_id] = info_dict
        

    return race_tables,race_infos

def scrape_horse_results(horse_id_list, pre_horse_id=[]):
    horse_results = {}
    for horse_id in horse_id_list:
        if horse_id in pre_horse_id:
            continue
        try:
            url = 'https://db.netkeiba.com/horse/' + horse_id
            
            html = requests.get(url)
            html.encoding = "EUC-JP"
            soup = BeautifulSoup(html.text, "html.parser")
            
            texts = soup.find("div", attrs={"class": "db_prof_area_02"}).find_all("a")
            for text in texts:
                if "breeder" in str(text):
                    Borned_place = str(text)[str(text).find('e="')+3:str(text).find('">')]
            
            df = read_html(url,3)
            if df.columns[0]=='受賞歴':
                df = read_html(url,4)

            df["Borned_place"] = Borned_place
            
            df["Blood_f_id"] = soup.find_all("td", attrs={"class": "b_ml"})[0].find('a').get('href')[11:-1]
            df["Blood_ff_id"] = soup.find_all("td", attrs={"class": "b_ml"})[1].find('a').get('href')[11:-1]
            df["Blood_mf_id"] = soup.find_all("td", attrs={"class": "b_ml"})[2].find('a').get('href')[11:-1]

            horse_results[horse_id] = df
            
            time.sleep(0.1)
        except IndexError:
            continue
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(e)
            break
        except:
            break
    return horse_results

class HorseResults:
    def __init__(self, horse_results):
        self.horse_results = horse_results[['日付','着順', '賞金','上り','通過']]
        self.preprocessing()

    def preprocessing(self):
        df = self.horse_results.copy()

        # 着順に数字以外の文字列が含まれているものを取り除く
        df['着順'] = pd.to_numeric(df['着順'], errors='coerce')
        df.dropna(subset=['着順'], inplace=True)
        df['着順'] = df['着順'].astype(int)
        df['着順'].fillna(0, inplace=True)

        df["date"] = pd.to_datetime(df["日付"])

        #賞金のNaNを0で埋める
        df['賞金'].fillna(0, inplace=True)

        def corner(x,n):
            if type(x) != str:
                return x
            elif n==4:
                return int(re.findall(r'\d+', x)[-1])
            elif n==1:
                return int(re.findall(r'\d+', x)[0])

        df['first_corner'] = df['通過'].map(lambda x: corner(x,1))
        df['final_corner'] = df['通過'].map(lambda x: corner(x,4))

        df['final_to_rank'] = df['final_corner'] - df['着順']
        df['first_to_rank'] = df['first_corner'] - df['着順']
        df['first_to_final'] = df['final_corner'] - df['first_corner']

        self.horse_results = df

    def average(self, horse_id_list, date, n_samples='all'):
        self.horse_results.reindex(horse_id_list, axis=1)
        target_df = self.horse_results.query('index in @horse_id_list')

        #過去何走分取り出すか指定
        if n_samples == 'all':
            filtered_df = target_df[target_df['date'] < date]
        elif n_samples > 0:
            filtered_df = target_df[target_df['date'] < date].sort_values('date', ascending=False).groupby(level=0).head(n_samples)
        else:
            raise Exception('n_samples must be >0')

        average = filtered_df.groupby(level=0)[['着順', '賞金', '上り','first_corner','final_corner','final_to_rank','first_to_rank','first_to_final']].mean()
        return average.rename(columns={'着順':'平均着順_{}R'.format(n_samples),
                                       '賞金':'平均賞金_{}R'.format(n_samples),
                                       '上り':'平均上り_{}R'.format(n_samples),
                                       'first_corner':'平均first_corner_{}R'.format(n_samples),
                                       'final_corner':'平均final_corner_{}R'.format(n_samples),
                                       'final_to_rank':'平均final_to_rank_{}R'.format(n_samples),
                                       'first_to_rank':'平均first_to_rank_{}R'.format(n_samples),
                                       'first_to_final':'平均first_to_final_{}R'.format(n_samples),})

    def std(self, horse_id_list, date, n_samples='all'):
        self.horse_results.reindex(horse_id_list, axis=1)
        target_df = self.horse_results.query('index in @horse_id_list')

        #過去何走分取り出すか指定
        if n_samples == 'all':
            filtered_df = target_df[target_df['date'] < date]
        elif n_samples > 0:
            filtered_df = target_df[target_df['date'] < date].sort_values('date', ascending=False).groupby(level=0).head(n_samples)
        else:
            raise Exception('n_samples must be >0')

        average = filtered_df.groupby(level=0)[['着順', '賞金', '上り','first_corner','final_corner','final_to_rank','first_to_rank','first_to_final']].std()
        return average.rename(columns={'着順':'偏差着順_{}R'.format(n_samples),
                                       '賞金':'偏差賞金_{}R'.format(n_samples),
                                       '上り':'偏差上り_{}R'.format(n_samples),
                                       'first_corner':'偏差first_corner_{}R'.format(n_samples),
                                       'final_corner':'偏差final_corner_{}R'.format(n_samples),
                                       'final_to_rank':'偏差final_to_rank_{}R'.format(n_samples),
                                       'first_to_rank':'偏差first_to_rank_{}R'.format(n_samples),
                                       'first_to_final':'偏差first_to_final_{}R'.format(n_samples),})
    # change 馬の最高賞金追加
    def max_money(self, horse_id_list, date, n_samples='all'):
        self.horse_results.reindex(horse_id_list, axis=1)
        target_df = self.horse_results.query('index in @horse_id_list')
        
        #過去何走分取り出すか指定
        if n_samples == 'all':
            filtered_df = target_df[target_df['date'] < date]
        elif n_samples > 0:
            filtered_df = target_df[target_df['date'] < date].sort_values('date', ascending=False).groupby(level=0).head(n_samples)
        else:
            raise Exception('n_samples must be >0')
            
        max_money = filtered_df.groupby(level=0)[['賞金']].max()
        return max_money.rename(columns={'賞金':'最高賞金_{}R'.format(n_samples)})

    def sum_money(self, horse_id_list, date, n_samples='all'):
        self.horse_results.reindex(horse_id_list, axis=1)
        target_df = self.horse_results.query('index in @horse_id_list')
        
        #過去何走分取り出すか指定
        if n_samples == 'all':
            filtered_df = target_df[target_df['date'] < date]
        elif n_samples > 0:
            filtered_df = target_df[target_df['date'] < date].sort_values('date', ascending=False).groupby(level=0).head(n_samples)
        else:
            raise Exception('n_samples must be >0')
            
        sum_money = filtered_df.groupby(level=0)[['賞金']].sum()
        return sum_money.rename(columns={'賞金':'合計賞金_{}R'.format(n_samples)})

    def merge(self, results, date, n_samples='all'):
        df = results[results['date']==date]
        horse_id_list = df['horse_id']
        merged_df = df.merge(self.average(horse_id_list, date, 3), left_on='horse_id',right_index=True, how='left')\
                      .merge(self.average(horse_id_list, date, 5), left_on='horse_id',right_index=True, how='left')\
                      .merge(self.average(horse_id_list, date, 7), left_on='horse_id',right_index=True, how='left')\
                      .merge(self.average(horse_id_list, date, "all"), left_on='horse_id',right_index=True, how='left')\
                      .merge(self.max_money(horse_id_list, date, 3), left_on='horse_id',right_index=True, how='left')\
                      .merge(self.max_money(horse_id_list, date, 5), left_on='horse_id',right_index=True, how='left')\
                      .merge(self.max_money(horse_id_list, date, 7), left_on='horse_id',right_index=True, how='left')\
                      .merge(self.max_money(horse_id_list, date, 'all'), left_on='horse_id',right_index=True, how='left')\
                      .merge(self.sum_money(horse_id_list, date, 3), left_on='horse_id',right_index=True, how='left')\
                      .merge(self.sum_money(horse_id_list, date, 5), left_on='horse_id',right_index=True, how='left')\
                      .merge(self.sum_money(horse_id_list, date, 7), left_on='horse_id',right_index=True, how='left')\
                      .merge(self.sum_money(horse_id_list, date, 'all'), left_on='horse_id',right_index=True, how='left')
        return merged_df

    def merge_all(self, results, n_samples='all'):
        date_list = results['date'].unique()
        merged_df = pd.concat([self.merge(results, date, n_samples) for date in date_list])
        return merged_df

def scrape_peds(horse_id_list, pre_peds={}):
    peds = pre_peds
    for horse_id in horse_id_list:
        if horse_id in peds.keys():
            continue
        try:
            url = "https://db.netkeiba.com/horse/ped/" + horse_id
            df = read_html(url,0)

            generations = {}
            for i in reversed(range(5)):
                generations[i] = df[i]
                df.drop([i], axis=1, inplace=True)
                df = df.drop_duplicates()

            ped = pd.concat([generations[i] for i in range(5)]).rename(horse_id)
            peds[horse_id] = ped.reset_index(drop=True)
            time.sleep(0.1)
        except IndexError:
            continue
        except Exception as e:
            print(e)
            break
    return peds

def process_categorical(df, target_columns):
    df2 = df.copy()
    for column in target_columns:
        df2[column] = LabelEncoder().fit_transform(df2[column].fillna('Na'))
    
    #target_columns以外にカテゴリ変数があれば、ダミー変数にする
    df2 = pd.get_dummies(df2)

    for column in target_columns:
        df2[column] = df2[column].astype('category')

    return df2

def add_blood_data(horse_id_list,df):
    peds = scrape_peds(horse_id_list)
    peds = pd.concat([peds[horse_id] for horse_id in peds], axis=1).T
    peds = peds.add_prefix('peds_')
    df = df.merge(peds,left_on='horse_id', right_index=True, how='left')
    return df

def scrape_jockey_results(jockey_id_list, pre_jockey_id=[]):
    jockey_results = {}
    jockey_results_all = {}
    for jockey_id in jockey_id_list:
        if jockey_id in pre_jockey_id:
            continue
        try:
            url = 'https://db.netkeiba.com/jockey/result/' + jockey_id + '/'
            df = read_html(url,0)
            df_all = read_html(url,0)[['勝率','連対率','複勝率']][:1]
            jockey_results[jockey_id] = df
            jockey_results_all[jockey_id] = df_all
            time.sleep(0.1)
        except IndexError:
            print("IndexError",jockey_id)
            continue
        except ValueError:
            print("ValueError",jockey_id)
            continue
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(e)
            break
        except:
            break
    return jockey_results,jockey_results_all

def before_race(df):
    if df['馬体重(増減)'].isnull().any() == True:
        race_results = pd.read_pickle('../pickle_data/Preprocessing/LGBM.pickle')
        horse_id_list = list(df['horse_id'])
        tmp = []

        for horse_id in horse_id_list:
            average_weight = race_results[race_results['horse_id'] == horse_id]['体重'].mean()
            average_weight_change = race_results[race_results['horse_id'] == horse_id]['体重変化'].mean()
            
            tmp.append(str(int(average_weight))+'('+str(int(average_weight_change))+')')
            
        df['馬体重(増減)'] = tmp
        
        return df
        
    else:
        return df

def preprocessing_predict(df):
    df = before_race(df)
    df.loc[df['馬体重(増減)'] == '--','馬体重(増減)'] = "0(0)"
    df['性'] = df['性齢'].map(lambda x:str(x)[0])
    df['年齢'] = df['性齢'].map(lambda x:str(x)[1:]).astype(int)
    df['体重'] = df['馬体重(増減)'].str.split('(',expand = True)[0].astype(int)
    df['体重変化'] = df['馬体重(増減)'].str.split('(',expand = True)[1].str[:-1]
    df.loc[df['体重変化'] == "前計不", '体重変化'] = 0
    object_to_int = [int(s) for s in list(df['体重変化'])]
    df['体重変化'] = object_to_int
    df['枠'] = df['枠'].astype(int)
    df['馬番'] = df['馬番'].astype(int)
    df['斤量'] = df['斤量'].astype(float)
    df['斤量'] = df['斤量'].astype(int)
    df['厩舎'] = df['厩舎'].map(lambda x:str(x)[:2])
    
    horse_name = df["馬名"]
    jockey_name = df[['騎手', 'jockey_id']]
    
    df.drop(['性齢','馬体重(増減)'],axis = 1,inplace = True)
    
    
    df.drop(['horse_id'],axis=1,inplace=True)
    df.drop(['jockey_id'],axis=1,inplace=True)
    df.drop(['騎手'],axis=1,inplace=True)
    df.drop(['date'],axis=1,inplace=True)
    df.drop(['Blood_f_id'],axis=1,inplace=True) 
    df.drop(['Blood_ff_id'],axis=1,inplace=True) 
    df.drop(['Blood_mf_id'],axis=1,inplace=True)
    df.drop(['評価'],axis=1,inplace=True)
    
    df['厩舎'] = df['厩舎'].map({'栗東':0, '美浦':1, '地方':2, '海外':3, '不明':4})
    df['class'] = df['class'].map({'新馬':0, '未勝利':0, '1勝':1, '2勝':2, '3勝':3, 'オープン':4})
    df['性'] = df['性'].map({'牡':0, '牝':1, 'セ':2})
    df['ground_state'] = df['ground_state'].map({'良':0, '稍':1, '重':2, '不':3})
    df['race_type'] = df['race_type'].map({'芝':0, 'ダート':1})
    df['weather'] = df['weather'].map({'晴':0, '曇':1, '小雨':2, '雨':3, '小雪':4, '雪':5})
    df['course_type'] = df['course_type'].map({'右':0, '左':1, '直線':2})
    df['評価ランク'] = df['評価ランク'].map({'A':0, 'B':1, 'C':2, 'D':3})
    
    df = df.rename(columns=lambda s: s.replace(" ",""))
    
    #df = Categorical(df)

    return df,horse_name,jockey_name

def Categorical(predict_data):
    Base_Data = pd.read_pickle('../pickle_data/Base_Data.pickle')    

    sex = Base_Data['性'].unique()
    Class = Base_Data['class'].unique()
    shozoku = Base_Data['厩舎'].unique()
        
    predict_data['weather'] = pd.Categorical(predict_data['weather'],["曇", "晴", "雨", "小雨", "小雪", "雪"])
    predict_data['ground_state'] = pd.Categorical(predict_data['ground_state'],["良", "重", "稍", "不"])
    predict_data['course_type'] = pd.Categorical(predict_data['course_type'],["右","左","直線"])
    predict_data['性'] = pd.Categorical(predict_data['性'],sex)
    predict_data['race_type'] = pd.Categorical(predict_data['race_type'],["芝","ダート"])
    predict_data['class'] = pd.Categorical(predict_data['class'],Class)
    predict_data['厩舎'] = pd.Categorical(predict_data['厩舎'],shozoku)
    
    #predict_data['評価ランク'] = predict_data['評価ランク'].astype('category')
    #predict_data['評価'] = predict_data['評価'].astype('category')
    
    #predict_data = merge_hyouka(predict_data)
    
    #predict_data.drop(['評価ランク'],axis=1,inplace=True)
    predict_data.drop(['評価'],axis=1,inplace=True)
    
    
    #predict_data = pd.get_dummies(predict_data,columns=['course_type','weather','race_type','ground_state','性','class','厩舎'])
    
    return predict_data

def merge_hyouka(predict_data):
    tyoukyou_rank = pd.read_pickle('../pickle_data/tyoukyou_rank.pickle')
    tyoukyou = pd.read_pickle('../pickle_data/tyoukyou.pickle')
    
    pre_hyouka_rank = list(predict_data['評価ランク'])
    pre_hyouka = list(predict_data['評価'])
    
    tmp_rank = []
    tmp = []
    for rank in pre_hyouka_rank:
        tmp_rank.append(str(tyoukyou_rank[tyoukyou_rank['評価ランク'] == rank]['評価ランク_label']))
        
    for text in pre_hyouka:
        tmp.append(str(tyoukyou[tyoukyou['評価'] == text]['評価_label']))
        
    predict_data['評価ランク_label'] = tmp_rank
    predict_data['評価_label'] = tmp
    
    predict_data['評価ランク_label'] = predict_data['評価ランク_label'].astype('category')
    predict_data['評価_label'] = predict_data['評価_label'].astype('category')
    
    return predict_data

    

def diff_date(df,horse_results):
    date = df['date'].unique()[0]
    horse_results['date'] = pd.to_datetime(horse_results['日付'])
    horse_results = horse_results[horse_results['date'] < date]
    df['レース間隔'] = list((date - horse_results.groupby(level=0).head(1)['date'])/timedelta(days=1))
        
    return df

def preprocess_race_predict(df):
    preprocess_df,horse_name,jockey_name = preprocessing_predict(df)
    target_columns = []
    for i in range(62):
        target_columns.append('peds_'+str(i))
    preprocess_df = process_categorical(preprocess_df, target_columns)
    return preprocess_df,horse_name,jockey_name

def compare_df(df):
    df_predict = df.copy()

    df_train = pd.read_pickle('../pickle_data/Train/train_data.pickle')
    horse_count = len(df_predict)
    t_column = set(list(df_train.columns.values))
    p_column = set(list(df_predict.columns.values))

    drop_list = list(p_column - t_column)
    add_list = list(t_column - p_column)

    for drop in drop_list:
        df_predict.drop([drop],axis=1,inplace=True)

    for add in add_list:
        df_predict[add] = [0]*horse_count
            
    return df_predict

def joint_horse_data(df_now,df_past):
    day_list = list(df_now['日付'])
    id_list = list(df_now['日付'].index)
    tmp = []
    for i in range(len(day_list)):
        tmp.append(day_list[i]+id_list[i])
    df_now['年度id'] = tmp
    
    now = list(df_now['年度id'])
    
    day_list = list(df_past['日付'])
    id_list = list(df_past['日付'].index)
    tmp = []
    for i in range(len(day_list)):
        tmp.append(day_list[i]+id_list[i])
    df_past['年度id'] = tmp
    
    past = list(df_past['年度id'])
    
    tmp = [0]*len(now)
    for i in range(len(now)):
        flag = False
        for j in range(len(past)):
            if now[i] == past[j]:
                tmp[i] = float(df_past.iloc[j]['偏差値'])
                flag = True
        if flag == False:
            tmp[i] = 50
                
    #df_now = df_now.merge(df_past['偏差値'],left_on='年度id',right_on='年度id',how='inner')
    df_now['偏差値'] = tmp
    
    return df_now


class JockeyResults:
    def __init__(self, jockey_results):
        self.jockey_results = jockey_results
        self.preprocessing()

    def preprocessing(self):
        df = self.jockey_results.copy()
        df = df[df[('年度','年度')] != '累計']
        idx = list(df.index)
        year = list(df['年度']['年度'])
        tmp = []
        for i in range(len(idx)):
            tmp.append(str(idx[i])+str(year[i]))
        df['年度id'] = tmp
        df['年度合計出走'] = df[['1着','2着','3着','着外']].sum(axis=1)
        df['年度馬券圏内'] = df[['1着','2着','3着']].sum(axis=1)
        df['年度勝利'] = df[['1着']].sum(axis=1)
        
        df[('年度','年度')] = df[('年度','年度')].astype(int)
        self.jockey_results = df

    def average_jyusho(self, jockey_id_list, year, n_samples='all'):
        #self.jockey_results.reindex(jockey_id_list, axis=1)
        target_df = self.jockey_results.loc[jockey_id_list]
        #target_df = self.jockey_results[jockey_results['年度id']==jockey_id_list]
        #target_df = self.jockey_results.query('index in @jockey_id_list')

        #過去何走分取り出すか指定
        if n_samples == 'all':
            filtered_df = target_df[target_df[('年度','年度')] < year]
        elif n_samples > 0:
            filtered_df = target_df[target_df[('年度','年度')] < year].sort_values(('年度','年度'), ascending=False).groupby(level=0).head(n_samples)
        else:
            raise Exception('n_samples must be >0')

        #average = filtered_df.groupby(level=0)[['着順', '賞金', '上り','first_corner','final_corner','final_to_rank','first_to_rank','first_to_final']].mean()
        average = filtered_df.groupby(level=0).sum()[('重賞','勝利')]/filtered_df.groupby(level=0).sum()[('重賞','出走')]
        return pd.DataFrame(average).rename(columns={0:'平均重賞勝利確率_{}Y'.format(n_samples)})
        #return average.rename(columns={'着順':'平均着順_{}R'.format(n_samples)})
        
    def average_tokubetu(self, jockey_id_list, year, n_samples='all'):
        #self.jockey_results.reindex(jockey_id_list, axis=1)
        target_df = self.jockey_results.loc[jockey_id_list]
        #target_df = self.jockey_results.query('index in @jockey_id_list')

        #過去何走分取り出すか指定
        if n_samples == 'all':
            filtered_df = target_df[target_df[('年度','年度')] < year]
        elif n_samples > 0:
            filtered_df = target_df[target_df[('年度','年度')] < year].sort_values(('年度','年度'), ascending=False).groupby(level=0).head(n_samples)
        else:
            raise Exception('n_samples must be >0')

        #average = filtered_df.groupby(level=0)[['着順', '賞金', '上り','first_corner','final_corner','final_to_rank','first_to_rank','first_to_final']].mean()
        average = filtered_df.groupby(level=0).sum()[('特別','勝利')]/filtered_df.groupby(level=0).sum()[('特別','出走')]
        return pd.DataFrame(average).rename(columns={0:'平均特別勝利確率_{}Y'.format(n_samples)})
    
    def average_hiraba(self, jockey_id_list, year, n_samples='all'):
        #self.jockey_results.reindex(jockey_id_list, axis=1)
        target_df = self.jockey_results.loc[jockey_id_list]
        #target_df = self.jockey_results.query('index in @jockey_id_list')

        #過去何走分取り出すか指定
        if n_samples == 'all':
            filtered_df = target_df[target_df[('年度','年度')] < year]
        elif n_samples > 0:
            filtered_df = target_df[target_df[('年度','年度')] < year].sort_values(('年度','年度'), ascending=False).groupby(level=0).head(n_samples)
        else:
            raise Exception('n_samples must be >0')

        #average = filtered_df.groupby(level=0)[['着順', '賞金', '上り','first_corner','final_corner','final_to_rank','first_to_rank','first_to_final']].mean()
        average = filtered_df.groupby(level=0).sum()[('平場','勝利')]/filtered_df.groupby(level=0).sum()[('平場','出走')]
        return pd.DataFrame(average).rename(columns={0:'平均平場勝利確率_{}Y'.format(n_samples)})
    
    def average_turf(self, jockey_id_list, year, n_samples='all'):
        #self.jockey_results.reindex(jockey_id_list, axis=1)
        target_df = self.jockey_results.loc[jockey_id_list]
        #target_df = self.jockey_results.query('index in @jockey_id_list')

        #過去何走分取り出すか指定
        if n_samples == 'all':
            filtered_df = target_df[target_df[('年度','年度')] < year]
        elif n_samples > 0:
            filtered_df = target_df[target_df[('年度','年度')] < year].sort_values(('年度','年度'), ascending=False).groupby(level=0).head(n_samples)
        else:
            raise Exception('n_samples must be >0')

        #average = filtered_df.groupby(level=0)[['着順', '賞金', '上り','first_corner','final_corner','final_to_rank','first_to_rank','first_to_final']].mean()
        average = filtered_df.groupby(level=0).sum()[('芝','勝利')]/filtered_df.groupby(level=0).sum()[('芝','出走')]
        return pd.DataFrame(average).rename(columns={0:'平均芝勝利確率_{}Y'.format(n_samples)})
    
    def average_durt(self, jockey_id_list, year, n_samples='all'):
        #self.jockey_results.reindex(jockey_id_list, axis=1)
        target_df = self.jockey_results.loc[jockey_id_list]
        #target_df = self.jockey_results.query('index in @jockey_id_list')

        #過去何走分取り出すか指定
        if n_samples == 'all':
            filtered_df = target_df[target_df[('年度','年度')] < year]
        elif n_samples > 0:
            filtered_df = target_df[target_df[('年度','年度')] < year].sort_values(('年度','年度'), ascending=False).groupby(level=0).head(n_samples)
        else:
            raise Exception('n_samples must be >0')

        #average = filtered_df.groupby(level=0)[['着順', '賞金', '上り','first_corner','final_corner','final_to_rank','first_to_rank','first_to_final']].mean()
        average = filtered_df.groupby(level=0).sum()[('ダート','勝利')]/filtered_df.groupby(level=0).sum()[('ダート','出走')]
        return pd.DataFrame(average).rename(columns={0:'平均ダート勝利確率_{}Y'.format(n_samples)})
    
    def average_win1(self, jockey_id_list, year, n_samples='all'):
        #self.jockey_results.reindex(jockey_id_list, axis=1)
        target_df = self.jockey_results.loc[jockey_id_list]
        #target_df = self.jockey_results.query('index in @jockey_id_list')

        #過去何走分取り出すか指定
        if n_samples == 'all':
            filtered_df = target_df[target_df[('年度','年度')] < year]
        elif n_samples > 0:
            filtered_df = target_df[target_df[('年度','年度')] < year].sort_values(('年度','年度'), ascending=False).groupby(level=0).head(n_samples)
        else:
            raise Exception('n_samples must be >0')

        #average = filtered_df.groupby(level=0)[['着順', '賞金', '上り','first_corner','final_corner','final_to_rank','first_to_rank','first_to_final']].mean()
        
        #tmp = filtered_df.groupby(level=0).sum().merge(pd.DataFrame(filtered_df.groupby(level=0).sum()[['1着','2着','3着','着外']].sum(axis=1)), left_index=True,right_index=True, how='left')
        #average = tmp[('1着','1着')]/tmp[0]
        average = filtered_df.groupby(level=0).sum()#['年度合計出走']/filtered_df.groupby(level=0).sum()['年度馬券圏内']
        average['平均勝利'] = average['年度勝利']/average['年度合計出走']
        
        #return pd.DataFrame(average).rename(columns={0:'平均勝利確率_{}Y'.format(n_samples)})
        return pd.DataFrame(average['平均勝利']).rename(columns={'平均勝利':'平均勝利確率_{}Y'.format(n_samples)})
    
    def average_win3(self, jockey_id_list, year, n_samples='all'):
        #self.jockey_results.reindex(jockey_id_list, axis=1)
        target_df = self.jockey_results.loc[jockey_id_list]
        #target_df = self.jockey_results.query('index in @jockey_id_list')

        #過去何走分取り出すか指定
        if n_samples == 'all':
            filtered_df = target_df[target_df[('年度','年度')] < year]
        elif n_samples > 0:
            filtered_df = target_df[target_df[('年度','年度')] < year].sort_values(('年度','年度'), ascending=False).groupby(level=0).head(n_samples)
        else:
            raise Exception('n_samples must be >0')

        #average = filtered_df.groupby(level=0)[['着順', '賞金', '上り','first_corner','final_corner','final_to_rank','first_to_rank','first_to_final']].mean()
        #tmp = filtered_df.groupby(level=0).sum().merge(pd.DataFrame(filtered_df.groupby(level=0).sum()[['1着','2着','3着','着外']].sum(axis=1)), left_index=True,right_index=True, how='left')
        #average = tmp[('1着','1着')]/tmp[0] + tmp[('2着','2着')]/tmp[0] + tmp[('3着','3着')]/tmp[0]
        #return pd.DataFrame(average).rename(columns={0:'平均複勝確率_{}Y'.format(n_samples)})
        
        average = filtered_df.groupby(level=0).sum()#['年度合計出走']/filtered_df.groupby(level=0).sum()['年度馬券圏内']
        average['平均複勝'] = average['年度馬券圏内']/average['年度合計出走']
        return pd.DataFrame(average['平均複勝']).rename(columns={'平均複勝':'平均複勝確率_{}Y'.format(n_samples)})


    def merge(self, results, year, n_samples='all'):
        df = results[results['round_year']==year]
        jockey_id_list = list(df['jockey_id'].unique())
        
        df = df.merge(self.average_jyusho(jockey_id_list, year, 2), left_on='jockey_id',right_index=True, how='left')
        df = df.merge(self.average_tokubetu(jockey_id_list, year, 2), left_on='jockey_id',right_index=True, how='left')
        df = df.merge(self.average_hiraba(jockey_id_list, year, 2), left_on='jockey_id',right_index=True, how='left')
        df = df.merge(self.average_turf(jockey_id_list, year, 2), left_on='jockey_id',right_index=True, how='left')
        df = df.merge(self.average_durt(jockey_id_list, year, 2), left_on='jockey_id',right_index=True, how='left')
        df = df.merge(self.average_win1(jockey_id_list, year, 2), left_on='jockey_id',right_index=True, how='left')
        df = df.merge(self.average_win3(jockey_id_list, year, 2), left_on='jockey_id',right_index=True, how='left')
        
        return df

    def merge_all(self, results, n_samples='all'):
        year_list = results['round_year'].unique()
        merged_df = pd.concat([self.merge(results, year, n_samples) for year in year_list])
        return merged_df

def predict(race_id_list,day):

    race_tables,race_infos = scrape_race_predict(race_id_list,day)
    
    for key in race_tables:
        race_tables[key].index = [key] * len(race_tables[key])
    race_tables = pd.concat([race_tables[key] for key in race_tables], sort=False)
    
    #race_tables = race_tables[race_tables['馬番'] != 1]
    #race_tables = race_tables[race_tables['馬番'] != 2]
    #race_tables = race_tables[race_tables['馬番'] != 3]
    #race_tables = race_tables[race_tables['馬番'] != 4]
    #race_tables = race_tables[race_tables['馬番'] != 5]
    #race_tables = race_tables[race_tables['馬番'] != 6]
    #race_tables = race_tables[race_tables['馬番'] != 7]
    #race_tables = race_tables[race_tables['馬番'] != 8]
    #race_tables = race_tables[race_tables['馬番'] != 9]
    #race_tables = race_tables[race_tables['馬番'] != 10]
    #race_tables = race_tables[race_tables['馬番'] != 11]
    #race_tables = race_tables[race_tables['馬番'] != 12]
    #race_tables = race_tables[race_tables['馬番'] != 13]
    #race_tables = race_tables[race_tables['馬番'] != 14]
    #race_tables = race_tables[race_tables['馬番'] != 15]
    #race_tables = race_tables[race_tables['馬番'] != 16]
    #race_tables = race_tables[race_tables['馬番'] != 17]
    #race_tables = race_tables[race_tables['馬番'] != 18]
    
    df_infos = pd.DataFrame(race_infos.values(), index=race_infos.keys())
    predict_addinfo = race_tables.merge(df_infos,left_index=True,right_index=True,how='inner')
    predict_addinfo['date'] = pd.to_datetime(predict_addinfo['date'],format='%Y年%m月%d日')
    predict_addinfo['round_year'] = predict_addinfo.index.map(lambda x: int(x[0:4]))
    predict_addinfo['course_id'] = predict_addinfo.index.map(lambda x: int(x[4:6]))
    predict_addinfo['round_count'] = predict_addinfo.index.map(lambda x: int(x[6:8]))
    predict_addinfo['round_day'] = predict_addinfo.index.map(lambda x: int(x[8:10]))
    predict_addinfo['round'] = predict_addinfo.index.map(lambda x: int(x[10:12]))
    
    print("チェック1")
    
    horse_id_list = predict_addinfo['horse_id'].unique()
    horse_results = scrape_horse_results(horse_id_list)
    for key in horse_results:
        horse_results[key].index = [key] * len(horse_results[key])
    df_horse_results = pd.concat([horse_results[key] for key in horse_results])
    
    print("チェック2")
    
    peds_id_df = df_horse_results[['Blood_f_id','Blood_ff_id','Blood_mf_id']]
    grouped = peds_id_df.groupby(level=0)  
    df2 = grouped.last() 
    predict_addinfo = predict_addinfo.merge(df2,left_on='horse_id', right_index=True, how='left')
    
    print("チェック3")
    
    df_horse_results = df_horse_results.rename(columns=lambda s: s.replace(" ",""))
    hr = HorseResults(df_horse_results)
    predict_data = hr.merge_all(predict_addinfo, n_samples=5)
    predict_data = diff_date(predict_data,df_horse_results)
    
    print("チェック4")
    
    peds_data = pd.read_pickle('../pickle_data/preprocessing/peds_data_category.pickle')
    peds_results = pd.read_pickle('../pickle_data/Scraping/peds_results.pickle')
    jockey_results = pd.read_pickle('../pickle_data/Scraping/jockey_results.pickle')
    
    print("チェック5")
    
    predict_data = predict_data.merge(peds_results.add_prefix('f_'),left_on='Blood_f_id', right_index=True, how='left')
    predict_data = predict_data.merge(peds_results.add_prefix('ff_'),left_on='Blood_ff_id', right_index=True, how='left')
    predict_data = predict_data.merge(peds_results.add_prefix('mf_'),left_on='Blood_mf_id', right_index=True, how='left')
    
    print("チェック6")
   
    
    jr = JockeyResults(jockey_results)
    predict_data = jr.merge_all(predict_data, n_samples=5)
    
    
    predict_data = predict_data.merge(peds_data,left_on='horse_id', right_on='horse_id', how='left')
    predict_data, horse_name, jockey_name = preprocessing_predict(predict_data)
    
    duplicate = (predict_data.duplicated(keep='first'))
    predict_data = predict_data[~duplicate]

    
    
    return predict_data,horse_name,jockey_name

def Deviation_value(test_data):
    import math
    mean = sum(test_data) / len(test_data)
    dev_data = []

    for dev in test_data:
        dev_data.append((dev - mean) ** 2)
    dispersion_data = sum(dev_data) / len(dev_data)
    result_sd = math.sqrt(dispersion_data)
    dispersion_value = []

    for t in test_data:
        dispersion_value.append(int(10 * ((t - mean) / result_sd) + 50))

    return dispersion_value


def round_dev(df,race_id,day,race_type):
    df.index = [race_id]*len(df)

    day = datetime.datetime.strptime(day[0], '%Y年%m月%d日')
    
    if race_type == '芝':
        df_all = pd.read_pickle('../DataBase/Turf/DataBase_all.pickle')
    else:
        df_all = pd.read_pickle('../DataBase/Dirt/DataBase_all.pickle')
        
    df_all = df_all[df_all['date'] < day]
    columns = []
    columns += ['予想着順','馬名','round','1着率','2着率','3着率','その他']
    df_all = df_all[columns]
    df_Copy = df.copy()
    df_Copy = df_Copy[columns]
    DataBase = df_all.append(df)
    
    calcu = lambda x: ((x - x.mean())/x.std())*10 + 60
    calcu1 = lambda x: ((x - x.mean())/x.std())*10 + 25
    calcu2 = lambda x: ((x - x.mean())/x.std())*10 + 15
    calcu3 = lambda x: ((x - x.mean())/x.std())*10
    
    calcu4 = lambda x: -((x - x.mean())/x.std())*10 + 50
    DataBase['期待値'] = (DataBase['1着率']*1 + DataBase['2着率']*2 + DataBase['3着率']*3 + DataBase['その他']*4).round(3)
    DataBase['期待値_ROUND'] = DataBase.groupby('round')['期待値'].transform(calcu4).round(3)

    DataBase['1着率_偏差値_ROUND'] = DataBase.groupby('round')['1着率'].transform(calcu).round(3)
    DataBase['2着率_偏差値_ROUND'] = DataBase.groupby('round')['2着率'].transform(calcu1).round(3)
    DataBase['3着率_偏差値_ROUND'] = DataBase.groupby('round')['3着率'].transform(calcu2).round(3)
    DataBase['その他_偏差値_ROUND'] = DataBase.groupby('round')['その他'].transform(calcu3).round(3)
    DataBase['合計_偏差値_ROUND'] = DataBase['1着率_偏差値_ROUND'] + DataBase['2着率_偏差値_ROUND'] + DataBase['3着率_偏差値_ROUND']
    
    DataBase = DataBase[DataBase.index == race_id]
    duplicate = (DataBase.duplicated(keep='first'))
    DataBase = DataBase[~duplicate]
        
    df['1着率_偏差値_ROUND'] = list(DataBase['1着率_偏差値_ROUND'])
    df['2着率_偏差値_ROUND'] = list(DataBase['2着率_偏差値_ROUND'])
    df['3着率_偏差値_ROUND'] = list(DataBase['3着率_偏差値_ROUND'])
    df['その他_偏差値_ROUND'] = list(DataBase['その他_偏差値_ROUND'])
    df['合計_偏差値_ROUND'] = list(DataBase['合計_偏差値_ROUND'])
    
    df['期待値_ROUND'] = list(DataBase['期待値_ROUND'])
    
    return df

def class_dev(df,race_id,day,race_type):
    df.index = [race_id]*len(df)
    day = datetime.datetime.strptime(day[0], '%Y年%m月%d日')
    
    if race_type == '芝':
        df_all = pd.read_pickle('../DataBase/Turf/DataBase_all.pickle')
    else:
        df_all = pd.read_pickle('../DataBase/Dirt/DataBase_all.pickle')
        
    df_all = df_all[df_all['date'] < day]
    columns = []
    columns += ['予想着順','馬名','階級','1着率','2着率','3着率','その他']
    df_all = df_all[columns]
    df_Copy = df.copy()
    df_Copy = df_Copy[columns]
    DataBase = df_all.append(df)
    
    calcu = lambda x: ((x - x.mean())/x.std())*10 + 60
    calcu1 = lambda x: ((x - x.mean())/x.std())*10 + 25
    calcu2 = lambda x: ((x - x.mean())/x.std())*10 + 15
    calcu3 = lambda x: ((x - x.mean())/x.std())*10
    
    calcu4 = lambda x: -((x - x.mean())/x.std())*10 + 50
    DataBase['期待値'] = (DataBase['1着率']*1 + DataBase['2着率']*2 + DataBase['3着率']*3 + DataBase['その他']*4).round(3)
    DataBase['期待値_CLASS'] = DataBase.groupby('階級')['期待値'].transform(calcu4).round(3)

    DataBase['1着率_偏差値_CLASS'] = DataBase.groupby('階級')['1着率'].transform(calcu).round(3)
    DataBase['2着率_偏差値_CLASS'] = DataBase.groupby('階級')['2着率'].transform(calcu1).round(3)
    DataBase['3着率_偏差値_CLASS'] = DataBase.groupby('階級')['3着率'].transform(calcu2).round(3)
    DataBase['その他_偏差値_CLASS'] = DataBase.groupby('階級')['その他'].transform(calcu3).round(3)
    DataBase['合計_偏差値_CLASS'] = DataBase['1着率_偏差値_CLASS'] + DataBase['2着率_偏差値_CLASS'] + DataBase['3着率_偏差値_CLASS']
    
    
    DataBase = DataBase[DataBase.index == race_id]
    duplicate = (DataBase.duplicated(keep='first'))
    DataBase = DataBase[~duplicate]
    
    df['1着率_偏差値_CLASS'] = list(DataBase['1着率_偏差値_CLASS'])
    df['2着率_偏差値_CLASS'] = list(DataBase['2着率_偏差値_CLASS'])
    df['3着率_偏差値_CLASS'] = list(DataBase['3着率_偏差値_CLASS'])
    df['その他_偏差値_CLASS'] = list(DataBase['その他_偏差値_CLASS'])
    df['合計_偏差値_CLASS'] = list(DataBase['合計_偏差値_CLASS'])
    
    df['期待値_CLASS'] = list(DataBase['期待値_CLASS'])
    
    return df

def pickle_dump(obj, path):
    with open(path, mode='wb') as f:
        pickle.dump(obj,f)

def pickle_load(path):
    with open(path, mode='rb') as f:
        data = pickle.load(f)
        return data

def columns_change(df):
    columns = pickle_load('columns.pickle')
    df = df[columns]
    return df
    
def columns_change_j(df):
    columns = pickle_load('columns_j.pickle')
    df = df[columns]
    return df

def scale(x):
    res = (x - np.mean(x)) / np.std(x, ddof=1)
    if np.std(x, ddof=1) == 0:
        res = 0
    
    return res


def standrad(df):
    columns = pd.read_pickle('../pickle_data/columns.pickle')
    for column in columns:
        #df['標準化_'+column] = df.groupby(level=0)[column].transform(scale)
        #df['標準化_'+column] = df[column].transform(scale)
        df['標準化_'+column] = df[column].apply(lambda x: (x - np.mean(x)) / np.std(x))
    df.drop(columns,axis=1,inplace=True)
        
    return df


def predict_send(predict_data,horse_name,place_dict,race_id_list,place,jockey_name,day):
    
    tmp_data = predict_data.copy()
    predict_data.to_csv('../race_result_place/ponyo/test.csv')
    predict_data.drop(['馬名'],axis=1,inplace=True)
    predict_data_j = predict_data.copy()
    
    place = int(predict_data['course_id'].unique())
    #predict_data = standrad(predict_data)
    predict_data = columns_change(predict_data)
    predict_data_j = columns_change_j(predict_data_j)
    
    len_case = predict_data['course_len'].map(lambda x: "S" if x < 1301 else ('M' if x < 1900 else ('I' if x < 2101 else ('L' if x < 2701 else 'E')))).unique()[0]
    

    if predict_data['race_type'].unique() == 0:
        loaded_model = pickle.load(open('../train_data/standard/lightgbm_'+len_case+'_Turf.pickle', 'rb'))
        loaded_model_hukusho = pickle.load(open('../train_data/standard/lightgbm_' + '3_'+len_case + '_Turf.pickle', 'rb'))
        loaded_model_rentai = pickle.load(open('../train_data/standard/lightgbm_' + '2_'+len_case + '_Turf.pickle', 'rb'))
        loaded_model_kati = pickle.load(open('../train_data/standard/lightgbm_' + '1_' +len_case +'_Turf.pickle', 'rb'))
        
        loaded_model_j = pickle.load(open('../train_data/add_jockey/lightgbm_'+len_case+'_Turf.pickle', 'rb'))
        loaded_model_hukusho_j = pickle.load(open('../train_data/add_jockey/lightgbm_' + '3_'+len_case + '_Turf.pickle', 'rb'))
        loaded_model_rentai_j = pickle.load(open('../train_data/add_jockey/lightgbm_' + '2_'+len_case + '_Turf.pickle', 'rb'))
        loaded_model_kati_j = pickle.load(open('../train_data/add_jockey/lightgbm_' + '1_' +len_case +'_Turf.pickle', 'rb'))
        race_type = '芝'
    else:
        loaded_model = pickle.load(open('../train_data/standard/lightgbm_'+len_case+'_Dirt.pickle', 'rb'))
        loaded_model_hukusho = pickle.load(open('../train_data/standard/lightgbm_' + '3_' +len_case+ '_Dirt.pickle', 'rb'))
        loaded_model_rentai = pickle.load(open('../train_data/standard/lightgbm_' + '2_' +len_case+ '_Dirt.pickle', 'rb'))
        loaded_model_kati = pickle.load(open('../train_data/standard/lightgbm_' + '1_' +len_case+ '_Dirt.pickle', 'rb'))
        
        loaded_model_j = pickle.load(open('../train_data/add_jockey/lightgbm_'+len_case+'_Dirt.pickle', 'rb'))
        loaded_model_hukusho_j = pickle.load(open('../train_data/add_jockey/lightgbm_' + '3_' +len_case+ '_Dirt.pickle', 'rb'))
        loaded_model_rentai_j = pickle.load(open('../train_data/add_jockey/lightgbm_' + '2_' +len_case+ '_Dirt.pickle', 'rb'))
        loaded_model_kati_j = pickle.load(open('../train_data/add_jockey/lightgbm_' + '1_' +len_case+ '_Dirt.pickle', 'rb'))
        race_type = 'ダート'
        
    proba = loaded_model.predict_proba(predict_data)
    proba_hukusho = loaded_model_hukusho.predict_proba(predict_data)
    proba_rentai = loaded_model_rentai.predict_proba(predict_data)
    proba_kati = loaded_model_kati.predict_proba(predict_data)
    result = loaded_model.predict(predict_data)
    
    proba_j = loaded_model_j.predict_proba(predict_data_j)
    proba_hukusho_j = loaded_model_hukusho_j.predict_proba(predict_data_j)
    proba_rentai_j = loaded_model_rentai_j.predict_proba(predict_data_j)
    proba_kati_j = loaded_model_kati_j.predict_proba(predict_data_j)
    result_j = loaded_model_j.predict(predict_data_j)
    
    win1 = [r[0] for r in proba]
    win2 = [r[1] for r in proba]
    win3 = [r[2] for r in proba]
    #win4 = [r[3] for r in proba]
    hukusho = [r[1] for r in proba_hukusho]
    rentai = [r[1] for r in proba_rentai]
    kati = [r[1] for r in proba_kati]
    
    win1_j = [r[0] for r in proba_j]
    win2_j = [r[1] for r in proba_j]
    win3_j = [r[2] for r in proba_j]
    #win4 = [r[3] for r in proba]
    hukusho_j = [r[1] for r in proba_hukusho_j]
    rentai_j = [r[1] for r in proba_rentai_j]
    kati_j = [r[1] for r in proba_kati_j]
    
    df = tmp_data[['round','class']]
    
    df["馬名"] = tmp_data['馬名'].copy()
    df["予想着順"] = result
    df["1着率"] = win1
    df["2着率"] = win2
    df["3着率"] = win3
    
    df["予想着順_j"] = result_j
    df["1着率_j"] = win1_j
    df["2着率_j"] = win2_j
    df["3着率_j"] = win3_j
    #df["その他"] = win4
        
    df['1着率'] = df['1着率'].round(3)
    df['2着率'] = df['2着率'].round(3)
    df['3着率'] = df['3着率'].round(3)
    #df['その他'] = df['その他'].round(3)
    
    df['1着率_j'] = df['1着率_j'].round(3)
    df['2着率_j'] = df['2着率_j'].round(3)
    df['3着率_j'] = df['3着率_j'].round(3)
        
    calcu = lambda x: ((x - x.mean())/x.std())*10 + 60
    calcu1 = lambda x: ((x - x.mean())/x.std())*10 + 25
    calcu2 = lambda x: ((x - x.mean())/x.std())*10 + 15
    calcu3 = lambda x: ((x - x.mean())/x.std())*10
    calcu4 = lambda x: -((x - x.mean())/x.std())*10 + 50
    
    
    #df = round_dev(df,race_id_list[0],day,race_type)
    #df = class_dev(df,race_id_list[0],day,race_type)
    
    df["複勝率"] = hukusho
    df['複勝率'] = df['複勝率'].round(3)
    
    df["連対率"] = rentai
    df['連対率'] = (df['複勝率']*df['連対率']).round(3)
    
    df["勝率"] = kati
    df['勝率'] = (df['複勝率']*df['連対率']*df['勝率']).round(3)
    
    
    df["複勝率_j"] = hukusho_j
    df['複勝率_j'] = df['複勝率_j'].round(3)
    
    df["連対率_j"] = rentai_j
    df['連対率_j'] = (df['複勝率_j']*df['連対率_j']).round(3)
    
    df["勝率_j"] = kati_j
    df['勝率_j'] = (df['複勝率_j']*df['連対率_j']*df['勝率_j']).round(3)
    
    df['予測オッズ'] = 1/df['勝率']*0.8
    df['予測オッズ'] = df['予測オッズ'].round(3)

    
    df['1着率_偏差値_RACE'] = df['1着率'].transform(calcu).round(3)
    df['2着率_偏差値_RACE'] = df['2着率'].transform(calcu1).round(3)
    df['3着率_偏差値_RACE'] = df['3着率'].transform(calcu2).round(3)
    #df['その他_偏差値_RACE'] = df['その他'].transform(calcu3).round(3)
    df['複勝率_偏差値'] = df['複勝率'].transform(calcu).round(3)
    
    df['合計_偏差値_RACE'] = (df['1着率_偏差値_RACE'] + df['2着率_偏差値_RACE'] + df['3着率_偏差値_RACE']).round(0)
    #df['合計_偏差値_ROUND'] = (df['1着率_偏差値_ROUND'] + df['2着率_偏差値_ROUND'] + df['3着率_偏差値_ROUND']).round(0)
    #df['合計_偏差値_CLASS'] = (df['1着率_偏差値_CLASS'] + df['2着率_偏差値_CLASS'] + df['3着率_偏差値_CLASS']).round(0)
    df['期待値'] = (df['1着率']*1 + df['2着率']*2 + df['3着率']*3).round(3)
    df['期待値_RACE'] = df['期待値'].transform(calcu4).round(3)
    
    df.to_pickle('../race_result_place/ponyo/'+race_id_list[0]+'.pickle')
    
    #DataBase_hukusho_return = search_jockey_data(jockey_name,race_type)
        
    #DataBase_hukusho_return.to_pickle('../race_result_place/ponyo/jockey_'+race_id_list[0]+'.pickle')
    df.to_csv('../race_result_place/ponyo/'+race_id_list[0]+'.csv')


    place_name = place_dict[int(race_id_list[0][4:6])]
    round_name = race_id_list[0][-2:]
    
    
    return df

def Make_DataBase(df):
    df.index = [i for i in range(1,len(df)+1)]
    columns = ['馬名','予想着順','期待値','1着率','2着率','3着率','複勝率','連対率','勝率','1着率_j','2着率_j','3着率_j','複勝率_j','連対率_j','勝率_j']
    df = df[columns]

    return df


def search_jockey_data(jockey_name,race_type):
    if race_type == "芝":
        DataBase = pd.read_pickle('../DataBase/Turf/DataBase_all.pickle')
        DataBase_hukusho = DataBase[DataBase['着順']<4]
        DataBase_hukusho = DataBase_hukusho[['jockey_id','Tier1','Tier2','Tier3']]
        
        DataBase_hukusho = pd.concat([DataBase_hukusho.groupby('jockey_id').mean().add_prefix('平均_'), DataBase_hukusho.groupby('jockey_id').max().add_prefix('最大_'),DataBase_hukusho.groupby('jockey_id').min().add_prefix('最小_')], axis=1)
        DataBase_hukusho['平均_Tier1'] = DataBase_hukusho['平均_Tier1'].round(3)
        DataBase_hukusho['平均_Tier2'] = DataBase_hukusho['平均_Tier2'].round(3)
        DataBase_hukusho['平均_Tier3'] = DataBase_hukusho['平均_Tier3'].round(3)
        DataBase_hukusho_return = pd.merge(jockey_name, DataBase_hukusho, left_on='jockey_id', right_on='jockey_id')
        DataBase_hukusho_return.index = list(DataBase_hukusho_return['騎手'])
    else:
        DataBase = pd.read_pickle('../DataBase/Dirt/DataBase_all.pickle')
        DataBase_hukusho = DataBase[DataBase['着順']<4]
        DataBase_hukusho = DataBase_hukusho[['jockey_id','Tier1','Tier2','Tier3']]
        
        DataBase_hukusho = pd.concat([DataBase_hukusho.groupby('jockey_id').mean().add_prefix('平均_'), DataBase_hukusho.groupby('jockey_id').max().add_prefix('最大_'),DataBase_hukusho.groupby('jockey_id').min().add_prefix('最小_')], axis=1)
        DataBase_hukusho['平均_Tier1'] = DataBase_hukusho['平均_Tier1'].round(3)
        DataBase_hukusho['平均_Tier2'] = DataBase_hukusho['平均_Tier2'].round(3)
        DataBase_hukusho['平均_Tier3'] = DataBase_hukusho['平均_Tier3'].round(3)
        DataBase_hukusho_return = pd.merge(jockey_name, DataBase_hukusho, left_on='jockey_id', right_on='jockey_id')
        DataBase_hukusho_return.index = list(DataBase_hukusho_return['騎手'])
    
    return DataBase_hukusho_return

if __name__ == "__main__":
    # Parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--race_id', type=int, required=True, help='race_id.')
    args = parser.parse_args()
    race_id = str(args.race_id)

    year = str(datetime.datetime.now().year)
    month = str(datetime.datetime.now().month)
    date = str(datetime.datetime.now().day)
    dt_now = year+"年"+month+"月"+date+"日"

    place_dict = {1:"札幌",2:"函館",3:"福島",4:"新潟",5:"東京",6:"中山",7:"中京",8:"京都",9:"阪神",10:"小倉"}
    place = int(race_id[4:6])

    # デバッグの時だけファイルパスを変更する
    # 新しいディレクトリのパスを指定します。この例では、新しいディレクトリのパスは'/path/to/your/directory'です。
    new_directory = '/opt/mnt/App_ponyo'
    # ワーキングディレクトリを新しいディレクトリに変更します。
    os.chdir(new_directory)

    predict_data, horse_name, jockey_name = predict([race_id],[dt_now])
    df = predict_send(predict_data,horse_name,place_dict,[race_id],place,jockey_name,[dt_now])
    df = Make_DataBase(df)
    print("GOAL!!!!!!")
    print(df)