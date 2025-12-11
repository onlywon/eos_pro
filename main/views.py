from django.shortcuts import render, get_object_or_404, redirect, resolve_url
from django.http import HttpResponse
from .models import Event, Task, Vendor, Quotation, PurchaseOrder
from .forms import CueForm, EventForm, TaskForm, EventOverviewForm, EventSpaceForm
from django.contrib.auth.forms import UserCreationForm 
from django.contrib.auth import login 
from .calculators import calculate_space, calculate_audio, LightingEngine, draw_space, draw_audio, draw_light
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Case, When, Value, IntegerField
import pandas as pd
import urllib.parse
from datetime import date 

# 1. 메인 대시보드
@login_required
def index(request):
    events = Event.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'main/index.html', {'events': events})

# 2. 새 프로젝트 생성
@login_required
def event_create(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.author = request.user
            event.save()
            return redirect('detail', event_id=event.id)
    else:
        form = EventForm()
    return render(request, 'main/event_form.html', {'form': form})

# 3. 상세 페이지 (통합 상황실 & 솔루션 모드)
@login_required
def detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    
    if event.author != request.user:
        return HttpResponse("이 프로젝트를 볼 권한이 없습니다.", status=403)
    
    overview_form = EventOverviewForm(instance=event)
    space_form = EventSpaceForm(instance=event)
    cue_form = CueForm()
    task_form = TaskForm() 

    if request.method == 'POST':
        # [Tab 1] 개요 저장 -> #tab1 유지
        if 'update_overview' in request.POST:
            overview_form = EventOverviewForm(request.POST, instance=event)
            if overview_form.is_valid():
                overview_form.save()
                return redirect(resolve_url('detail', event_id=event.id) + '#tab1')
        
        # [Tab 2] 공간 설계 저장 -> #tab2 유지
        elif 'update_space' in request.POST:
            space_form = EventSpaceForm(request.POST, instance=event)
            if space_form.is_valid():
                space_form.save()
                return redirect(resolve_url('detail', event_id=event.id) + '#tab2')

        # [Tab 5] 큐시트 저장 -> #tab5 유지
        elif 'save_cue' in request.POST:
            cue_form = CueForm(request.POST)
            if cue_form.is_valid():
                cue = cue_form.save(commit=False)
                cue.event = event
                cue.save()
                return redirect(resolve_url('detail', event_id=event.id) + '#tab5')

    # --- 대시보드 계산 로직 ---
    today = date.today()
    d_day = (event.date - today).days
    
    total_tasks = event.tasks.count()
    done_tasks = event.tasks.filter(is_done=True).count()
    progress = int((done_tasks / total_tasks) * 100) if total_tasks > 0 else 0
        
    total_task_budget = event.tasks.aggregate(total=Sum('planned_budget'))['total'] or 0
    budget = event.budget if event.budget is not None else 0
    cost = total_task_budget 
    profit = budget - cost
    
    try:
        profit_rate = round((profit / budget) * 100, 1) if budget > 0 else 0.0
    except (TypeError, ZeroDivisionError):
        profit_rate = 0.0

    fmt_budget = f"{budget:,}"
    fmt_cost = f"{cost:,}"
    fmt_profit = f"{profit:,}"

    # === [데이터 가져오기: 정렬 로직 강화 (구버전 호환)] ===
    # 💡 과거 데이터(소문자)와 신규 데이터(대문자)를 모두 같은 순위로 묶어줍니다.
    
    phase_ordering = Case(
        # 1. 기획 (PLANNING, planning, admin) -> 0순위
        When(task_category__in=['PLANNING', 'planning', 'admin'], then=Value(0)),
        
        # 2. 디자인 (DESIGN, design) -> 1순위
        When(task_category__in=['DESIGN', 'design'], then=Value(1)),
        
        # 3. 제작/준비 (PREPARATION) -> 2순위
        When(task_category__in=['PREPARATION', 'preparation'], then=Value(2)),
        
        # 4. 실행/현장 (EXECUTION, execution) -> 3순위
        When(task_category__in=['EXECUTION', 'execution'], then=Value(3)),
        
        # 5. 정산/마감 (CLOSING, settlement) -> 4순위
        When(task_category__in=['CLOSING', 'settlement'], then=Value(4)),
        
        default=Value(99), # 기타 -> 맨 뒤
        output_field=IntegerField(),
    )
    
    # 정렬 적용: 순위(order_rank) -> 마감일(deadline)
    tasks = event.tasks.all().annotate(order_rank=phase_ordering).order_by('order_rank', 'deadline')
    
    cues = event.cue_set.all().order_by('order')
    
    # --- 시각화 엔진 ---
    space_report = calculate_space(event)
    graph_space = draw_space(event)
    audio_report = calculate_audio(event)
    graph_audio = draw_audio(event, audio_report['specs'])
    l_engine = LightingEngine(event)
    light_patch, light_power, light_layout, gen_info = l_engine.get_patch_data() 
    graph_light = draw_light(event, light_layout)
    
    return render(request, 'main/detail.html', {
        'event': event, 
        'd_day': d_day, 
        'progress': progress,
        'fmt_budget': fmt_budget, 
        'fmt_cost': fmt_cost, 
        'fmt_profit': fmt_profit,
        'profit_rate': profit_rate, 
        'profit_raw': profit,
        'overview_form': overview_form, 
        'space_form': space_form,
        'task_form': task_form, 
        'form': cue_form,
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

# ----------------------------------------------------------------------------------
# ▼▼▼ Task 관련 함수 (탭 위치 유지: #tab4) ▼▼▼
# ----------------------------------------------------------------------------------

@login_required
def task_add(request, event_id):
    if request.method != 'POST':
        return redirect(resolve_url('detail', event_id=event_id) + '#tab4')

    event = get_object_or_404(Event, pk=event_id)
    if event.author != request.user:
        return HttpResponse("권한이 없습니다.", status=403)

    form = TaskForm(request.POST) 
    if form.is_valid():
        task = form.save(commit=False)
        task.event = event
        task.save()
        
        total_task_budget = event.tasks.aggregate(total=Sum('planned_budget'))['total'] or 0
        event.expected_cost = total_task_budget 
        event.save(update_fields=['expected_cost'])
        
    return redirect(resolve_url('detail', event_id=event.id) + '#tab4')

@login_required
def task_delete(request, task_id):
    if request.method != 'POST':
        return redirect('index') 
    
    task = get_object_or_404(Task, pk=task_id)
    if task.event.author != request.user:
        return HttpResponse("권한이 없습니다.", status=403) 
        
    event_id = task.event.id
    task.delete()
    
    event = get_object_or_404(Event, pk=event_id)
    total_task_budget = event.tasks.aggregate(total=Sum('planned_budget'))['total'] or 0
    event.expected_cost = total_task_budget 
    event.save(update_fields=['expected_cost'])
    
    return redirect(resolve_url('detail', event_id=event_id) + '#tab4')

@login_required
def task_toggle(request, task_id):
    if request.method != 'POST':
        return redirect('index')

    task = get_object_or_404(Task, pk=task_id)
    if task.event.author != request.user:
        return HttpResponse("권한이 없습니다.", status=403) 
        
    task.is_done = not task.is_done
    task.save()
    
    return redirect(resolve_url('detail', event_id=task.event.id) + '#tab4')

@login_required
def task_update(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    
    if task.event.author != request.user:
        return HttpResponse("권한이 없습니다.", status=403)
        
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            
            event = task.event
            total_task_budget = event.tasks.aggregate(total=Sum('planned_budget'))['total'] or 0
            event.expected_cost = total_task_budget 
            event.save(update_fields=['expected_cost']) 
            
            return redirect(resolve_url('detail', event_id=event.id) + '#tab4')
    else:
        form = TaskForm(instance=task)
        
    return render(request, 'main/task_update_form.html', {
        'form': form, 
        'task': task, 
        'event_id': task.event.id
    })

# 8. 프로젝트 삭제 기능
@login_required
def event_delete(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if event.author != request.user:
        return HttpResponse("권한이 없습니다.", status=403)
    
    if request.method == 'POST':
        event.delete()
        return redirect('index')
    return redirect('index')

# 9. 엑셀 다운로드
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

# 10. 회원가입
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