from django import forms
from .models import Cue, Event, Task

# ========================================================
# 1. [초기 생성용] 프로젝트 생성 폼 (Create)
# ========================================================
class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        # 생성 시점에는 핵심 정보만 입력받습니다.
        fields = ['title', 'client_name', 'venue_name', 'budget', 'date', 'event_type']
        
        labels = {
            'title': '프로젝트 명',
            'client_name': '클라이언트',
            'venue_name': '장소명',
            'budget': '총 예산(원)',
            'date': '행사 날짜',
            'event_type': '행사 종류',
        }
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'style': 'width: 100%;'}),
            'client_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '예: 삼성전자'}),
            'venue_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '예: 코엑스 그랜드볼룸'}),
            'budget': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '숫자만 입력'}),
            'date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'event_type': forms.Select(attrs={'class': 'form-input'}),
        }

# ========================================================
# 2. [Tab 1용] 개요 및 재무 관리 폼 (Dashboard) - 신규
# ========================================================
class EventOverviewForm(forms.ModelForm):
    class Meta:
        model = Event
        # 상황실에서 수정할 정보들 (진행상태, 비용 포함)
        fields = ['title', 'client_name', 'venue_name', 'date', 'status', 'budget', 'expected_cost']
        
        labels = {
            'title': '프로젝트 명',
            'client_name': '클라이언트',
            'venue_name': '장소명',
            'date': '행사 날짜',
            'status': '진행 상태',       # [New]
            'budget': '매출 (총 예산)',
            'expected_cost': '예상 지출', # [New]
        }
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'client_name': forms.TextInput(attrs={'class': 'form-input'}),
            'venue_name': forms.TextInput(attrs={'class': 'form-input'}),
            'date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            # 상태 변경은 눈에 띄게 스타일링
            'status': forms.Select(attrs={'class': 'form-input', 'style': 'font-weight:bold; color:#00ff00;'}),
            'budget': forms.NumberInput(attrs={'class': 'form-input'}),
            'expected_cost': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '지출 예상액 입력'}),
        }

# ========================================================
# 3. [Tab 2용] 공간 설계 폼 (Space Design) - 분리됨
# ========================================================
class EventSpaceForm(forms.ModelForm):
    class Meta:
        model = Event
        # 공간/무대/객석 관련 필드만 모음
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
# 5. 일정 폼 (기존 유지)
# ========================================================
class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['content', 'deadline']
        widgets = {
            'content': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '추가할 업무 내용', 'style': 'width: 70%;'}),
            'deadline': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
        }