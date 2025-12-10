from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Event
from .forms import CueForm, EventForm
from django.contrib.auth.forms import UserCreationForm # 회원가입 폼
from django.contrib.auth import login # 가입 후 즉시 로그인

# [수정] 도면 그리는 함수들(draw_...) 추가 임포트
from .calculators import calculate_space, calculate_audio, LightingEngine, draw_space, draw_audio, draw_light
import pandas as pd
import urllib.parse

# 1. 메인 대시보드
def index(request):
    if request.user.is_authenticated:
        events = Event.objects.filter(author=request.user).order_by('-created_at')
        return render(request, 'main/index.html', {'events': events})
    else:
        return render(request, 'main/index.html')

# 2. 새 프로젝트 생성
def event_create(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.author = request.user
            event.save()
            return redirect('index')
    else:
        form = EventForm()
        
    return render(request, 'main/event_form.html', {'form': form})

# 3. 상세 페이지 (솔루션 모드) - 최종 버전
def detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    
    # 폼 초기화 (에러 방지용)
    cue_form = CueForm()
    event_form = EventForm(instance=event)

    # POST 요청 처리
    if request.method == 'POST':
        # [A] 큐시트 저장
        if 'save_cue' in request.POST:
            cue_form = CueForm(request.POST)
            if cue_form.is_valid():
                cue = cue_form.save(commit=False)
                cue.event = event
                cue.save()
                return redirect('detail', event_id=event.id)
        
        # [B] 행사 설계 수정
        elif 'update_event' in request.POST:
            event_form = EventForm(request.POST, instance=event)
            if event_form.is_valid():
                event_form.save()
                return redirect('detail', event_id=event.id)

    # 데이터 가져오기
    tasks = event.tasks.all().order_by('deadline')
    cues = event.cue_set.all().order_by('order')
    
    # ==========================================
    # 🧠 파이썬 계산기 & 시각화 가동
    # ==========================================
    
    # 1. 공간 분석 & 도면 그리기
    space_report = calculate_space(event)
    graph_space = draw_space(event) # <--- [추가] 공간 도면 생성
    
    # 2. 음향 분석 & 도면 그리기
    audio_report = calculate_audio(event)
    graph_audio = draw_audio(event, audio_report['specs']) # <--- [추가] 음향 도면 생성
    
    # 3. 조명 분석 & 도면 그리기
    l_engine = LightingEngine(event)
    # [주의] calculators.py를 수정했으므로 이제 3개 값을 리턴합니다 (패치, 전력, 레이아웃)
    light_patch, light_power, light_layout = l_engine.get_patch_data() 
    graph_light = draw_light(event, light_layout) # <--- [추가] 조명 도면 생성
    
    return render(request, 'main/detail.html', {
        'event': event, 
        'tasks': tasks, 
        'cues': cues, 
        'form': cue_form, 
        'event_form': event_form,
        # 수치 리포트
        'space': space_report,
        'audio': audio_report,
        'light_patch': light_patch,
        'light_power': light_power,
        # 도면 이미지 (Base64 코드)
        'graph_space': graph_space,
        'graph_audio': graph_audio,
        'graph_light': graph_light
    })

# 4. 엑셀 다운로드
def export_excel(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    cues = event.cue_set.all().order_by('order').values('order', 'content', 'duration', 'bgm', 'action')
    
    if not cues:
        return HttpResponse("저장된 큐시트가 없습니다.", status=400)

    df = pd.DataFrame(list(cues))
    df.columns = ['No', '진행 내용', '시간(초)', 'BGM', 'Action']
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"CueSheet_{event.title}.xlsx"
    quoted_filename = urllib.parse.quote(filename.encode('utf-8'))
    response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{quoted_filename}'
    
    df.to_excel(response, index=False)
    return response

# [Step 10] 회원가입 기능
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # 가입 후 바로 로그인 처리
            return redirect('index') # 메인으로 이동
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})
