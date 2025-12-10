from django.urls import path
from . import views

urlpatterns = [
    # 1. 메인 화면
    path('', views.index, name='index'),
    
    # 2. 새 프로젝트 생성
    path('event/new/', views.event_create, name='event_create'),
    
    # 3. 상세 페이지
    path('event/<int:event_id>/', views.detail, name='detail'),
    
    # 4. 엑셀 다운로드
    path('event/<int:event_id>/export/', views.export_excel, name='export_excel'),
]