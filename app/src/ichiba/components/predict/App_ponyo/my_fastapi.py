from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import predict_race 
from typing import Any, Dict, List
import datetime

app = FastAPI()

# ヘルスチェック用のエンドポイント
@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# リクエストデータの構造を定義
class RequestData(BaseModel):
    race_id: str

# レスポンスデータの構造を定義
class ResponseData(BaseModel):
    prediction: List[Dict[str, Any]]

@app.post("/predict", response_model=ResponseData)
async def predict(request_data: RequestData):
    race_id = request_data.race_id

    year = str(datetime.datetime.now().year)
    month = str(datetime.datetime.now().month)
    date = str(datetime.datetime.now().day)
    dt_now = year+"年"+month+"月"+date+"日"

    place_dict = {1:"札幌",2:"函館",3:"福島",4:"新潟",5:"東京",6:"中山",7:"中京",8:"京都",9:"阪神",10:"小倉"}
    place = int(race_id[4:6])

    print("start preprocess")
    predict_data, horse_name, jockey_name = predict_race.predict([race_id],[dt_now])
    print("start predict")
    df = predict_race.predict_send(predict_data,horse_name,place_dict,[race_id],place,jockey_name,[dt_now])
    df = predict_race.Make_DataBase(df)
    print(df)

    return {"prediction": df.to_dict('records')}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)