from django.contrib import admin
from .models import Event, Cue, Task

# [설정 1] 행사 상세 페이지에서 '할 일(Task)'을 같이 보여주기
class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    readonly_fields = ('content', 'deadline') # 자동 생성된 건 수정 못하게 (선택)

# [설정 2] 행사 상세 페이지에서 '큐시트(Cue)'를 같이 보여주기
class CueInline(admin.TabularInline):
    model = Cue
    extra = 1

# [설정 3] 행사 목록 페이지 꾸미기
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'date', 'author') # 목록에 보일 항목
    list_filter = ('event_type', 'date') # 우측 필터 메뉴
    inlines = [TaskInline, CueInline] # 상세 페이지에 위 2개(Task, Cue) 포함

# [최종 등록] 장고에게 "이거 보여줘"라고 명령
admin.site.register(Event, EventAdmin)
admin.site.register(Task)