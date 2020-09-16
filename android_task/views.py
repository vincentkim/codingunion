import datetime, timedelta
import json

import pymongo
import requests
from braces.views import CsrfExemptMixin
from bson import ObjectId
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

# Create your views here.
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

db_address = "Your mongo address"

#workingroom/find_workingroom: 로그인 한 아이디 정보를 바탕으로 Main_Room 정보를 찾는 페이지
#Request's Json data = {'USER_ID', 'Main_Room', 'Sub_Room',HW_Name', HW_ID', 'UPT_DATE', 'RED_DATE'}}
#Response Json list data, Json data 의 포맷은 request와 동일
class Room_Matching_find_View(CsrfExemptMixin, APIView):
    authentication_classes = []
    permission_classes =  [AllowAny]

    def post(self, request):
        data = request.data

        exist_data = 0
        #DB cursor CAll 
        client = pymongo.MongoClient(db_address)
        db = client.IoT_DB
        matching = db.User_Room_Matching
        matching_cursor = matching.find({"USER_ID": data})

        json_list = list()

        try:
            # Call 된 cursor 를 if 문으로 접근, Document 중 같은 USER_ID 가 있는 것을 찾음
            # 만약 등록된 데이터가 없다는 것은 Main_Room을 가진 신규 사용자가 아니므로 새로운 Main Room 을 생성
            for find_room in matching_cursor:
                if str(data) == find_room['USER_ID']:
                    del find_room['_id']
                    json_list.append(find_room)
                    exist_data = 1

            if exist_data == 0:
                dict_list = dict()
                dict_list['USER_ID']    = data
                dict_list['Main_Room']  = ''
                dict_list['Sub_Room']   = ''
                dict_list['HW_Name']    = ''
                dict_list['HW_ID']      = ''
                dict_list['UPT_DATE']   = ''
                dict_list['RED_DATE']   = ''
                json_list.append(dict_list)

            # convert_json = json.dumps(json_list)
            client.close()
            return JsonResponse(json_list, safe = False)

        except KeyError:
            client.close()
            return HttpResponse(status=400)

#Request's Json data = {'USER_ID', 'Main_Room', 'Sub_Room',HW_Name', HW_ID', 'UPT_DATE', 'RED_DATE'}}
#Response data = String, 실제로 사용되는 값은 아님.
class Add_SR_View(CsrfExemptMixin, APIView):
    authentication_classes = []
    permission_classes =  [AllowAny]

    def post(self, request):
        data = request.data

        client = pymongo.MongoClient(db_address)
        db = client.IoT_DB
        matching = db.User_Room_Matching

        try:
            # 입력받은 USER_ID와 Main_Room 속성을 이용하여 새로운 Sub_Room 생성
            matching.update({'USER_ID': data['USER_ID'], 'Main_Room': data['Main_Room'], 'Sub_Room': ''},
                            { '$set':
                                  {'USER_ID'   : data['USER_ID'],
                                   'Main_Room' : data['Main_Room'],
                                   'Sub_Room'  : data['Sub_Room'],
                                   'HW_Name'   : '',
                                   'HW_ID'     : '',
                                   'UPT_DATE'  : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                   'RED_DATE'  : data['RED_DATE']
                                    }},
                            upsert=True,multi=False)
            client.close()
            return JsonResponse('OK',safe=False)

        except KeyError:
            client.close()
            return HttpResponse("Fail",status=400)

#Request's Json data = {'USER_ID', 'Main_Room', 'Sub_Room',HW_Name', HW_ID', 'UPT_DATE', 'RED_DATE'}}
#Resonse data = Json List data, Json data ={'HW_ID', 'Temp', 'Hum'}
class Get_TH_View(CsrfExemptMixin, APIView):
    authentication_classes = []
    permission_classes =  [AllowAny]

    def post(self, request):
        data = request.data

        client = pymongo.MongoClient(db_address)
        db = client.IoT_DB

        json_list = list()
        exist_data = 0
        # DB에 접근하여 최신 온도를 검색, 최신온도 정보를 list json 형태로 받아 저장
        for reach_data in data:
            if reach_data['HW_ID'] != "":
                dbs = db.Sensor.find({"serial": int(reach_data['HW_ID'])}).limit(1).sort([('cur_time', pymongo.DESCENDING)])

                for s in dbs:
                    sending_dict = dict()
                    sending_dict['HW_ID'] = s['serial']
                    sending_dict['Temp'] = str(s['temp_avg'])
                    sending_dict['Hum'] = str(s['hum_avg'])
                    exist_data = 1
                    json_list.append(sending_dict)
        # 만약 검색된 데이터가 없다면 빈 json data list 를 만들어서 전송
        if exist_data == 0:
            null_sensing = dict()
            null_sensing = {
                'HW_ID' : '',
                'temp' : '',
                'hum' : '',
            }
            json_list.append(null_sensing)
        try:
            client.close()
            return JsonResponse(json_list,safe=False)
        except KeyError:
            client.close()
            return HttpResponse(status=400)

#Request's json data = {'USER_ID', 'Main_Room', 'Sub_Room',HW_Name', HW_ID', 'UPT_DATE', 'RED_DATE'}}
#Response data = String, 실제로 사용 X
class Making_MR_view(CsrfExemptMixin, APIView):
    authentication_classes = []
    permission_classes =  [AllowAny]

    def post(self, request):
        data = request.data
        client = pymongo.MongoClient(db_address)
        db = client.IoT_DB
        matching = db.User_Room_Matching
        
        # Main Room 이 없을 때, 입력받은 Main Room 정보를 받아 
        # 새로운 Main Room 정보를 DB에 등록
        new_Room = {
            'USER_ID'   : data['USER_ID'],
            'Main_Room' : data['Main_Room'],
            'Sub_Room'  : '',
            'HW_Name'   : '',
            'HW_ID'     : '',
            'UPT_DATE'  : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'RED_DATE'  : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        try:
            matching.insert_one(new_Room)
            client.close()
            return HttpResponse("Success", status=200)
        except KeyError:
            client.close()
            return HttpResponse(status=400)

#Request's json data = {'USER_ID', 'Main_Room', 'Sub_Room',HW_Name', HW_ID', 'UPT_DATE', 'RED_DATE'}}
#Response's json data = string
class Change_SR_view(CsrfExemptMixin, APIView):
    authentication_classes = []
    permission_classes =  [AllowAny]

    def post(self, request):
        data = request.data
        client = pymongo.MongoClient(db_address)
        db = client.IoT_DB
        matching = db.User_Room_Matching

        # Sub Room 정보와 바꾸고 싶은 방 이름을 받아와서 DB에 저장
        # data안에는 기존의 Sub Room data 가 data['Sub_Room']에
        # 바꾸고 싶은 방의 이름이 data['Main_Room']에 있음
        try:
            matching.update({'USER_ID': data['USER_ID'], 'Sub_Room': data['Sub_Room']},
                            {'$set':
                                {
                                    'Sub_Room': data['Main_Room'],
                                    'UPT_DATE': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                }},
                            upsert=False, multi=True)
            client.close()
            return HttpResponse("OK", status= 200)
        except KeyError:
            client.close()
            return HttpResponse("Error", status=400)

#Request's json data = {'USER_ID', 'Main_Room', 'Sub_Room',HW_Name', HW_ID', 'UPT_DATE', 'RED_DATE'}}
#Response's json data = string
class Delete_SR_View(CsrfExemptMixin, APIView):
    authentication_classes = []
    permission_classes =  [AllowAny]

    def post(self, request):
        data = request.data
        client = pymongo.MongoClient(db_address)
        db = client.IoT_DB
        matching = db.User_Room_Matching
        IoT_matching = db.IoT_Device

        # 삭제하고 싶은 Sub Room 정보를 받아와서 해당 정보를 DB에서 삭제
        
        try:
            HW_ID_List = list()
            finding = matching.find( {"USER_ID" : data['USER_ID'], "Sub_Room" : data['Sub_Room']})
            for part in finding:
                HW_ID_List.append(part['HW_ID'])
            matching.delete_many( {"USER_ID" : data['USER_ID'], "Sub_Room" : data['Sub_Room']})
            # 삭제되는 Sub Room과 연결된 IoT는 disconnect로 전환
            for HW_ID in HW_ID_List:
                IoT_matching.update({'HW_ID': HW_ID},
                                    {'$set':
                                        {
                                            'connection': '0',
                                            'UPT_DATE': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        }},
                                    upsert=False, multi=False)

            client.close()
            return HttpResponse("OK", status= 200)
        except KeyError:
            client.close()
            return HttpResponse("Error", status=400)

#Request's json data = {'USER_ID', 'Main_Room', 'Sub_Room',HW_Name', HW_ID', 'UPT_DATE', 'RED_DATE'}}
#Response's json data = Json List data, json data 포맷은 Request 와 동일
class Find_SR_View(CsrfExemptMixin, APIView):
    authentication_classes = []
    permission_classes =  [AllowAny]

    def post(self, request):
        data = request.data
        client = pymongo.MongoClient(db_address)
        db = client.IoT_DB
        matching = db.User_Room_Matching

        json_list = list()
        exist_data = 0
        
        # Sub Room 페이지에 들어갔을 때, 보여줄 Sub_Room 정보를 DB로부터 찾아 response 전송
        try:
            finding = matching.find({"USER_ID" : data['USER_ID'], "Sub_Room" : data['Sub_Room']})
            for HW in finding:
                del HW['_id']
                json_list.append(HW)
                exist_data =1

            if exist_data == 0:
                dict_list = dict()
                dict_list['USER_ID'] = ''
                dict_list['Main_Room'] = ''
                dict_list['Sub_Room'] = ''
                dict_list['HW_Name'] = ''
                dict_list['HW_ID'] = ''
                dict_list['UPT_DATE'] = ''
                dict_list['RED_DATE'] = ''
                json_list.append(dict_list)

            client.close()
            return JsonResponse(json_list, safe=False)
        except KeyError:
            client.close()
            return HttpResponse(status=400)

#Request's body 는 없음
#Response's data = Json List data
#{'userID', 'Sub', 'HW_ID', 'MAC', 'RED_DATE', 'HEALTH'}
class Find_IoT_List_View(CsrfExemptMixin, APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        client = pymongo.MongoClient(db_address)
        db = client.IoT_DB
        matching = db.IoT_Device
        
        # disconnect 상태인 IoT 목록을 찾아서 response
        try:
            json_list = list()
            finding = matching.find({'connection': '0'})
            for parts in finding:
                get_dict = dict()
                get_dict['MAC'] = parts['HW_MAC']
                get_dict['HW_ID'] = parts['HW_ID']
                get_dict['RED_DATE'] = parts['RED_DATE']
                get_dict['Health'] = 'Good'
                if int(parts['DISCON_TIME']) >= 10:
                    get_dict['Health'] = 'Bad'
                json_list.append(get_dict)

            client.close()
            return JsonResponse(json_list, safe=False)

        except KeyError:
            client.close()
            return HttpResponse(status=400)

#Request's Json data = {'userID', 'Sub', 'HW_ID', 'MAC', 'RED_DATE', 'HEALTH'}
#Response = string, 실제로 사용 X
class Add_IoTtoSub_View(CsrfExemptMixin, APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        client = pymongo.MongoClient(db_address)
        db = client.IoT_DB
        matching = db.User_Room_Matching
        IoT_matching = db.IoT_Device

        # disconnected IoT List 에서 클릭된 대상 정보를 받고
        # 해당 IoT를 Sub Room 밑으로 편입, connect 상태로 전환
        try:
            finding = matching.find({'USER_ID': data['userID'], 'Sub_Room': data['Sub']})
            add_dict = dict()
            for part in finding:
                del part['_id']
                add_dict = part
            add_dict['HW_ID'] = data['HW_ID']
            add_dict['HW_Name'] = 'New Device'
            IoT_matching.update({'HW_ID' : data['HW_ID']},
                                {'$set':
                                    {
                                        'connection': '1',
                                        'UPT_DATE': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    }},
                                upsert=False, multi=False)

            add_dict['UPT_DATE'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            matching.insert_one(add_dict)
            client.close()
            return HttpResponse("OK", status=200)

        except KeyError:
            client.close()
            return HttpResponse("Error", status=400)

#Request's json data = {'USER_ID', 'Main_Room', 'Sub_Room',HW_Name', HW_ID', 'UPT_DATE', 'RED_DATE'}}
#Response = Json List data, Json data 는 Request 와 동일
class Find_HW_Name_View(CsrfExemptMixin, APIView):
    authentication_classes = []
    permission_classes =  [AllowAny]

    def post(self, request):
        data = request.data
        client = pymongo.MongoClient(db_address)
        db = client.IoT_DB
        matching = db.User_Room_Matching

        sending_data = dict()
        exist_data = 0
        # IoT 버튼을 눌렀을 떄, 보여줄 IoT 정보를 response, 1개의 IoT 에 대한 세부 정보만릉 response
        try:
            finding = matching.find({"HW_ID" : data['HW_ID']})
            for HW in finding:
                del HW['_id']
                sending_data = HW
                exist_data =1

            if exist_data == 0:
                dict_list = dict()
                dict_list['USER_ID'] = ''
                dict_list['Main_Room'] = ''
                dict_list['Sub_Room'] = ''
                dict_list['HW_Name'] = ''
                dict_list['HW_ID'] = ''
                dict_list['UPT_DATE'] = ''
                dict_list['RED_DATE'] = ''
                sending_data = dict_list
            jsonList = list()
            jsonList.append(sending_data)
            client.close()
            return JsonResponse(jsonList, safe=False)
        except KeyError:
            client.close()
            return HttpResponse(status=400)

#Request's json data = {'USER_ID', 'Main_Room', 'Sub_Room',HW_Name', HW_ID', 'UPT_DATE', 'RED_DATE'}}
#Response = String, 실제로 사용되는 데이터 X
class Change_HW_name(CsrfExemptMixin, APIView):
    authentication_classes = []
    permission_classes =  [AllowAny]

    def post(self, request):
        data = request.data
        client = pymongo.MongoClient(db_address)
        db = client.IoT_DB
        matching = db.User_Room_Matching
        IoT_matching = db.IoT_Device

        # 변경하고 싶은 IoT의 이름을 data['HW_Name']으로 받고
        # 변경할 IoT 의 HW_ID 를 가지고 탐색, 변경하여 저장
        # 이 때, 저장되는 DB가 User_Room_Matching 과 IoT_Device 2개
        try:
            matching.update({'USER_ID': data['USER_ID'], 'HW_ID': data['HW_ID']},
                            {'$set':
                                {
                                    'HW_Name': data['HW_Name'],
                                    'UPT_DATE': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                }},
                            upsert=False, multi=False)
            IoT_matching.update( {'HW_ID': data['HW_ID']},
                                 {'$set':
                                     {
                                         'HW_Name': data['HW_Name'],
                                         'UPT_DATE': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                     }},
                                 upsert=False, multi=False)

            client.close()
            return HttpResponse("OK", status= 200)
        except KeyError:
            client.close()
            return HttpResponse("Error", status=400)

#Request's json data = {'USER_ID', 'Main_Room', 'Sub_Room',HW_Name', HW_ID', 'UPT_DATE', 'RED_DATE'}}
#Response = String, 실제로 사용되는 데이터 X
class Delete_HW_View(CsrfExemptMixin, APIView):
    authentication_classes = []
    permission_classes =  [AllowAny]

    def post(self, request):
        data = request.data
        client = pymongo.MongoClient(db_address)
        db = client.IoT_DB
        matching = db.User_Room_Matching
        IoT_matching = db.IoT_Device

        # Sub Room 에서 삭제하고 싶은 IoT를 삭제
        # 이때, disconnect 상태로 만들어 주고,
        # HW_Name의 경우 새로 등록할 때 자동으로 New Device 로 변경되므로 수정 X
        try:
            matching.delete_one( {"USER_ID" : data['USER_ID'], "HW_ID" : data['HW_ID']})
            IoT_matching.update( {'HW_ID': data['HW_ID']},
                                 {'$set':
                                     {
                                         'connection': '0',
                                         'UPT_DATE': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                     }},
                                 upsert=False, multi=False)

            client.close()
            return HttpResponse("OK", status= 200)
        except KeyError:
            client.close()
            return HttpResponse("Error", status=400)

#Request's json data = {'HW_ID', 'Temp', 'Hum'}
#Response = String, 실제로 사용되는 데이터 X
class Change_TH_View(CsrfExemptMixin, APIView):
    authentication_classes = []
    permission_classes =  [AllowAny]

    # 설정된 온 습도 값을 변경
    def post(self, request):
        data = request.data
        client = pymongo.MongoClient(db_address)
        db = client.IoT_DB
        matching = db.IoT_Device

        try:
            matching.update({'HW_ID': data['HW_ID']},
                            {'$set':
                                {
                                    'SET_TEMP': data['Temp'],
                                    'HIGH_TEMP' : str(int(data['Temp'])+ 10),
                                    'LOW_TEMP' : str(int(data['Temp'])- 5),
                                    'SET_HUM' : data['Hum'],
                                    'HIGH_HUM': str(int(data['Hum']) + 10),
                                    'LOW_HUM': str(int(data['Hum']) - 5),
                                    'UPT_DATE': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                }},
                            upsert=False, multi=False)

            client.close()
            return HttpResponse("OK",status=200)

        except KeyError:
            client.close()
            return HttpResponse(status=400)

#Request's json data = String(HW_ID)
#Response = Json list data
#{'HW_ID', 'Temp', 'Hum'}
class Show_detail_graph_View(CsrfExemptMixin, APIView):
    authentication_classes = []
    permission_classes =  [AllowAny]

    def post(self, request):
        data = request.data
        client = pymongo.MongoClient(db_address)
        db = client.IoT_DB
        matching = db.Sensor
        start_day = datetime.datetime.today().replace(microsecond=0)+ datetime.timedelta(days=-int(data['start_date']))
        end_day = datetime.datetime.today().replace(microsecond=0) + datetime.timedelta(days=-int(data['end_date']))

        # 온 습도 값을 그래프로 보여주기 위해서 Json list data 를 response
        # 요청 시간 기준으로 start day 와 end day를 계산
        # today - data['start_day'] = start_day
        # today - data['end_day'] = end_day
        try:
            json_list = list()
            finding = matching.find({'serial': int(data['HW_ID']),
                           'cur_time': {'$lte': end_day, '$gte': start_day}})

            for parts in finding:
                add_dict = dict()
                if int(data['mode']) ==0:
                    add_dict['Temp'] = parts['temp_avg']
                    add_dict['cur_time'] = parts['cur_time'].strftime("%Y-%m-%d %H:%M:%S")
                    json_list.append(add_dict)
                elif int(data['mode']) ==1:
                    add_dict['Hum'] = parts['hum_avg']
                    add_dict['cur_time'] = parts['cur_time'].strftime("%Y-%m-%d %H:%M:%S")
                    json_list.append(add_dict)
            client.close()
            return JsonResponse(json_list, safe=False)
        except KeyError:
            client.close()
            return HttpResponse(status=400)

class Get_Target_View(CsrfExemptMixin, APIView):
    authentication_classes = []
    permission_classes =  [AllowAny]

    def post(self, request):
        data = request.data
        client = pymongo.MongoClient(db_address)
        db = client.IoT_DB
        matching = db.IoT_Device
        json_dict = list()

        # IoT의 설정 온도, 습도를 찾아서 response
        try:
            finding = matching.find_one({"HW_ID": data})
            get_dict = dict()
            get_dict['HW_ID'] = finding['HW_ID']
            get_dict['Temp'] = finding['SET_TEMP']
            get_dict['Hum'] = finding['SET_HUM']
            json_dict.append(get_dict)

            return JsonResponse(json_dict, safe=False)

        except KeyError:
            return HttpResponse(status=400)

class Save_FCM_key_View(CsrfExemptMixin, APIView):
    authentication_classes = []
    permission_classes =  [AllowAny]

    def post(self, request):
        data = request.data
        client = pymongo.MongoClient(db_address)
        db = client.IoT_DB
        matching = db.FCM_key

        #Firebase Clouding Mesasge service 를 사용하기 위한
        # 사용자 단말기별 Token 값을 DB에 저장
        try:
            matching.update({'USER_ID': data['USER_ID']},
                            {'$set':
                                {
                                    'Key' : data['key']
                                }},
                            upsert=True, multi=False)
            return HttpResponse('Success',status=200)
        except KeyError:
            return HttpResponse("Fail", status=400)

