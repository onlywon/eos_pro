from django.contrib import admin
from django.urls import path, include
from main import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. 로그인/로그아웃
    path('accounts/', include('django.contrib.auth.urls')),
    
    # 2. 회원가입
    path('accounts/signup/', views.signup, name='signup'),
    
    # 3. 메인 앱으로 연결 (여기가 중요!)
    path('', include('main.urls')),
]