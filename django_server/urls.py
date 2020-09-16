"""jwt URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.urls import path, include
from member.views import SignUpView, SignInView,ValidationView
from sensor.views import SensorView
from android_task.views import Room_Matching_find_View, Add_SR_View, Get_TH_View, Making_MR_view, \
    Change_SR_view,Delete_SR_View, Find_SR_View, Find_IoT_List_View, Add_IoTtoSub_View, Find_HW_Name_View, \
    Change_HW_name, Delete_HW_View, Change_TH_View, Show_detail_graph_View, Get_Target_View, \
    Save_FCM_key_View

#sign-up: 회원가입 페이지
#sign-in: 로그인 페이지
#sign-up/valid: 중복 아이디 체크 페이지
#sensing: 센싱 정보 DB 저장 및 머신러닝 결과 도출 페이지
#workingroom/find_workingroom: 로그인 한 아이디 정보를 바탕으로 Main_Room 정보를 찾는 페이지
#workingroom/add_Room: DB 정보를 바탕으로 Main_Room 하위의 Sub_Room을 추가하는 페이지
#workingroom/get_Temp_hum: Main_Room 이나 Sub_Room 페이지에서 보여줄 IoT 정보들을 전송받아 최신 온도를 보여주는 페이지
#workingroom//save_Fcm_key: 로그인 아이디 정보를 가지고 단말기의 FCM token을 DB에 저장하는 페이지
#sub/find_sub_room: Main_Room 페이지에서 Sub_Room 을 눌렀을 때 이동되는 페이지
#sub/change_sub_room: 현재 보고있는 sub_Room의 이름을 변경하는 페이지
#sub/delete_sub_room: 현재 보고있는 sub_Room을 삭제하는 페이지, 이때, 등록된 모든 기기는 disconnect 상태로 변경
#sub/find_IoT_List: sub_Room 페이지에서 IoT 추가 등록 버튼을 눌렀을 때, disconnect 상태의 기기 목록을 보여주는 페이지
#sub/add_IoT: IoT 추가등록 페이지에서 클릭된 IoT를 해당 sub_Room에 등록되도록 DB에 저장하는 페이지
#detail/find_HW_Name: Main_Room, Sub_Room 페이지에서 등록된 IoT 기기를 보여주도록 DB 정보를 가져오는 페이지
#detail/change_HW_Name: 세부정보를 보고있는 IoT의 이름을 변경하는 페이지
#detail/delete_HW_Name: 세부정보를 보고있는 IoT를 삭제하고, disconnect 하는 페이지
#detail/change_Temp_Hum: IoT_Device DB에 저장된 설정 온도, 습도 정보를 변경하는 페이지
#detail/Show_detail_graph: IoT가 측정한 정보를 그래프 형태로 보여줄 수 있도록 DB 정보를  보내주는 페이지
#detail/get_Target: IoT의 세부 온도 및 설정 온습도를 보여주는 페이지 데이터를 들고오는 페이지


urlpatterns = [
    path('sign-up', SignUpView.as_view()),
    path('sign-in', SignInView.as_view()),
    path('sign-in/valid', ValidationView.as_view()),
    path('sensing', SensorView.as_view()),
    path('workingroom/find_workingroom',Room_Matching_find_View.as_view()),
    path("workingroom/add_Room", Add_SR_View.as_view()),
    path('workingroom/get_Temp_hum', Get_TH_View.as_view()),
    path('workingroom/make_main', Making_MR_view.as_view()),
    path('workingroom/save_Fcm_key', Save_FCM_key_View.as_view()),
    path('sub/find_sub_room', Find_SR_View.as_view()),
    path('sub/change_sub_room', Change_SR_view.as_view()),
    path('sub/delete_sub_room', Delete_SR_View.as_view()),
    path('sub/find_IoT_list', Find_IoT_List_View.as_view()),
    path('sub/add_IoT', Add_IoTtoSub_View.as_view()),
    path('detail/find_HW_Name', Find_HW_Name_View.as_view()),
    path('detail/change_HW_Name', Change_HW_name.as_view()),
    path('detail/delete_HW_Name', Delete_HW_View.as_view()),
    path('detail/change_Temp_Hum', Change_TH_View.as_view()),
    path('detail/Show_detail_graph', Show_detail_graph_View.as_view()),
    path('detail/get_Target', Get_Target_View.as_view()),
]
