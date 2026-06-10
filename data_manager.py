import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timezone, timedelta

# 数据目录
DATA_DIR = 'data'
SCHEDULES_DIR = os.path.join(DATA_DIR, 'schedules')
TEMP_SCHEDULES_DIR = os.path.join(DATA_DIR, 'temp_schedules')
ATTENDANCE_DIR = os.path.join(DATA_DIR, 'attendance')
TEACHER_CLASSES_DIR = os.path.join(DATA_DIR, 'teacher_classes')

# 初始化目录
os.makedirs(SCHEDULES_DIR, exist_ok=True)
os.makedirs(TEMP_SCHEDULES_DIR, exist_ok=True)
os.makedirs(ATTENDANCE_DIR, exist_ok=True)
os.makedirs(TEACHER_CLASSES_DIR, exist_ok=True)

# 老师账号列表
TEACHER_IDS = ['0001', '0002', '0003', '0004']

# 超级管理员账号
SUPER_ADMIN_ID = '00000'

# 时区设置（北京时间 UTC+8）
BEIJING_TZ = timezone(timedelta(hours=8))

def get_beijing_now():
    """获取北京时间"""
    return datetime.now(BEIJING_TZ)

# 星期列表
WEEKDAYS = ['周一', '周二', '周三', '周四', '周五']
WEEKDAY_MAP = {
    0: '周一',
    1: '周二',
    2: '周三',
    3: '周四',
    4: '周五',
    5: '周六',
    6: '周日'
}

# 节次列表
PERIODS = [f'第{i}节' for i in range(1, 14)]

# 默认每节课的时间
DEFAULT_PERIOD_TIMES = {
    '第1节': {'start_time': '08:20', 'end_time': '09:00', 'early_start': '08:10', 'late_end': '08:30',
              'enabled': False},
    '第2节': {'start_time': '09:10', 'end_time': '09:50', 'early_start': '09:00', 'late_end': '09:20',
              'enabled': False},
    '第3节': {'start_time': '10:00', 'end_time': '10:40', 'early_start': '09:50', 'late_end': '10:10',
              'enabled': False},
    '第4节': {'start_time': '10:50', 'end_time': '11:30', 'early_start': '10:40', 'late_end': '11:00',
              'enabled': False},
    '第5节': {'start_time': '11:40', 'end_time': '12:20', 'early_start': '11:30', 'late_end': '11:50',
              'enabled': False},
    '第6节': {'start_time': '14:00', 'end_time': '14:40', 'early_start': '13:50', 'late_end': '14:10',
              'enabled': False},
    '第7节': {'start_time': '14:50', 'end_time': '15:30', 'early_start': '14:40', 'late_end': '15:00',
              'enabled': False},
    '第8节': {'start_time': '15:40', 'end_time': '16:20', 'early_start': '15:30', 'late_end': '15:50',
              'enabled': False},
    '第9节': {'start_time': '16:30', 'end_time': '17:10', 'early_start': '16:20', 'late_end': '16:40',
              'enabled': False},
    '第10节': {'start_time': '17:20', 'end_time': '18:00', 'early_start': '17:10', 'late_end': '17:30',
               'enabled': False},
    '第11节': {'start_time': '19:00', 'end_time': '19:40', 'early_start': '18:50', 'late_end': '19:10',
               'enabled': False},
    '第12节': {'start_time': '19:50', 'end_time': '20:30', 'early_start': '19:40', 'late_end': '20:00',
               'enabled': False},
    '第13节': {'start_time': '20:40', 'end_time': '21:20', 'early_start': '20:30', 'late_end': '20:50',
               'enabled': False}
}


def get_default_schedule():
    schedule = {}
    for weekday in WEEKDAYS:
        schedule[weekday] = {}
        for period, times in DEFAULT_PERIOD_TIMES.items():
            schedule[weekday][period] = times.copy()
    return schedule


def get_teacher_classes_file(teacher_id):
    return os.path.join(TEACHER_CLASSES_DIR, f'{teacher_id}.json')


def load_teacher_classes(teacher_id):
    filepath = get_teacher_classes_file(teacher_id)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        default_classes = {
            '一班': {'prefix': '1', 'student_count': 33},
            '二班': {'prefix': '2', 'student_count': 33},
            '三班': {'prefix': '3', 'student_count': 33}
        }
        save_teacher_classes(teacher_id, default_classes)
        return default_classes


def save_teacher_classes(teacher_id, classes):
    filepath = get_teacher_classes_file(teacher_id)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(classes, f, ensure_ascii=False, indent=2)


def get_next_class_number(teacher_id):
    classes = load_teacher_classes(teacher_id)
    max_num = 0
    for class_name in classes.keys():
        for i in range(1, 100):
            if class_name == f'{i}班':
                if i > max_num:
                    max_num = i
    if max_num == 0:
        return len(classes) + 1
    return max_num + 1


def add_teacher_class(teacher_id, class_name, prefix, student_count):
    classes = load_teacher_classes(teacher_id)
    if class_name in classes:
        return False, "班级已存在"
    classes[class_name] = {
        'prefix': prefix,
        'student_count': student_count
    }
    save_teacher_classes(teacher_id, classes)
    schedule = get_default_schedule()
    save_teacher_schedule(teacher_id, class_name, schedule)
    return True, "添加成功"


def remove_teacher_class(teacher_id, class_name):
    if class_name in ['一班', '二班', '三班']:
        return False, "不能删除默认班级"
    classes = load_teacher_classes(teacher_id)
    if class_name not in classes:
        return False, "班级不存在"
    del classes[class_name]
    save_teacher_classes(teacher_id, classes)
    prefix = f'{teacher_id}_{class_name}'
    for file in os.listdir(ATTENDANCE_DIR):
        if file.startswith(prefix):
            os.remove(os.path.join(ATTENDANCE_DIR, file))
    return True, "删除成功"


def update_class_student_count(teacher_id, class_name, student_count):
    classes = load_teacher_classes(teacher_id)
    if class_name not in classes:
        return False, "班级不存在"
    classes[class_name]['student_count'] = student_count
    save_teacher_classes(teacher_id, classes)
    return True, "修改成功"


def get_teacher_class_list(teacher_id):
    classes = load_teacher_classes(teacher_id)
    result = []
    for class_name, info in classes.items():
        result.append({
            'name': class_name,
            'prefix': info['prefix'],
            'student_count': info['student_count']
        })
    return result


def get_students_by_class(teacher_id, class_name):
    classes = load_teacher_classes(teacher_id)
    if class_name not in classes:
        return []
    prefix = classes[class_name]['prefix']
    count = classes[class_name]['student_count']
    return [f'{prefix}{i:02d}' for i in range(1, count + 1)]


def get_class_by_student_id(teacher_id, student_id):
    classes = load_teacher_classes(teacher_id)
    for class_name, info in classes.items():
        prefix = info['prefix']
        if student_id.startswith(prefix):
            return class_name
    return None


def get_schedule_key(teacher_id, class_name):
    return f'{teacher_id}_{class_name}'


def load_teacher_schedule(teacher_id, class_name):
    key = get_schedule_key(teacher_id, class_name)
    schedule_file = os.path.join(SCHEDULES_DIR, f'{key}.json')
    if os.path.exists(schedule_file):
        with open(schedule_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return get_default_schedule()


def save_teacher_schedule(teacher_id, class_name, schedule):
    key = get_schedule_key(teacher_id, class_name)
    schedule_file = os.path.join(SCHEDULES_DIR, f'{key}.json')
    with open(schedule_file, 'w', encoding='utf-8') as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)


def load_temp_schedules(teacher_id, class_name):
    key = get_schedule_key(teacher_id, class_name)
    temp_file = os.path.join(TEMP_SCHEDULES_DIR, f'{key}.json')
    if os.path.exists(temp_file):
        with open(temp_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {}


def save_temp_schedules(teacher_id, class_name, temp_schedules):
    key = get_schedule_key(teacher_id, class_name)
    temp_file = os.path.join(TEMP_SCHEDULES_DIR, f'{key}.json')
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(temp_schedules, f, ensure_ascii=False, indent=2)


def add_temp_schedule(teacher_id, class_name, date_str, period, schedule):
    temp_schedules = load_temp_schedules(teacher_id, class_name)
    if date_str not in temp_schedules:
        temp_schedules[date_str] = {}
    temp_schedules[date_str][period] = schedule
    save_temp_schedules(teacher_id, class_name, temp_schedules)


def remove_temp_schedule(teacher_id, class_name, date_str, period):
    temp_schedules = load_temp_schedules(teacher_id, class_name)
    if date_str in temp_schedules and period in temp_schedules[date_str]:
        del temp_schedules[date_str][period]
        if len(temp_schedules[date_str]) == 0:
            del temp_schedules[date_str]
        save_temp_schedules(teacher_id, class_name, temp_schedules)
        return True
    return False


def has_class(teacher_id, class_name, date_str, period):
    """检查某个班级在某个日期和节次是否有课"""
    date = datetime.strptime(date_str, '%Y-%m-%d')
    weekday = WEEKDAY_MAP[date.weekday()]
    
    if weekday not in WEEKDAYS:
        return False
    
    # 先检查临时课表
    temp_schedules = load_temp_schedules(teacher_id, class_name)
    if date_str in temp_schedules and period in temp_schedules[date_str]:
        if temp_schedules[date_str][period].get('enabled', False):
            return True
    
    # 检查常规课表
    schedule = load_teacher_schedule(teacher_id, class_name)
    weekday_schedule = schedule.get(weekday, {})
    period_schedule = weekday_schedule.get(period, {})
    
    return period_schedule.get('enabled', False)


def get_current_period_and_teacher(teacher_id, class_name, current_time):
    current_str = current_time.strftime('%H:%M')
    weekday = WEEKDAY_MAP[current_time.weekday()]
    date_str = current_time.strftime('%Y-%m-%d')

    if weekday not in WEEKDAYS:
        return None, None

    temp_schedules = load_temp_schedules(teacher_id, class_name)
    if date_str in temp_schedules:
        for period, schedule in temp_schedules[date_str].items():
            if schedule.get('enabled', False):
                end_time = schedule.get('end_time')
                early_start = schedule.get('early_start')
                if early_start and end_time and early_start <= current_str <= end_time:
                    return period, schedule

    schedule = load_teacher_schedule(teacher_id, class_name)
    weekday_schedule = schedule.get(weekday, {})
    for period, period_schedule in weekday_schedule.items():
        if period_schedule.get('enabled', False):
            end_time = period_schedule.get('end_time')
            early_start = period_schedule.get('early_start')
            if early_start and end_time and early_start <= current_str <= end_time:
                return period, period_schedule

    return None, None


def check_attendance_status(schedule, current_time):
    if schedule is None or not schedule.get('enabled', False):
        return 'no_class'

    early_start = schedule.get('early_start')
    start_time = schedule.get('start_time')
    late_end = schedule.get('late_end')

    if not early_start or not start_time or not late_end:
        return 'no_class'

    current_str = current_time.strftime('%H:%M')

    if current_str < early_start:
        return 'early'
    elif current_str <= start_time:
        return 'present'
    elif current_str <= late_end:
        return 'late'
    else:
        return 'absent'


def load_attendance(teacher_id, class_name, date_str, period):
    filename = f'{teacher_id}_{class_name}_{date_str}_{period}.csv'
    filepath = os.path.join(ATTENDANCE_DIR, filename)

    if os.path.exists(filepath):
        df = pd.read_csv(filepath, index_col=0)
        # 确保index是字符串类型，与get_students_by_class返回的类型一致
        df.index = df.index.astype(str)
        # 确保签到时间列是字符串类型
        if '签到时间' in df.columns:
            df['签到时间'] = df['签到时间'].fillna('').astype(str)
        # 确保备注列是字符串类型
        if '备注' in df.columns:
            df['备注'] = df['备注'].fillna('').astype(str)
        # 如果没有任课老师列，添加默认值
        if '任课老师' not in df.columns:
            df['任课老师'] = str(teacher_id)
        else:
            # 确保任课老师列是字符串类型
            df['任课老师'] = df['任课老师'].fillna('').astype(str)
        return df, filepath
    else:
        student_ids = get_students_by_class(teacher_id, class_name)
        df = pd.DataFrame(index=student_ids, columns=['签到时间', '状态', '备注', '任课老师'])
        df['签到时间'] = ''
        df['状态'] = '缺勤'
        df['备注'] = ''
        df['任课老师'] = str(teacher_id)
        return df, filepath


def save_attendance(df, filepath):
    df.to_csv(filepath, encoding='utf-8-sig')


def record_attendance(teacher_id, class_name, student_id, period, status, time_str):
    date_str = datetime.now().strftime('%Y-%m-%d')
    df, filepath = load_attendance(teacher_id, class_name, date_str, period)

    # 确保student_id是字符串类型来匹配index
    student_id = str(student_id)

    if student_id in df.index and df.loc[student_id, '状态'] != '缺勤' and df.loc[student_id, '签到时间'] != '':
        return False, '这节课你已经签过了'

    df.loc[student_id, '签到时间'] = time_str
    df.loc[student_id, '状态'] = status
    df.loc[student_id, '备注'] = ''

    save_attendance(df, filepath)
    return True, f'签到成功（{status}）'


def update_attendance_status(teacher_id, class_name, date_str, period, student_id, new_status, remark='', checkin_time=''):
    df, filepath = load_attendance(teacher_id, class_name, date_str, period)

    # 确保student_id是字符串类型来匹配index
    student_id = str(student_id)
    
    if student_id in df.index:
        df.loc[student_id, '状态'] = new_status
        if remark:
            df.loc[student_id, '备注'] = remark
        if checkin_time:
            df.loc[student_id, '签到时间'] = checkin_time
        save_attendance(df, filepath)
        return True
    return False


def get_attendance_summary(teacher_id, class_name, date_str, period):
    df, _ = load_attendance(teacher_id, class_name, date_str, period)

    present_count = len(df[df['状态'] == '出勤'])
    late_count = len(df[df['状态'] == '迟到'])
    absent_count = len(df[df['状态'] == '缺勤'])

    return {
        'total': len(df),
        'present': present_count,
        'late': late_count,
        'absent': absent_count
    }


def export_to_csv(teacher_id, class_name, date_str, period):
    df, filepath = load_attendance(teacher_id, class_name, date_str, period)

    export_df = df.reset_index()
    export_df = export_df.rename(columns={'index': '学号'})

    export_filename = f'attendance_{teacher_id}_{class_name}_{date_str}_{period}.csv'
    export_path = os.path.join(ATTENDANCE_DIR, export_filename)
    export_df.to_csv(export_path, index=False, encoding='utf-8-sig')

    return export_path


def get_all_temp_schedules(teacher_id, class_name):
    temp_schedules = load_temp_schedules(teacher_id, class_name)
    result = []
    for date_str, periods in temp_schedules.items():
        for period, schedule in periods.items():
            result.append({
                'date': date_str,
                'period': period,
                'schedule': schedule
            })
    result.sort(key=lambda x: x['date'])
    return result
