import json

import requests
from braces.views import CsrfExemptMixin
from django.http import HttpResponse

from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
import pymongo
import datetime

import pandas as pd
import datetime
from sklearn.ensemble import RandomForestClassifier

db_address = "Your MongoDB Address"
FCM_Key= 'Your FCM_key'


class SensorView(CsrfExemptMixin, APIView):
    authentication_classes = []
    permission_classes =  [AllowAny]

    def post(self, request):
        client = pymongo.MongoClient(db_address)
        db = client.IoT_DB
        save_Sensor_DB = db.Sensor
        ML_DB = db.ML_DB
        test = json.loads(request.data)

        datetime_convert = datetime.datetime.strptime(test['cur_time'], '%Y-%m-%d %H:%M:%S')
        test['cur_time'] = datetime_convert.replace(microsecond=0)

        # 온도저장
        save_Sensor_DB.insert_one(test)

        new_dict = dict()

        #머신러닝 데이터 저장
        finding_ML_data = ML_DB.find_one({'HW_ID': str(test['serial'])})
        if bool(finding_ML_data):

            print("not empty")
            finding_ML_data['count'] = (finding_ML_data['count'] +1) % 3
            test.pop('_id')
            finding_ML_data['data'].append(test)
            if finding_ML_data['count'] == 0:
                call_ML(finding_ML_data)
                new_list = list()
                finding_ML_data['data'] = new_list
            ML_DB.update({"HW_ID": finding_ML_data['HW_ID']},
                         {
                             '$set': {
                                 'data' : finding_ML_data['data'],
                                 'count' : finding_ML_data['count'],
                             }
                         }
                         ,upsert = False, multi = False)

        else:
            print("empty")
            new_list = list()
            test.pop('_id')
            new_list.append(test)

            new_dict['HW_ID'] = str(test['serial'])
            new_dict['count'] = 1
            new_dict['data'] = new_list
            ML_DB.insert_one(new_dict)

        #IoT 온습도 변화정보 라즈베리파이 전송
        matching = db.IoT_Device
        finding = matching.find_one({"HW_ID" : str(test['serial'])})
        response = {'temp' : float(finding['SET_TEMP']), 'hum' : float(finding['SET_HUM']), 'connect' : 1}
        json_response = json.dumps(response)

        client.close()
        return HttpResponse(json_response, status=200)


def call_ML(ML_data):
    client = pymongo.MongoClient(db_address)
    db = client.IoT_DB
    USER_matching = db.User_Room_Matching
    FCM_key_matching = db.FCM_key

    train = pd.read_csv('./train_nt6.csv')
    test0 = pd.DataFrame(ML_data['data'][0], index = [0])
    test1 = pd.DataFrame(ML_data['data'][1], index = [1])
    test2 = pd.DataFrame(ML_data['data'][2], index = [2])
    resutl1 = test0.append(test1)
    test = resutl1.append(test2)
    test_time = test.sort_values(by=['cur_time'], axis=0)

    idx1 = test_time[(test_time['temp_max'] > 50) | (test_time['temp_min'] < -20)].index
    test_time = test_time.drop(idx1)
    idx2 = test_time[(test_time['hum_max'] > 100) | (test_time['hum_min'] < 0)].index
    test_time = test_time.drop(idx2)

    num = test_time.shape[0]
    test_time = test_time.reindex(range(num), method='ffill')

    f = open("test14p.csv", "w")
    f.write('temp_avg_gap')
    f.write(",")
    f.write('hum_avg_gap')
    f.write(",")
    f.write('temp_max_min')
    f.write(",")
    f.write('temp_min_max')
    f.write(",")
    f.write('hum_max_min')
    f.write(",")
    f.write('hum_min_max')
    f.write(",")
    f.write('status')
    f.write("\n")
    for i in range(test_time.shape[0] - 1):
        if test_time['status'][i] != 22:
            if test_time['status'][i + 1] == test_time['status'][i] and test_time['serial'][i + 1] == test_time['serial'][i]:
                data = test_time['cur_time'][i + 1] - test_time['cur_time'][i]
                res = round(data.seconds + data.days * 24 * 3600)
                print("res = ",res)
                if res < 100:
                    print("4")
                    f.write(str(round(test_time['temp_avg'][i + 1] - test_time['temp_avg'][i], 2)))
                    f.write(",")
                    f.write(str(round(test_time['hum_avg'][i + 1] - test_time['hum_avg'][i], 2)))
                    f.write(",")
                    f.write(str(round(test_time['temp_max'][i + 1] - test_time['temp_min'][i], 2)))
                    f.write(",")
                    f.write(str(round(test_time['temp_min'][i + 1] - test_time['temp_max'][i], 2)))
                    f.write(",")
                    f.write(str(round(test_time['hum_max'][i + 1] - test_time['hum_min'][i], 2)))
                    f.write(",")
                    f.write(str(round(test_time['hum_min'][i + 1] - test_time['hum_max'][i], 2)))
                    f.write(",")
                    f.write(str(test_time['status'][i]))
                    f.write("\n")
    f.close()

    test = pd.read_csv('./test14p.csv')

    train_data = train.drop('work', axis=1)
    target = train["work"]
    clf = RandomForestClassifier(n_estimators=7)
    clf.fit(train_data, target)


    test_data = test.copy()

    if (test_data.shape[0] < 2):
        return 0

    predict = clf.predict(test_data)
    result = pd.DataFrame({
        'status': test['status'],
        'work': predict
    })
    print(result)
    result.to_csv('result_RF_14.csv', index=False)
    result_RF = pd.read_csv('result_RF_14.csv')
    print(result_RF)

    for i in range(0, result_RF.shape[0] - 1, 2):
        if result_RF['status'][i] == result_RF['status'][i + 1]:
            if (result_RF['work'][i] | result_RF['work'][i + 1]) == 0:
                print("ERROR OCCUR in status ", result_RF['status'][i])
                print(result_RF['work'][i])
                print(result_RF['work'][i + 1])
                print(i)
                #DB에서 HW_ID를 바탕으로 user id 를 검색
                #DB 의 FCM_key에는 USER_ID와 key 값만있으므로 search 할 때 USER_ID 중요
                userid = USER_matching.find_one({'HW_ID': str(ML_data['data'][0]['serial'])})
                FCM = FCM_key_matching.find_one({'USER_ID' : userid['USER_ID']})

                send_form_FCM(FCM['Key'], result_RF['status'][i])


def send_form_FCM(ids, status):

    temp_st = int(status / 10)
    hum_st = int(status) % 10
    print("status = ",status,type(status))
    print("temp_st = ",temp_st)
    print("hum_st = ",hum_st)

    title = ''
    body = ''
    print("making message body")

    #해당 모델에서는 온도를 올리고 습도를 낮추는 기능으로 백열구가 연결되어 있으므로 문제점이 됨
    #따라서 온도를 올려야되고 습도를 낮춰야 되는 경우룰 분리시켜서 if checking
    if temp_st == 1 :
        title += '팬 '
        body += '팬 연결 상태와 동작 상태를 확인해주세요\n'
    if temp_st == 3 and hum_st == 1:
        title += '백열구 '
        body += '백열구 연결 상태와 동작 상태를 확인해 주세요\n'
    elif temp_st == 3:
        title += '백열구 '
        body += '백열구 연결 상태와 동작 상태를 확인해 주세요\n'
    elif hum_st == 1:
        title += '백열구 '
        body += '백열구 연결 상태와 동작 상태를 확인해 주세요\n'
    if hum_st == 3:
        title += '가습기 '
        body += '가습기 연결 상태와 동작 상태를 확인해 주세요\n'

    title += "에러"

    # fcm 푸시 메세지 요청 주소
    url = 'https://fcm.googleapis.com/fcm/send'

    # 인증 정보(서버 키)를 헤더에 담아 전달
    #header 의 정보로 FCM_key, 즉 Firebase 에 등록된 앱의 key를 사용
    headers = {
        'Authorization': 'key='+FCM_Key,
        'Content-Type': 'application/json; UTF-8',
    }


    #ids 에는 기기별로 고유하게 가지는 Token 값을 사용
    # 보낼 내용을 작성
    content = {
        'to': ids,
        'notification': {
            'title': title,
            'body': body
        }
    }
    print("send request message to FCM")

    r = requests.post(url, data=json.dumps(content), headers=headers)
