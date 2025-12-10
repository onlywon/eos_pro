from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta

# 1. 행사(Event) 테이블 - 통합 설계 데이터 포함
class Event(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, verbose_name="프로젝트명")
    
    # [관리 정보] (기존 항목 유지)
    client_name = models.CharField(max_length=100, verbose_name="클라이언트(발주처)", default="", blank=True)
    venue_name = models.CharField(max_length=100, verbose_name="장소명", default="", blank=True)
    budget = models.IntegerField(default=0, verbose_name="총 예산(원)")
    
    # ▼▼▼ [신규 추가] 상황실용 데이터 (지출, 진행상태) ▼▼▼
    expected_cost = models.IntegerField(default=0, verbose_name="예상 지출(비용)")
    
    STATUS_CHOICES = [
        ('inquiry', '🟡 문의/접수'),
        ('design', '🔵 디자인/견적 중'),
        ('confirmed', '🟢 계약 확정 (준비 중)'),
        ('onsite', '🔴 현장 운영 중'),
        ('done', '⚪ 행사 종료'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inquiry', verbose_name="진행 상태")
    # ▲▲▲ 추가 끝 ▲▲▲

    date = models.DateField(verbose_name="행사일")
    created_at = models.DateTimeField(auto_now_add=True)

    # [1] 행사 성격 (5가지)
    TYPE_CHOICES = [
        ('general', '일반 행사 (General)'),
        ('conference', '컨퍼런스/세미나 (Conference)'),
        ('concert', '공연/콘서트 (Concert)'),
        ('exhibition', '전시회 (Exhibition)'),
        ('festival', '축제/이벤트 (Festival)'),
    ]
    event_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='general', verbose_name="행사 유형")

    # [2] 공간 데이터 (Venue)
    venue_width = models.FloatField(default=20.0, verbose_name="공간 가로(m)")
    venue_depth = models.FloatField(default=40.0, verbose_name="공간 깊이(m)")
    venue_height = models.FloatField(default=5.0, verbose_name="천고(m)")

    # [3] 무대 데이터 (Stage)
    has_stage = models.BooleanField(default=True, verbose_name="[장비] 무대 사용")
    stage_width = models.FloatField(default=14.4, verbose_name="무대 가로(m)")
    stage_depth = models.FloatField(default=4.8, verbose_name="무대 깊이(m)")
    stage_height = models.FloatField(default=0.9, verbose_name="무대 높이(m)")

    # [4] 세부 설계 옵션
    table_gap = models.FloatField(default=3.0, verbose_name="객석 간격(m)")
    
    # [객석 배치 타입]
    SEATING_CHOICES = [
        ('banquet', '연회식 (Round Table)'),
        ('theater', '극장식 (Theater / Chairs only)'),
        ('classroom', '강의식 (Classroom / Table & Chair)'),
    ]
    seating_type = models.CharField(max_length=20, choices=SEATING_CHOICES, default='banquet', verbose_name="객석 배치 유형")

    has_virgin_road = models.BooleanField(default=False, verbose_name="버진로드 포함")
    has_foh = models.BooleanField(default=True, verbose_name="FOH(콘솔) 배치")

    # [5] 기타 장비 사용 여부
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

# 3. 할 일 (기존 유지)
class Task(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tasks')
    content = models.CharField(max_length=200, verbose_name="할 일 내용")
    deadline = models.DateField(verbose_name="마감일")
    is_done = models.BooleanField(default=False, verbose_name="완료 여부")

    def __str__(self):
        return f"[{'완료' if self.is_done else '미완'}] {self.content}"

# 4. 자동 생성 엔진 (Signal)
@receiver(post_save, sender=Event)
def create_default_tasks(sender, instance, created, **kwargs):
    if created:
        tasks = []
        d_day = instance.date
        
        # 공통 업무
        tasks.append(Task(event=instance, content="Kick-off 및 현장 답사", deadline=d_day - timedelta(days=30)))
        tasks.append(Task(event=instance, content="도면 및 3D 시안 확정", deadline=d_day - timedelta(days=14)))
        
        # 공연/세미나 특화
        if instance.event_type in ['concert', 'festival']:
            tasks.append(Task(event=instance, content="큐시트 & 리허설 계획 수립", deadline=d_day - timedelta(days=7)))
            tasks.append(Task(event=instance, content="음원/영상 소스 최종 확인", deadline=d_day - timedelta(days=3)))
        else:
            tasks.append(Task(event=instance, content="발표자료 취합 및 리허설", deadline=d_day - timedelta(days=3)))
            
        Task.objects.bulk_create(tasks)