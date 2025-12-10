from django import forms
from .models import Cue, Event

# 1. [새 프로젝트 등록용] 신청서
class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'date', 'event_type', 
                  'has_stage', 'has_sound', 'has_lighting', 'has_screen', 'has_booth', 'has_print',
                  'stage_width', 'stage_depth', 'stage_height']
        
        labels = {
            'title': '프로젝트 명',
            'date': '행사 날짜',
            'event_type': '행사 종류',
            'stage_width': '무대 가로(m)',
            'stage_depth': '무대 깊이(m)',
            'stage_height': '무대 높이(m)',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'style': 'width: 100%;'}),
            'date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}), 
            'event_type': forms.Select(attrs={'class': 'form-input'}),
        }
        from django import forms
from .models import Cue, Event

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title', 'date', 'event_type', # 기본
            'venue_width', 'venue_depth', 'venue_height', # 공간
            'has_stage', 'stage_width', 'stage_depth', 'stage_height', # 무대
            'table_gap', 'has_virgin_road', 'has_foh', # 세부 옵션
            'has_sound', 'has_lighting', 'has_screen', 'has_booth', 'has_print' # 장비
        ]
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'event_type': forms.Select(attrs={'class': 'form-input'}),
            # 숫자 입력칸 스타일 통일
            'venue_width': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'venue_depth': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'venue_height': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'stage_width': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'stage_depth': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'stage_height': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'table_gap': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
        }

# 2. [큐시트 입력용] 입력창
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