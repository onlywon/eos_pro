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
    gap = event.table_gap
    
    report = {'warnings': [], 'infos': []}
    
    screen_space = (v_w - s_w) / 2
    if screen_space >= 2.5:
        report['infos'].append(f"✅ 무대 양옆 {screen_space:.1f}m 확보 (200인치 스크린 가능)")
    elif screen_space < 1.0:
        report['warnings'].append(f"⚠️ 무대 좌우 공간 협소 ({screen_space:.1f}m).")
        
    avail_w = v_w - 3.0 
    cols = int(avail_w // gap)
    start_y = v_d - event.stage_depth - 4.0
    end_y = 4.0 if event.has_foh else 2.0
    rows = int((start_y - end_y) // gap)
    
    raw_count = cols * rows
    if event.has_virgin_road: raw_count -= rows 
    table_count = max(0, int(raw_count))
    
    report['table_count'] = table_count
    report['pax'] = table_count * 8
    return report

def calculate_audio(event):
    v_d = event.venue_depth
    v_w = event.venue_width
    
    # [수정] 행사 종류가 'concert'나 'festival'이면 퍼포먼스 모드로 인식!
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
        specs['delay'] = f"10~12 inch Point Source 1조 ({delay_pos:.1f}m 지점)"
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
        # [수정] 조명 엔진도 똑같이 수정
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

        # Spot (Front)
        for i in range(num_spots):
            offset = (i - (num_spots/2) + 0.5) * 2.5
            patch_list.append({'id': f'S{i+1}', 'fixture': 'Ellipsoidal', 'addr': addr, 'ch': 1, 'watt': 750})
            layout.append({'type': 'Spot', 'x': offset, 'y': -(self.d/2) - 3.0, 'color': 'orange'})
            addr += 1
            
        total_watts = sum([p['watt'] for p in patch_list])
        return patch_list, round((total_watts*1.2)/1000, 2), layout

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
    
    stage_y = v_d - s_d - 1.0
    ax.add_patch(patches.Rectangle(((v_w-s_w)/2, stage_y), s_w, s_d, color='#333'))
    ax.text(v_w/2, stage_y + s_d/2, "STAGE", color='white', ha='center', va='center', fontweight='bold')
    
    gap = event.table_gap
    start_x = (v_w - (int((v_w-3.0)//gap)-1)*gap)/2
    start_y = stage_y - 4.0
    end_y = 4.0 if event.has_foh else 2.0
    
    rows = int((start_y - end_y) // gap)
    cols = int((v_w - 3.0) // gap)
    
    for r in range(rows):
        curr_y = start_y - (r * gap)
        for c in range(cols):
            curr_x = start_x + (c * gap)
            if event.has_virgin_road and abs(curr_x - v_w/2) < 1.0: continue
            ax.add_patch(patches.Circle((curr_x, curr_y), 0.9, facecolor='white', edgecolor='#555'))
            
    if event.has_foh:
        ax.add_patch(patches.Rectangle(((v_w-6)/2, 0.5), 6, 2.5, facecolor='#ffcccc', edgecolor='red', linestyle='--'))
        ax.text(v_w/2, 1.75, "FOH", color='red', ha='center')
        
    ax.set_title("Space Layout Plan", color='white')
    ax.axis('off')
    return get_image()

def draw_audio(event, audio_specs):
    v_w, v_d = event.venue_width, event.venue_depth
    s_w, s_d = event.stage_width, event.stage_depth
    
    fig, ax = plt.subplots(figsize=(6, v_d/v_w*6))
    ax.set_xlim(0, v_w)
    ax.set_ylim(0, v_d)
    ax.set_facecolor('#e0e4eb')
    
    stage_y = v_d - s_d
    ax.add_patch(patches.Rectangle(((v_w-s_w)/2, stage_y), s_w, s_d, color='#333'))
    
    if audio_specs['main_type'] == 'array':
        ax.plot([2, 4], [stage_y, stage_y-2], 'b-', lw=4) # L
        ax.plot([v_w-4, v_w-2], [stage_y, stage_y-2], 'b-', lw=4) # R
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