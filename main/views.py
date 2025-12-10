from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Event, Task
# [수정] 분리된 폼들(Overview, Space) 추가 임포트
from .forms import CueForm, EventForm, TaskForm, EventOverviewForm, EventSpaceForm
from django.contrib.auth.forms import UserCreationForm 
from django.contrib.auth import login 
from .calculators import calculate_space, calculate_audio, LightingEngine, draw_space, draw_audio, draw_light
import pandas as pd
import urllib.parse
from datetime import date # [신규] D-Day 계산용

# 1. 메인 대시보드
def index(request):
    if request.user.is_authenticated:
        events = Event.objects.filter(author=request.user).order_by('-created_at')
        return render(request, 'main/index.html', {'events': events})
    else:
        return render(request, 'main/index.html')

# 2. 새 프로젝트 생성 (기본 EventForm 사용)
def event_create(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.author = request.user
            event.save()
            return redirect('detail', event_id=event.id) # 생성 후 바로 상세 페이지로 이동
    else:
        form = EventForm()
        
    return render(request, 'main/event_form.html', {'form': form})

# 3. 상세 페이지 (통합 상황실 & 솔루션 모드)
def detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    
    # === [폼 초기화: 탭별로 분리] ===
    overview_form = EventOverviewForm(instance=event)
    space_form = EventSpaceForm(instance=event)
    cue_form = CueForm()
    task_form = TaskForm()

    # === [POST 요청 처리] ===
    if request.method == 'POST':
        # [Tab 1] 개요 & 재무 정보 수정
        if 'update_overview' in request.POST:
            overview_form = EventOverviewForm(request.POST, instance=event)
            if overview_form.is_valid():
                overview_form.save()
                return redirect('detail', event_id=event.id)
        
        # [Tab 2] 공간 설계 수정
        elif 'update_space' in request.POST:
            space_form = EventSpaceForm(request.POST, instance=event)
            if space_form.is_valid():
                space_form.save()
                return redirect('detail', event_id=event.id)

        # [Tab 4] 할 일 추가
        elif 'add_task' in request.POST:
            task_form = TaskForm(request.POST)
            if task_form.is_valid():
                task = task_form.save(commit=False)
                task.event = event
                task.save()
                return redirect('detail', event_id=event.id)

        # [Tab 4] 할 일 삭제
        elif 'delete_task' in request.POST:
            task_id = request.POST.get('task_id')
            Task.objects.filter(id=task_id).delete()
            return redirect('detail', event_id=event.id)

        # [Tab 5] 큐시트 저장
        elif 'save_cue' in request.POST:
            cue_form = CueForm(request.POST)
            if cue_form.is_valid():
                cue = cue_form.save(commit=False)
                cue.event = event
                cue.save()
                return redirect('detail', event_id=event.id)

    # ==========================================
    # 📊 대시보드 데이터 계산 [업그레이드 완료]
    # ==========================================
    
    # 1. D-Day 계산
    today = date.today()
    d_day = (event.date - today).days
    
    # 2. 진척률 (Progress)
    total_tasks = event.tasks.count()
    done_tasks = event.tasks.filter(is_done=True).count()
    if total_tasks > 0:
        progress = int((done_tasks / total_tasks) * 100)
    else:
        progress = 0
        
    # 3. 재무 계산 (콤마 포맷팅 & 수익률 추가)
    budget = event.budget
    cost = event.expected_cost
    profit = budget - cost
    
    # 수익률(%) 계산 (0으로 나누기 방지)
    if budget > 0:
        profit_rate = round((profit / budget) * 100, 1)
    else:
        profit_rate = 0.0

    # 천단위 콤마(,) 찍기 (문자열로 변환)
    fmt_budget = f"{budget:,}"
    fmt_cost = f"{cost:,}"
    fmt_profit = f"{profit:,}"

    # === [데이터 가져오기] ===
    tasks = event.tasks.all().order_by('deadline')
    cues = event.cue_set.all().order_by('order')
    
    # ==========================================
    # 🧠 파이썬 계산기 & 시각화 가동
    # ==========================================
    
    space_report = calculate_space(event)
    graph_space = draw_space(event)
    audio_report = calculate_audio(event)
    graph_audio = draw_audio(event, audio_report['specs'])
    l_engine = LightingEngine(event)
    light_patch, light_power, light_layout, gen_info = l_engine.get_patch_data() 
    graph_light = draw_light(event, light_layout)
    
    return render(request, 'main/detail.html', {
        'event': event, 
        
        # [Dashboard Data]
        'd_day': d_day,
        'progress': progress,
        # 포맷팅된 재무 데이터 전달
        'fmt_budget': fmt_budget,
        'fmt_cost': fmt_cost,
        'fmt_profit': fmt_profit,
        'profit_rate': profit_rate, # 수익률 (%)
        'profit_raw': profit,       # 색상 판별용 숫자(int)

        # Forms
        'overview_form': overview_form,
        'space_form': space_form,
        'task_form': task_form,
        'form': cue_form,
        
        # Lists & Reports
        'tasks': tasks, 
        'cues': cues, 
        'space': space_report,
        'audio': audio_report,
        'light_patch': light_patch,
        'light_power': light_power,
        'gen_info': gen_info,
        'graph_space': graph_space,
        'graph_audio': graph_audio,
        'graph_light': graph_light
    })

# [신규] 프로젝트 삭제 기능
def event_delete(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if event.author != request.user:
        return HttpResponse("권한이 없습니다.", status=403)
    
    if request.method == 'POST':
        event.delete()
        return redirect('index')
    return redirect('index')

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

# 5. 회원가입
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})