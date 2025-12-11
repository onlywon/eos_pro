from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta
import locale # 재무 계산을 위해 locale 모듈 임포트 (views.py에서도 사용됨)
from django.db.models import Sum # Task 재무 연동에 필요하므로 명시적으로 추가

# =======================================================
# 💡 [필수 수정] 모든 CHOICES 상수를 모델 정의보다 위로 이동
# =======================================================

# 1. Event TYPE CHOICES (행사 유형)
TYPE_CHOICES_EVENT = [
    ('exhibition', '1. 전시회 (Exhibition)'),
    ('event', '2. 이벤트/운영 (Event/Operation)'),
    ('conference', '3. 컨퍼런스/세미나 (Conference)'),
    ('ceremony', '4. 기념식/시상식 (Ceremony)'),
    ('festival', '5. 지역 축제 (Regional Festival)'),
    ('promotion', '6. 홍보/브랜딩 (Promotion)'),
]

# 2. Event STATUS CHOICES (진행 상태)
STATUS_CHOICES = [
    ('inquiry', '🟡 문의/접수'),
    ('design', '🔵 디자인/견적 중'),
    ('confirmed', '🟢 계약 확정 (준비 중)'),
    ('onsite', '🔴 현장 운영 중'),
    ('done', '⚪ 행사 종료'),
]

# 3. Event SEATING CHOICES (객석 배치 유형)
SEATING_CHOICES = [
    ('banquet', '연회식 (Round Table)'),
    ('theater', '극장식 (Theater / Chairs only)'),
    ('classroom', '강의식 (Classroom / Table & Chair)'),
]

# 4. Task PHASE CHOICES (업무 단계 - WBS의 주요 단계로 확장)
PHASE_CHOICES = [
    ('PLANNING', '기획'),
    ('DESIGN', '디자인'),
    ('PREPARATION', '제작/준비'),
    ('EXECUTION', '실행/현장'),
    ('CLOSING', '정산/마감'),
]

# 5. Task TYPE CHOICES (업무 유형 - 연동 기능 기준)
TYPE_CHOICES_TASK = [
    ('GENERAL', '일반 업무'),
    ('PROCUREMENT', '발주/외주'),
    ('CHECKLIST', '점검/체크리스트'),
]

# 6. Task PRIORITY CHOICES (우선순위)
PRIORITY_CHOICES = [
    ('LOW', '낮음'),
    ('MEDIUM', '보통'),
    ('HIGH', '높음'),
]

# 7. Task PO CHOICES (조달 상태)
PO_CHOICES = [
    ('ready', '견적 요청 준비'),
    ('bidding', '입찰/견적 비교 중'),
    ('contracted', '계약 완료'),
    ('po_issued', '발주서 생성 완료'),
]
# =======================================================


# A. 협력업체 (Vendor) - [신규]
class Vendor(models.Model):
    name = models.CharField(max_length=100, verbose_name="업체명")
    business_number = models.CharField(max_length=20, unique=True, verbose_name="사업자등록번호")
    contact_person = models.CharField(max_length=50, verbose_name="담당자")
    phone_number = models.CharField(max_length=20, verbose_name="연락처")
    address = models.CharField(max_length=255, verbose_name="주소", blank=True)

    def __str__(self):
        return self.name

# 1. 행사(Event) 테이블 - 통합 설계 데이터 포함
class Event(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, verbose_name="프로젝트명")
    
    # [관리 정보] (기존 항목 유지)
    client_name = models.CharField(max_length=100, verbose_name="클라이언트(발주처)", default="", blank=True)
    venue_name = models.CharField(max_length=100, verbose_name="장소명", default="", blank=True)
    budget = models.IntegerField(default=0, verbose_name="총 예산(원)")
    
    # [상황실용 데이터] (기존 항목 유지)
    expected_cost = models.IntegerField(default=0, verbose_name="예상 지출(비용)")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inquiry', verbose_name="진행 상태")

    date = models.DateField(verbose_name="행사일")
    created_at = models.DateTimeField(auto_now_add=True)

    # [1] 행사 성격 (6가지로 확장)
    event_type = models.CharField(max_length=20, choices=TYPE_CHOICES_EVENT, default='event', verbose_name="행사 유형")

    # (이하 공간/무대/장비 데이터는 기존 코드와 동일하게 유지)
    venue_width = models.FloatField(default=20.0, verbose_name="공간 가로(m)")
    venue_depth = models.FloatField(default=40.0, verbose_name="공간 깊이(m)")
    venue_height = models.FloatField(default=5.0, verbose_name="천고(m)")
    has_stage = models.BooleanField(default=True, verbose_name="[장비] 무대 사용")
    stage_width = models.FloatField(default=14.4, verbose_name="무대 가로(m)")
    stage_depth = models.FloatField(default=4.8, verbose_name="무대 깊이(m)")
    stage_height = models.FloatField(default=0.9, verbose_name="무대 높이(m)")
    table_gap = models.FloatField(default=3.0, verbose_name="객석 간격(m)")
    
    seating_type = models.CharField(max_length=20, choices=SEATING_CHOICES, default='banquet', verbose_name="객석 배치 유형")

    has_virgin_road = models.BooleanField(default=False, verbose_name="버진로드 포함")
    has_foh = models.BooleanField(default=True, verbose_name="FOH(콘솔) 배치")
    has_sound = models.BooleanField(default=True, verbose_name="[장비] 음향 사용")
    has_lighting = models.BooleanField(default=True, verbose_name="[장비] 조명 사용")
    has_screen = models.BooleanField(default=False, verbose_name="[장비] 영상 사용")
    has_booth = models.BooleanField(default=False, verbose_name="[시설] 전시 부스")
    has_print = models.BooleanField(default=False, verbose_name="[제작] 인쇄물")

    def __str__(self):
        return f"[{self.get_event_type_display()}] {self.title}"

# 2. 큐시트 (기존 유지)
class Cue(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    order = models.IntegerField()
    content = models.CharField(max_length=500)
    duration = models.IntegerField(default=0)
    bgm = models.CharField(max_length=200, blank=True)
    action = models.CharField(max_length=50, default='Play')

    def __str__(self):
        return f"[{self.order}] {self.content}"

# 3. 할 일 (Task) - E.O.S 및 PMS+ 확장
class Task(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tasks')
    content = models.CharField(max_length=200, verbose_name="할 일 내용")
    deadline = models.DateField(verbose_name="마감일")
    is_done = models.BooleanField(default=False, verbose_name="완료 여부")

    # ▼▼▼ [필수 추가] Task 계층 구조 (WBS)를 위한 부모-자식 관계 설정 ▼▼▼
    parent = models.ForeignKey(
        'self', # 자기 자신(Task)을 참조
        on_delete=models.SET_NULL, # 부모 Task가 삭제되어도 하위 Task는 남김
        null=True,
        blank=True,
        related_name='subtasks', # 하위 Task를 가져올 때 사용되는 이름 (task.subtasks.all())
        verbose_name='상위 Task'
    )
    
    # ▼▼▼ [PMS+ 확장 필드] ▼▼▼
    
    # 1. 분류 (WBS 단계) - PHASE_CHOICES로 변경 및 통합
    task_category = models.CharField(
        max_length=20, 
        choices=PHASE_CHOICES, 
        default='PLANNING', 
        verbose_name="Task 단계"
    )
    
    # 2. Task 유형 (신규 추가) - TYPE_CHOICES_TASK 사용
    task_type = models.CharField(
        max_length=20, 
        choices=TYPE_CHOICES_TASK, 
        default='GENERAL', 
        verbose_name="Task 유형"
    )
    
    # 3. 우선순위 (신규 추가) - PRIORITY_CHOICES 사용
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_CHOICES, 
        default='MEDIUM', 
        verbose_name="우선순위"
    )
    
    # 4. 예산/정산 기능
    planned_budget = models.IntegerField(default=0, verbose_name="책정 예산(원)")
    actual_cost = models.IntegerField(default=0, verbose_name="실 지출(원)")
    
    # 5. 외주/협업 기능
    is_external = models.BooleanField(default=False, verbose_name="외주 업무 여부")
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="담당 협력업체") 
    
    # 6. 발주/계약 상태
    po_status = models.CharField(max_length=20, choices=PO_CHOICES, default='ready', verbose_name="조달 상태")

    def __str__(self):
        # Task에 parent가 있으면 계층을 표시
        if self.parent:
            return f"[{self.get_task_category_display()}] {self.content} (-> {self.parent.content})"
        return f"[{self.get_task_category_display()}] {self.content}"


# B. 견적서/입찰 (Quotation) - [신규]
class Quotation(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name="관련 Task") 
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, verbose_name="제출 업체")
    quoted_amount = models.IntegerField(verbose_name="견적 금액(원)")
    is_selected = models.BooleanField(default=False, verbose_name="선정 여부")
    file = models.FileField(upload_to='quotations/', verbose_name="견적 파일", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.task.content} - {self.vendor.name}"

# C. 발주서/전자 계약 (Purchase Order - PO) - [신규]
class PurchaseOrder(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name="관련 Task")
    vendor = models.ForeignKey(Vendor, on_delete=models.RESTRICT, verbose_name="계약 업체")
    contract_amount = models.IntegerField(verbose_name="계약 금액(원)")
    is_signed = models.BooleanField(default=False, verbose_name="전자 계약 완료")
    po_date = models.DateField(auto_now_add=True, verbose_name="발주 일자")
    
    def __str__(self):
        return f"PO-{self.id}: {self.task.content}"

# 4. 자동 생성 엔진 (Signal)
@receiver(post_save, sender=Event)
def create_default_tasks(sender, instance, created, **kwargs):
    if created:
        d_day = instance.date
        
        # 💡 [업데이트] 프로젝트 유형별 표준 Task 정의 (데이터 구조 변경)
        # 튜플 형식: (phase, task_type, content, days_before, is_external, planned_budget)
        STANDARD_TASKS = {
            'general': [
                ('PLANNING', 'GENERAL', "프로젝트 Kick-off 및 현장 답사", 30, False, 100000),
                ('PLANNING', 'GENERAL', "기본 도면 및 3D 시안 확정", 14, False, 0),
                ('EXECUTION', 'GENERAL', "현장 장비 리스트 최종 확정", 7, False, 0),
                ('CLOSING', 'GENERAL', "정산 마감 서류 취합", -7, False, 0), # 행사 종료 후 -7일
            ],
            'exhibition': [
                ('PLANNING', 'GENERAL', "전시회 부스 위치 및 인허가 신고", 45, False, 0),
                ('DESIGN', 'GENERAL', "전시 콘텐츠 및 브랜딩 가이드 확정", 25, False, 0),
                ('PREPARATION', 'PROCUREMENT', "부스 디자인 시공/철거 외주 발주", 18, True, 15000000), # 외주, 예산 반영
                ('EXECUTION', 'GENERAL', "운영요원 교육 및 배치", 5, False, 500000),
                ('CLOSING', 'GENERAL', "참가 업체 정산 마감", -10, False, 0),
            ],
            'conference': [
                ('PLANNING', 'GENERAL', "연사 확정 및 계약 진행", 60, False, 0),
                ('PREPARATION', 'GENERAL', "발표자료 최종 취합 및 리허설", 7, False, 0),
                ('PREPARATION', 'PROCUREMENT', "음향/영상 시스템 설치 외주 발주", 10, True, 5000000),
                ('PREPARATION', 'GENERAL', "참석자 명찰/자료 인쇄", 5, False, 300000),
                ('CLOSING', 'GENERAL', "참가자 만족도 조사 발송", -3, False, 0),
            ],
            'ceremony': [
                ('PLANNING', 'GENERAL', "초청 대상자 명단 확정", 30, False, 0),
                ('DESIGN', 'GENERAL', "시상식 대본 및 시퀀스 확정", 15, False, 0),
                ('PREPARATION', 'PROCUREMENT', "무대/조명 디자인 시공 외주 발주", 10, True, 7000000),
                ('PREPARATION', 'PROCUREMENT', "사회자 및 공연팀 섭외/계약", 8, True, 4000000),
                ('CLOSING', 'GENERAL', "선물/기념품 정산", -5, False, 0),
            ],
            'festival': [
                ('PLANNING', 'GENERAL', "지자체 인허가 및 안전 보험 등록", 60, False, 0),
                ('PLANNING', 'PROCUREMENT', "라인업 확정 및 출연료 계약", 50, True, 30000000), # 외주, 예산 반영
                ('PREPARATION', 'PROCUREMENT', "메인 무대 설치 및 현장 통제 외주 발주", 15, True, 10000000),
                ('EXECUTION', 'GENERAL', "MD 부스 설치 및 판매 시스템 점검", 7, False, 0),
                ('CLOSING', 'GENERAL', "매출 및 비용 정산 보고서 작성", -15, False, 0),
            ],
            'promotion': [
                ('PLANNING', 'GENERAL', "캠페인 목표 및 KPI 설정", 20, False, 0),
                ('DESIGN', 'PROCUREMENT', "홍보 콘텐츠 (영상/이미지) 제작 외주 발주", 15, True, 3000000),
                ('EXECUTION', 'GENERAL', "온라인 광고 채널 확정 및 운영 시작", 7, False, 0),
                ('CLOSING', 'GENERAL', "광고 효율 분석 및 보고서 작성", -10, False, 0),
            ],
        }
        
        # 현재 이벤트 유형에 맞는 표준 Task 목록 선택
        tasks_to_create = STANDARD_TASKS.get(instance.event_type, STANDARD_TASKS['general'])
        
        tasks = []
        # 💡 [업데이트] 튜플 구조 변경에 맞게 언패킹 변수 수정 (phase, task_type 추가)
        for phase, task_type, content, days_before, is_external, planned_budget in tasks_to_create:
            # deadline이 행사일(d_day)을 기준으로 days_before만큼 앞선 날짜로 설정
            tasks.append(
                Task(
                    event=instance,
                    content=content,
                    deadline=d_day - timedelta(days=days_before),
                    task_category=phase, # Task 단계 (PLANNING, DESIGN 등)
                    task_type=task_type, # Task 유형 (GENERAL, PROCUREMENT 등)
                    is_external=is_external,
                    planned_budget=planned_budget,
                    po_status='ready' if is_external else 'ready',
                    # 💡 [신규] 긴급 Task는 HIGH 우선순위 자동 부여
                    priority='HIGH' if days_before <= 7 else 'MEDIUM'
                )
            )
            
        Task.objects.bulk_create(tasks)
        
        # 💡 [재무 연동 로직] Task의 초기 예산을 Event 예상 지출에 합산
        total_planned_budget = sum(task.planned_budget for task in tasks)
        
        # 예상 지출(expected_cost) 필드는 Event의 Task 전체 예산 합계로 자동 업데이트
        instance.expected_cost = total_planned_budget 
        
        # DB에 반영 (시그널이 무한 루프에 빠지지 않도록 update_fields 지정)
        instance.save(update_fields=['expected_cost'])