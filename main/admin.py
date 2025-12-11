from django.contrib import admin
# .models에서 필요한 모델들을 임포트합니다.
# 💡 [필수 수정] Vendor, Quotation, PurchaseOrder 모델 임포트 추가
from .models import Event, Cue, Task, Vendor, Quotation, PurchaseOrder 

# [설정 1] 행사 상세 페이지에서 '할 일(Task)'을 같이 보여주기
class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    readonly_fields = ('content', 'deadline') # 자동 생성된 건 수정 못하게 (선택)

# [설정 2] 행사 상세 페이지에서 '큐시트(Cue)'를 같이 보여주기
class CueInline(admin.TabularInline):
    model = Cue
    extra = 1

# 💡 [신규] Task 상세 페이지에서 견적서 목록을 같이 보여주기 (조달 기능 확장)
class QuotationInline(admin.TabularInline):
    model = Quotation
    extra = 0
    fields = ('vendor', 'quoted_amount', 'is_selected') # 주요 필드만 노출
    readonly_fields = ('vendor',) # 견적 제출 업체는 수정 불가

# [설정 3] 행사 목록 페이지 꾸미기
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'date', 'author') # 목록에 보일 항목
    list_filter = ('event_type', 'date') # 우측 필터 메뉴
    inlines = [TaskInline, CueInline] # 상세 페이지에 위 2개(Task, Cue) 포함

# 💡 [신규] Task 상세 페이지 꾸미기 (Quotation Inline 추가)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('content', 'event', 'deadline', 'is_external', 'po_status')
    list_filter = ('is_external', 'po_status', 'task_category')
    inlines = [QuotationInline] # Task 상세 페이지에서 견적서를 관리

# [최종 등록] 장고에게 "이거 보여줘"라고 명령
admin.site.register(Event, EventAdmin)

# 💡 [수정] Task 모델 등록 시, 새로운 TaskAdmin 설정 적용
admin.site.register(Task, TaskAdmin) 

# ▼▼▼ [필수 추가] Vendor 및 조달 관련 모델 등록 ▼▼▼
admin.site.register(Vendor)
admin.site.register(Quotation)
admin.site.register(PurchaseOrder)