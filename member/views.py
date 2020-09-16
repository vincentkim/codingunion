import json
import bcrypt
from rest_framework.permissions import IsAuthenticated, AllowAny

from rest_framework.views import APIView

import jwt

from django_server.settings import SECRET_KEY

from django.views import View
from django.http import JsonResponse, HttpResponse
from braces.views import CsrfExemptMixin
import pymongo

db_address = "Your Mongo address"


# 로그인을 위한 View
# Request data = {'USER_ID' , 'USER_PW'}
# Response = string
class SignInView(CsrfExemptMixin, APIView):
    authentication_classes = []
    permission_classes =  [AllowAny]

    def post(self, request):
        data = request.data

        client = pymongo.MongoClient(db_address)
        db = client.IoT_DB
        datas = db.User
        cursors = datas.find()

        token = 0

        try:
            for cursor in cursors:
                if cursor['USER_ID'] == data['USER_ID']:
                    if data['USER_PW'] == cursor['USER_PW']:
                        return HttpResponse(data['USER_ID'], status=200)  # 토큰을 담아서 응답

            client.close()
            return HttpResponse(token,status=400)

        except KeyError:
            client.close()
            return HttpResponse(token, status=400)


# 회원가입을 위한 View
# Request data = {'USER_ID','USER_PW','ADDRESS','EMAIL','PHONE_NUM'}
# Response Data = String

class SignUpView(CsrfExemptMixin, APIView):
    authentication_classes = []
    permission_classes =  [AllowAny]

    def post(self, request):
        data = request.data

        client = pymongo.MongoClient(db_address)
        db = client.IoT_DB
        cursors = db.User

        try:
            Changed_PW = dict()
            Changed_PW['USER_ID'] = data['USER_ID']

            Changed_PW['USER_PW'] = data['USER_PW']
            Changed_PW['NAME'] = data['NAME']
            Changed_PW['ADDRESS'] = data['ADDRESS']
            Changed_PW['EMAIL'] = data['EMAIL']
            Changed_PW['PHONE_NUM'] = data['PHONE_NUM']

            response_json = json.dumps(Changed_PW)
            cursors.insert_one(Changed_PW)

            client.close()
            return HttpResponse(response_json,status=200)

        except KeyError:
            client.close()
            return HttpResponse(status=400)


# 회원가입 시 중복 아이디 체크를 위한 view
# Request data = String(USER_ID)
# Response = status 로 응답
class ValidationView(CsrfExemptMixin, APIView):

    authentication_classes = []
    permission_classes =  [AllowAny]
    def post(self, request):
        data = request.data

        client = pymongo.MongoClient(db_address)
        db = client.IoT_DB
        datas = db.User
        cursors = datas.find()

        jsonRes = json.dumps(data)

        for cursor in cursors:
            if data['USER_ID'] == cursor['USER_ID']:
                client.close()
                return HttpResponse(status=400)

        client.close()
        return HttpResponse(jsonRes, status=200)