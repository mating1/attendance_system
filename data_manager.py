import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

# 数据目录
DATA_DIR = 'data'
SCHEDULES_DIR = os.path.join(DATA_DIR, 'schedules')
TEMP_SCHEDULES_DIR = os.path.join(DATA_DIR, 'temp_schedules')
ATTENDANCE_DIR = os.path.join(DATA_DIR, 'attendance')

# 初始化目录
os.makedirs(SCHEDULES_DIR, exist_ok=True)
os.makedirs(TEMP_SCHEDULES_DIR, exist_ok=True)
os.makedirs(ATTENDANCE_DIR, exist_ok=True)

# 班级配置
CLASSES = ['一班', '二班', '三班']
CLASS_PREFIX = {
    '一班': '1',
    '二班': '2',
    '三班': '3'
}

# 生成所有学号（101~133, 201~233, 301~333）
STUDENT_IDS = []
for class_name in CLASSES:
    prefix = CLASS_PREFIX[class_name]
    for i in range(1, 34):
        STUDENT_IDS.append(f'{prefix}{i:02d}')


# 根据学号获取班级
def get_class_by_student_id(student_id):
    if student_id.startswith('1'):
        return '一班'
    elif student_id.startswith('2'):
        return '二班'
    elif student_id.startswith('3'):
        return '三班'
    return None


# 获取某个班级的学生学号列表
def get_students_by_class(class_name):
    prefix = CLASS_PREFIX[class_name]
    return [f'{prefix}{i:02d}' for i in range(1, 34)]


# 老师账号列表
TEACHER_IDS = ['0001', '0002', '0003', '0004']

# 星期列表（周一到周五有课）
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
    """获取默认课表（全部禁用）"""
    schedule = {}
    for weekday in WEEKDAYS:
        schedule[weekday] = {}
        for period, times in DEFAULT_PERIOD_TIMES.items():
            schedule[weekday][period] = times.copy()
    return schedule


def get_schedule_key(teacher_id, class_name):
    """获取课表文件的key"""
    return f'{teacher_id}_{class_name}'


def load_teacher_schedule(teacher_id, class_name):
    """加载老师某个班级的课表"""
    key = get_schedule_key(teacher_id, class_name)
    schedule_file = os.path.join(SCHEDULES_DIR, f'{key}.json')
    if os.path.exists(schedule_file):
        with open(schedule_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return get_default_schedule()


def save_teacher_schedule(teacher_id, class_name, schedule):
    """保存老师某个班级的课表"""
    key = get_schedule_key(teacher_id, class_name)
    schedule_file = os.path.join(SCHEDULES_DIR, f'{key}.json')
    with open(schedule_file, 'w', encoding='utf-8') as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)


def load_temp_schedules(teacher_id, class_name):
    """加载老师的临时调休记录"""
    key = get_schedule_key(teacher_id, class_name)
    temp_file = os.path.join(TEMP_SCHEDULES_DIR, f'{key}.json')
    if os.path.exists(temp_file):
        with open(temp_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {}


def save_temp_schedules(teacher_id, class_name, temp_schedules):
    """保存老师的临时调休记录"""
    key = get_schedule_key(teacher_id, class_name)
    temp_file = os.path.join(TEMP_SCHEDULES_DIR, f'{key}.json')
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(temp_schedules, f, ensure_ascii=False, indent=2)


def add_temp_schedule(teacher_id, class_name, date_str, period, schedule):
    """添加临时调休"""
    temp_schedules = load_temp_schedules(teacher_id, class_name)
    if date_str not in temp_schedules:
        temp_schedules[date_str] = {}
    temp_schedules[date_str][period] = schedule
    save_temp_schedules(teacher_id, class_name, temp_schedules)


def remove_temp_schedule(teacher_id, class_name, date_str, period):
    """删除临时调休"""
    temp_schedules = load_temp_schedules(teacher_id, class_name)
    if date_str in temp_schedules and period in temp_schedules[date_str]:
        del temp_schedules[date_str][period]
        if len(temp_schedules[date_str]) == 0:
            del temp_schedules[date_str]
        save_temp_schedules(teacher_id, class_name, temp_schedules)
        return True
    return False


def get_period_schedule(teacher_id, class_name, period, date=None):
    """获取某天某节课的课表（优先使用临时调休）"""
    if date is None:
        date = datetime.now()

    date_str = date.strftime('%Y-%m-%d')
    weekday = WEEKDAY_MAP[date.weekday()]

    # 周六周日没有课
    if weekday not in WEEKDAYS:
        return None

    # 优先检查临时调休
    temp_schedules = load_temp_schedules(teacher_id, class_name)
    if date_str in temp_schedules and period in temp_schedules[date_str]:
        return temp_schedules[date_str][period]

    # 使用每周固定课表
    schedule = load_teacher_schedule(teacher_id, class_name)
    if weekday in schedule and period in schedule[weekday]:
        return schedule[weekday][period]

    return None


def get_current_period_and_teacher(class_name, current_time):
    """根据当前时间和班级，找到对应的老师和节次"""
    current_str = current_time.strftime('%H:%M')
    weekday = WEEKDAY_MAP[current_time.weekday()]
    date_str = current_time.strftime('%Y-%m-%d')

    # 周六周日没有课
    if weekday not in WEEKDAYS:
        return None, None, None

    # 遍历所有老师
    for teacher_id in TEACHER_IDS:
        # 先查临时调休
        temp_schedules = load_temp_schedules(teacher_id, class_name)
        if date_str in temp_schedules:
            for period, schedule in temp_schedules[date_str].items():
                if schedule.get('enabled', False):
                    start_time = schedule.get('start_time')
                    end_time = schedule.get('end_time')
                    if start_time and end_time and start_time <= current_str <= end_time:
                        return teacher_id, period, schedule

        # 查每周固定课表
        schedule = load_teacher_schedule(teacher_id, class_name)
        weekday_schedule = schedule.get(weekday, {})
        for period, period_schedule in weekday_schedule.items():
            if period_schedule.get('enabled', False):
                start_time = period_schedule.get('start_time')
                end_time = period_schedule.get('end_time')
                if start_time and end_time and start_time <= current_str <= end_time:
                    return teacher_id, period, period_schedule

    return None, None, None


def check_attendance_status(schedule, current_time):
    """
    根据课表时间和当前时间判断考勤状态
    返回: 'early'(太早), 'present'(出勤), 'late'(迟到), 'absent'(缺勤), 'no_class'(无课)
    """
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
    """加载某天某节课的考勤数据"""
    filename = f'{teacher_id}_{class_name}_{date_str}_{period}.csv'
    filepath = os.path.join(ATTENDANCE_DIR, filename)

    if os.path.exists(filepath):
        df = pd.read_csv(filepath, index_col=0)
        return df, filepath
    else:
        # 创建空的考勤表，使用该班级的学生学号
        student_ids = get_students_by_class(class_name)
        df = pd.DataFrame(index=student_ids, columns=['签到时间', '状态', '备注'])
        df['签到时间'] = ''
        df['状态'] = '缺勤'
        df['备注'] = ''
        return df, filepath


def save_attendance(df, filepath):
    """保存考勤数据"""
    df.to_csv(filepath, encoding='utf-8-sig')


def record_attendance(teacher_id, class_name, student_id, period, status, time_str):
    """记录学生签到"""
    date_str = datetime.now().strftime('%Y-%m-%d')
    df, filepath = load_attendance(teacher_id, class_name, date_str, period)

    # 检查是否已经签过
    if student_id in df.index and df.loc[student_id, '状态'] != '缺勤' and df.loc[student_id, '签到时间'] != '':
        return False, '这节课你已经签过了'

    # 记录签到
    df.loc[student_id, '签到时间'] = time_str
    df.loc[student_id, '状态'] = status
    df.loc[student_id, '备注'] = ''

    save_attendance(df, filepath)
    return True, f'签到成功（{status}）'


def update_attendance_status(teacher_id, class_name, date_str, period, student_id, new_status, remark=''):
    """老师修改学生考勤状态"""
    df, filepath = load_attendance(teacher_id, class_name, date_str, period)

    if student_id in df.index:
        df.loc[student_id, '状态'] = new_status
        if remark:
            df.loc[student_id, '备注'] = remark
        save_attendance(df, filepath)
        return True
    return False


def get_attendance_summary(teacher_id, class_name, date_str, period):
    """获取考勤汇总"""
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
    """导出考勤表为CSV"""
    df, filepath = load_attendance(teacher_id, class_name, date_str, period)

    # 重置索引，让学号成为一列
    export_df = df.reset_index()
    export_df = export_df.rename(columns={'index': '学号'})

    export_filename = f'attendance_{teacher_id}_{class_name}_{date_str}_{period}.csv'
    export_path = os.path.join(ATTENDANCE_DIR, export_filename)
    export_df.to_csv(export_path, index=False, encoding='utf-8-sig')

    return export_path


def get_all_temp_schedules(teacher_id, class_name):
    """获取所有临时调休记录"""
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