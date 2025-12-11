from django import forms
from .models import Cue, Event, Task, Vendor, Quotation, PurchaseOrder 

# 💡 [필수 수정] models.py에서 변경된 상수 이름으로 임포트
from .models import (
    TYPE_CHOICES_EVENT, STATUS_CHOICES, SEATING_CHOICES, 
    PHASE_CHOICES, PO_CHOICES, TYPE_CHOICES_TASK, PRIORITY_CHOICES # Task 확장 필드 상수 추가
)


# ========================================================
# 1. [초기 생성용] 프로젝트 생성 폼 (Create) 
# ========================================================
class EventForm(forms.ModelForm):
    # event_type 필드를 명시적으로 models.TYPE_CHOICES_EVENT를 사용하여 정의
    event_type = forms.ChoiceField(
        choices=TYPE_CHOICES_EVENT,
        label='행사 종류',
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    
    class Meta:
        model = Event
        fields = ['title', 'client_name', 'venue_name', 'budget', 'date', 'event_type']
        
        labels = {
            'title': '프로젝트 명',
            'client_name': '클라이언트',
            'venue_name': '장소명',
            'budget': '총 예산(원)',
            'date': '행사 날짜',
        }
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'style': 'width: 100%;'}),
            'client_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '예: 삼성전자'}),
            'venue_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '예: 코엑스 그랜드볼룸'}),
            'budget': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '숫자만 입력'}),
            'date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
        }

# ========================================================
# 2. [Tab 1용] 개요 및 재무 관리 폼 (Dashboard) 
# ========================================================
class EventOverviewForm(forms.ModelForm):
    # status 필드를 명시적으로 models.STATUS_CHOICES를 사용하여 정의
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        label='진행 상태',
        widget=forms.Select(attrs={'class': 'form-input', 'style': 'font-weight:bold; color:#00ff00;'})
    )
    
    class Meta:
        model = Event
        fields = ['title', 'client_name', 'venue_name', 'date', 'status', 'budget', 'expected_cost']
        
        labels = {
            'title': '프로젝트 명',
            'client_name': '클라이언트',
            'venue_name': '장소명',
            'date': '행사 날짜',
            'budget': '매출 (총 예산)',
            'expected_cost': '예상 지출', 
        }
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'client_name': forms.TextInput(attrs={'class': 'form-input'}),
            'venue_name': forms.TextInput(attrs={'class': 'form-input'}),
            'date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'budget': forms.NumberInput(attrs={'class': 'form-input'}),
            'expected_cost': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '지출 예상액 입력'}),
        }

# ========================================================
# 3. [Tab 2용] 공간 설계 폼 (Space Design) 
# ========================================================
class EventSpaceForm(forms.ModelForm):
    # seating_type 필드를 명시적으로 models.SEATING_CHOICES를 사용하여 정의
    seating_type = forms.ChoiceField(
        choices=SEATING_CHOICES,
        label='객석 배치',
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    
    class Meta:
        model = Event
        fields = [
            'venue_width', 'venue_depth', 'venue_height', 
            'has_stage', 'stage_width', 'stage_depth', 'stage_height',
            'seating_type', 'table_gap', 'has_virgin_road', 'has_foh', 
            'has_sound', 'has_lighting', 'has_screen', 'has_booth', 'has_print'
        ]
        
        labels = {
            'seating_type': '객석 배치',
            'venue_width': '공간 가로(m)',
            'venue_depth': '공간 깊이(m)',
            'venue_height': '천장 높이(m)',
            'stage_width': '무대 가로(m)',
            'stage_depth': '무대 깊이(m)',
            'stage_height': '무대 높이(m)',
            'table_gap': '객석 간격(m)',
        }
        
        widgets = {
            'seating_type': forms.Select(attrs={'class': 'form-input'}),
            'venue_width': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'venue_depth': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'venue_height': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'stage_width': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'stage_depth': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'stage_height': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'table_gap': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
        }

# ========================================================
# 4. 큐시트 폼 (기존 유지)
# ========================================================
class CueForm(forms.ModelForm):
    class Meta:
        model = Cue
        fields = ['order', 'content', 'duration', 'bgm', 'action']
        labels = {
            'order': 'No.', 'content': '진행 내용', 'duration': '시간(초)', 'bgm': 'BGM', 'action': '동작'
        }
        widgets = {
            'order': forms.NumberInput(attrs={'class': 'form-input', 'style': 'width: 50px;'}),
            'content': forms.TextInput(attrs={'class': 'form-input', 'style': 'width: 300px;'}),
            'duration': forms.NumberInput(attrs={'class': 'form-input', 'style': 'width: 60px;'}),
            'bgm': forms.TextInput(attrs={'class': 'form-input', 'style': 'width: 100px;'}),
            'action': forms.TextInput(attrs={'class': 'form-input', 'style': 'width: 60px;'}),
        }

# ========================================================
# 5. 일정 폼 (E.O.S 및 PMS+ 기능 반영하여 확장)
# ========================================================
class TaskForm(forms.ModelForm):
    # 💡 [필수 수정] task_category -> PHASE_CHOICES 사용
    task_category = forms.ChoiceField(
        choices=PHASE_CHOICES, 
        label='Task 단계',
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    # 💡 [신규] task_type 필드 추가
    task_type = forms.ChoiceField(
        choices=TYPE_CHOICES_TASK,
        label='Task 유형',
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    # 💡 [신규] priority 필드 추가
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        label='우선순위',
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    # po_status 필드를 명시적으로 models.PO_CHOICES를 사용하여 정의
    po_status = forms.ChoiceField(
        choices=PO_CHOICES,
        label='조달 상태',
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    
    class Meta:
        model = Task
        # 확장된 Task 모델의 필드를 모두 포함합니다.
        fields = [
            'content', 'deadline', 'task_category', 'task_type', 'priority', # 신규 필드 추가
            'is_external', 
            'planned_budget', 'actual_cost', 'vendor', 'po_status'
        ]
        
        widgets = {
            'content': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '업무 내용', 'style': 'width: 100%;'}),
            'deadline': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'is_external': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'planned_budget': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '책정 예산 (원)'}),
            'actual_cost': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '실 지출 (원)'}),
            'vendor': forms.Select(attrs={'class': 'form-input'}), # 협력업체 목록 자동 로딩
        }
        
        labels = {
            'content': '업무 내용',
            'deadline': '마감일',
            'task_category': 'Task 단계',
            'task_type': 'Task 유형',
            'priority': '우선순위',
            'is_external': '외주 업무',
            'planned_budget': '책정 예산',
            'actual_cost': '실 지출',
            'vendor': '담당 업체',
            'po_status': '조달 상태',
        }


# ========================================================
# 6. 신규 폼: 외주 관리 시스템용 폼 추가
# ========================================================

# A. 협력업체 등록 폼
class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = '__all__'

# B. 견적서 등록 폼
class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        # task는 views에서 context로 받아서 처리
        fields = ['vendor', 'quoted_amount', 'file']