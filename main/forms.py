from django import forms
from .models import Cue, Event, Task # Task 모델 추가

# 1. [새 프로젝트 등록용] 신청서
class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title', 'date', 'event_type', 
            'seating_type', # [신규] 객석 배치 타입 추가
            'venue_width', 'venue_depth', 'venue_height', 
            'has_stage', 'stage_width', 'stage_depth', 'stage_height',
            'table_gap', 'has_virgin_road', 'has_foh', 
            'has_sound', 'has_lighting', 'has_screen', 'has_booth', 'has_print'
        ]
        
        # 대표님이 작성하신 라벨 설정 그대로 유지
        labels = {
            'title': '프로젝트 명',
            'date': '행사 날짜',
            'event_type': '행사 종류',
            'seating_type': '객석 배치', # [신규]
            'venue_width': '공간 가로(m)',
            'venue_depth': '공간 깊이(m)',
            'venue_height': '천장 높이(m)',
            'stage_width': '무대 가로(m)',
            'stage_depth': '무대 깊이(m)',
            'stage_height': '무대 높이(m)',
            'table_gap': '객석 간격(m)',
        }
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'style': 'width: 100%;'}),
            'date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'event_type': forms.Select(attrs={'class': 'form-input'}),
            'seating_type': forms.Select(attrs={'class': 'form-input'}), # [신규]
            
            # 숫자 입력칸 스타일 (대표님 설정 유지)
            'venue_width': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'venue_depth': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'venue_height': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'stage_width': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'stage_depth': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'stage_height': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'table_gap': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
        }

# 2. [큐시트 입력용] 입력창 (대표님 스타일 100% 유지)
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

# 3. [신규] 일정 추가용 폼 (새로 추가된 부분)
class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['content', 'deadline']
        widgets = {
            'content': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '추가할 업무 내용', 'style': 'width: 70%;'}),
            'deadline': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
        }