from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('event/new/', views.event_create, name='event_create'),
    path('event/<int:event_id>/', views.detail, name='detail'),
    path('event/<int:event_id>/export/', views.export_excel, name='export_excel'),
    
    # [기존] 프로젝트 삭제 기능 주소
    path('event/<int:event_id>/delete/', views.event_delete, name='event_delete'),
    
    # ▼▼▼ [E.O.S (Task) 관리 신규 URL 추가] ▼▼▼
    # Task 추가 주소: event_id를 사용하여 해당 이벤트에 Task를 연결
    path('event/<int:event_id>/task/add/', views.task_add, name='task_add'),
    
    # Task 삭제 및 토글 주소: task_id를 사용하여 특정 Task를 처리
    path('task/<int:task_id>/delete/', views.task_delete, name='task_delete'),
    path('task/<int:task_id>/toggle/', views.task_toggle, name='task_toggle'),

    # ▼▼▼ [신규 추가] Task 수정 전용 URL ▼▼▼
    path('task/<int:task_id>/update/', views.task_update, name='task_update'),
]