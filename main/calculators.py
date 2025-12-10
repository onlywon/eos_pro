import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import urllib, base64

# [중요] 서버에서 GUI 에러 방지를 위해 백엔드 설정
plt.switch_backend('Agg')

# ==========================================
# 1. 계산 로직
# ==========================================

def calculate_space(event):
    v_w = event.venue_width
    v_d = event.venue_depth
    s_w = event.stage_width
    
    # [업그레이드] 객석 타입에 따른 간격 및 단위 면적 설정
    mode = getattr(event, 'seating_type', 'banquet') # 기본값 안전장치
    
    if mode == 'theater': # 극장식 (의자만)
        unit_w, unit_d = 0.5, 0.5 # 의자 크기
        gap_w, gap_d = 0.1, 0.5   # 좌우, 앞뒤 간격
        pax_per_unit = 1
        unit_name = "Seats"
    elif mode == 'classroom': # 강의식 (책상+의자)
        unit_w, unit_d = 1.5, 0.6 # 책상 크기
        gap_w, gap_d = 0.2, 1.0
        pax_per_unit = 2 # 책상 1개당 2명
        unit_name = "Tables"
    else: # banquet (기존 원형 테이블)
        unit_w, unit_d = 2.0, 2.0
        gap_w, gap_d = event.table_gap, event.table_gap
        pax_per_unit = 8
        unit_name = "Tables"

    # 가용 면적 계산 (무대 및 FOH 제외)
    avail_w = v_w - 2.0
    start_y = v_d - event.stage_depth - 4.0
    end_y = 4.0 if event.has_foh else 2.0
    avail_d = start_y - end_y
    
    report = {'warnings': [], 'infos': []}
    
    # 스크린 공간 체크 (기존 로직)
    screen_space = (v_w - s_w) / 2
    if screen_space >= 2.5:
        report['infos'].append(f"✅ 무대 양옆 {screen_space:.1f}m 확보 (200인치 가능)")
    elif screen_space < 1.0:
        report['warnings'].append(f"⚠️ 무대 좌우 협소 ({screen_space:.1f}m)")

    if avail_w < 0 or avail_d < 0:
        report['warnings'].append("⚠️ 공간이 너무 좁아 객석 배치가 불가능합니다.")
        report['pax'] = 0
        report['table_count'] = 0
        return report

    # 수량 계산 (격자 방식)
    cols = int(avail_w / (unit_w + gap_w))
    rows = int(avail_d / (unit_d + gap_d))
    
    raw_count = cols * rows
    if event.has_virgin_road: 
        raw_count -= rows 
        
    final_count = max(0, int(raw_count))
    pax = final_count * pax_per_unit
    
    report['table_count'] = final_count
    report['pax'] = pax
    report['infos'].append(f"✅ 배치 모드: {event.get_seating_type_display()}")
    report['infos'].append(f"✅ 총 {final_count} {unit_name} 배치")
    
    return report

def calculate_audio(event):
    v_d = event.venue_depth
    v_w = event.venue_width
    
    # [유지] 행사 종류 매핑
    is_perf = event.event_type in ['concert', 'festival']
    
    specs = {}
    
    if v_d > 25 and is_perf:
        sys_type = "Line Array System"
        array_qty = max(4, int(v_d / 5))
        specs['main'] = f"Compact Line Array {array_qty}통 x 2조"
        specs['main_type'] = 'array'
    else:
        sys_type = "Point Source System"
        specs['main'] = "12~15 inch Point Source x 2조"
        specs['main_type'] = 'point'
        
    if v_d >= 20:
        delay_pos = v_d * 0.55
        delay_ms = (delay_pos / 340) * 1000 + 15
        specs['delay'] = f"10~12 inch PS 1조 ({delay_pos:.1f}m)"
        specs['delay_setting'] = f"{delay_ms:.1f} ms"
        specs['has_delay'] = True
        specs['delay_pos'] = delay_pos
    else:
        specs['delay'] = "불필요"
        specs['delay_setting'] = "-"
        specs['has_delay'] = False
        specs['delay_pos'] = 0
        
    if is_perf: specs['sub'] = f"18 inch Dual Sub {4 if v_w > 20 else 2}통"
    else: specs['sub'] = "18 inch Single/Dual 2통"
        
    return {'type': sys_type, 'specs': specs}

class LightingEngine:
    def __init__(self, event):
        self.w = event.stage_width
        self.d = event.stage_depth
        self.is_perf = event.event_type in ['concert', 'festival']
        
    def get_patch_data(self):
        interval = 1.5 if self.is_perf else 3.0
        num_beams = math.ceil(self.w / interval)
        num_wash = math.ceil(self.w / 2.0)
        num_spots = math.ceil(self.w / 3.0)
        if num_spots % 2 != 0: num_spots += 1
        
        patch_list = []
        addr = 1
        layout = []
        
        # Beam
        start_x = -(self.w/2) + (self.w/(num_beams+1))
        for i in range(num_beams):
            x = start_x + (i * (self.w/(num_beams+1)))
            patch_list.append({'id': f'B{i+1}', 'fixture': 'Beam 350W', 'addr': addr, 'ch': 16, 'watt': 350})
            layout.append({'type': 'Beam', 'x': x, 'y': self.d/2 - 0.5, 'color': 'blue'})
            addr += 18
            
        # Wash
        start_x_w = -(self.w/2) + (self.w/(num_wash+1))
        for i in range(num_wash):
            x = start_x_w + (i * (self.w/(num_wash+1)))
            patch_list.append({'id': f'W{i+1}', 'fixture': 'LED Wash', 'addr': addr, 'ch': 8, 'watt': 180})
            layout.append({'type': 'Wash', 'x': x, 'y': self.d/2 - 0.8, 'color': 'green'})
            addr += 10

        # Spot
        for i in range(num_spots):
            offset = (i - (num_spots/2) + 0.5) * 2.5
            patch_list.append({'id': f'S{i+1}', 'fixture': 'Ellipsoidal', 'addr': addr, 'ch': 1, 'watt': 750})
            layout.append({'type': 'Spot', 'x': offset, 'y': -(self.d/2) - 3.0, 'color': 'orange'})
            addr += 1
            
        # [업그레이드] 전력 계산 및 발전차 추천 로직 추가
        total_watts = sum([p['watt'] for p in patch_list])
        # 기본 부하(조명) + 음향/영상 여유율 가산
        margin = 10000 if self.is_perf else 3000 
        total_kw = round((total_watts + margin) / 1000, 1)
        
        if total_kw < 10: gen_info = f"⚡ {total_kw}kW (하우스 전력 사용 권장)"
        elif total_kw < 50: gen_info = f"⚡ {total_kw}kW (발전차 50kW 1대)"
        else: gen_info = f"⚡ {total_kw}kW (발전차 100kW 1대)"

        # 리턴값이 4개로 늘어남 (패치, 전력, 레이아웃, 발전차정보)
        return patch_list, total_kw, layout, gen_info

# ==========================================
# 2. 시각화 로직 (Drawing Engine)
# ==========================================

def get_image():
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', facecolor='#252526')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = urllib.parse.quote(string)
    plt.close()
    return uri

def draw_space(event):
    v_w, v_d = event.venue_width, event.venue_depth
    s_w, s_d = event.stage_width, event.stage_depth
    
    fig, ax = plt.subplots(figsize=(6, v_d/v_w*6))
    ax.set_xlim(0, v_w)
    ax.set_ylim(0, v_d)
    ax.set_facecolor('#f0f0f0')
    
    # 무대
    stage_y = v_d - s_d - 1.0
    ax.add_patch(patches.Rectangle(((v_w-s_w)/2, stage_y), s_w, s_d, color='#333'))
    ax.text(v_w/2, stage_y + s_d/2, "STAGE", color='white', ha='center', va='center', fontweight='bold')
    
    # [업그레이드] 배치 타입별 시각화 분기
    mode = getattr(event, 'seating_type', 'banquet')
    start_y = stage_y - 4.0
    end_y = 4.0 if event.has_foh else 2.0
    
    # 그리기 설정 (크기, 모양)
    if mode == 'theater': # 극장식
        unit_w, unit_d, gap_w, gap_d = 0.5, 0.5, 0.1, 0.5
        draw_shape = 'rect'
    elif mode == 'classroom': # 강의식
        unit_w, unit_d, gap_w, gap_d = 1.5, 0.6, 0.2, 1.0
        draw_shape = 'rect'
    else: # Banquet
        unit_w, unit_d = 0.9, 0.9 # 반지름 느낌
        gap_w, gap_d = event.table_gap, event.table_gap
        draw_shape = 'circle'

    # 중앙 정렬 계산
    cols = int((v_w - 3.0) / (unit_w + gap_w)) if mode != 'banquet' else int((v_w - 3.0) // gap_w)
    rows = int((start_y - end_y) / (unit_d + gap_d)) if mode != 'banquet' else int((start_y - end_y) // gap_d)
    
    total_row_width = cols * (unit_w + gap_w) - gap_w if mode != 'banquet' else cols * gap_w
    start_x = (v_w - total_row_width) / 2
    
    for r in range(rows):
        curr_y = start_y - (r * (unit_d + gap_d)) if mode != 'banquet' else start_y - (r * gap_d)
        for c in range(cols):
            curr_x = start_x + (c * (unit_w + gap_w)) if mode != 'banquet' else (v_w - (cols-1)*gap_w)/2 + c*gap_w
            
            # 버진로드 체크
            if event.has_virgin_road and abs(curr_x + unit_w/2 - v_w/2) < 1.0: continue
            
            if draw_shape == 'rect':
                color = '#888' if mode == 'theater' else '#8d6e63'
                ax.add_patch(patches.Rectangle((curr_x, curr_y), unit_w, unit_d, color=color))
            else:
                ax.add_patch(patches.Circle((curr_x, curr_y), 0.8, facecolor='white', edgecolor='#555'))
                
    if event.has_foh:
        ax.add_patch(patches.Rectangle(((v_w-6)/2, 0.5), 6, 2.5, facecolor='#ffcccc', edgecolor='red', linestyle='--'))
        ax.text(v_w/2, 1.75, "FOH", color='red', ha='center')
        
    ax.set_title(f"Layout: {event.get_seating_type_display()}", color='white')
    ax.axis('off')
    return get_image()

def draw_audio(event, audio_specs):
    # (기존 코드 유지)
    v_w, v_d = event.venue_width, event.venue_depth
    s_w, s_d = event.stage_width, event.stage_depth
    
    fig, ax = plt.subplots(figsize=(6, v_d/v_w*6))
    ax.set_xlim(0, v_w)
    ax.set_ylim(0, v_d)
    ax.set_facecolor('#e0e4eb')
    
    stage_y = v_d - s_d
    ax.add_patch(patches.Rectangle(((v_w-s_w)/2, stage_y), s_w, s_d, color='#333'))
    
    if audio_specs['main_type'] == 'array':
        ax.plot([2, 4], [stage_y, stage_y-2], 'b-', lw=4)
        ax.plot([v_w-4, v_w-2], [stage_y, stage_y-2], 'b-', lw=4)
    else:
        ax.add_patch(patches.Rectangle((2, stage_y-1), 2, 2, color='blue'))
        ax.add_patch(patches.Rectangle((v_w-4, stage_y-1), 2, 2, color='blue'))
        
    if audio_specs['has_delay']:
        dy = v_d - audio_specs['delay_pos']
        ax.plot([0, v_w], [dy, dy], 'r--', alpha=0.5)
        ax.scatter([3, v_w-3], [dy, dy], c='red', s=100)
        ax.text(v_w/2, dy+0.5, f"Delay Point ({audio_specs['delay_pos']:.1f}m)", color='red', ha='center')
        
    ax.set_title("Audio Coverage Map", color='white')
    ax.axis('off')
    return get_image()

def draw_light(event, layout):
    # (기존 코드 유지)
    s_w, s_d = event.stage_width, event.stage_depth
    
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_facecolor('#f0f0f0')
    
    ax.add_patch(patches.Rectangle((-s_w/2, -s_d/2), s_w, s_d, fill=False, edgecolor='black', lw=2))
    ax.plot([-s_w/2, s_w/2], [s_d/2-0.5, s_d/2-0.5], 'k--', alpha=0.3)
    ax.plot([-s_w/2, s_w/2], [-s_d/2-3.0, -s_d/2-3.0], 'k--', alpha=0.3)
    
    for item in layout:
        ax.scatter(item['x'], item['y'], c=item['color'], s=100, edgecolors='black', zorder=5)
    
    ax.set_xlim(-(s_w/2)-2, (s_w/2)+2)
    ax.set_ylim(-(s_d/2)-5, (s_d/2)+2)
    ax.set_title("Lighting Plot", color='white')
    ax.grid(True, alpha=0.2)
    ax.axis('off')
    return get_image()