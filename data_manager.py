import sqlite3
import pandas as pd
import os
from datetime import datetime, timezone, timedelta

# 配置
DB_PATH = 'attendance.db'
DATA_DIR = 'data'

# 常量定义
TEACHER_IDS = ['0001', '0002', '0003', '0004']
SUPER_ADMIN_ID = '00000'
WEEKDAYS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
WEEKDAY_MAP = {0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'}

PERIODS = [
    '第1节', '第2节', '第3节', '第4节', '第5节',
    '第6节', '第7节', '第8节', '第9节', '第10节',
    '第11节', '第12节', '第13节'
]

DEFAULT_PERIOD_TIMES = {
    '第1节': {'start_time': '08:20', 'end_time': '09:00', 'early_start': '08:10', 'late_end': '08:30'},
    '第2节': {'start_time': '09:10', 'end_time': '09:50', 'early_start': '09:00', 'late_end': '09:20'},
    '第3节': {'start_time': '10:10', 'end_time': '10:50', 'early_start': '10:00', 'late_end': '10:20'},
    '第4节': {'start_time': '11:00', 'end_time': '11:40', 'early_start': '10:50', 'late_end': '11:10'},
    '第5节': {'start_time': '11:50', 'end_time': '12:30', 'early_start': '11:40', 'late_end': '12:00'},
    '第6节': {'start_time': '14:00', 'end_time': '14:40', 'early_start': '13:50', 'late_end': '14:10'},
    '第7节': {'start_time': '14:50', 'end_time': '15:30', 'early_start': '14:40', 'late_end': '15:00'},
    '第8节': {'start_time': '15:50', 'end_time': '16:30', 'early_start': '15:40', 'late_end': '16:00'},
    '第9节': {'start_time': '16:40', 'end_time': '17:20', 'early_start': '16:30', 'late_end': '16:50'},
    '第10节': {'start_time': '17:30', 'end_time': '18:10', 'early_start': '17:20', 'late_end': '17:40'},
    '第11节': {'start_time': '19:00', 'end_time': '19:40', 'early_start': '18:50', 'late_end': '19:10'},
    '第12节': {'start_time': '19:50', 'end_time': '20:30', 'early_start': '19:40', 'late_end': '20:00'},
    '第13节': {'start_time': '20:40', 'end_time': '21:20', 'early_start': '20:30', 'late_end': '20:50'}
}

# 初始化数据库
def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 考勤记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id TEXT NOT NULL,
            class_name TEXT NOT NULL,
            student_id TEXT NOT NULL,
            date_str TEXT NOT NULL,
            period TEXT NOT NULL,
            checkin_time TEXT DEFAULT '',
            status TEXT DEFAULT '缺勤',
            remark TEXT DEFAULT '',
            teacher TEXT DEFAULT '',
            UNIQUE(teacher_id, class_name, student_id, date_str, period)
        )
    ''')
    
    # 班级表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id TEXT NOT NULL,
            class_name TEXT NOT NULL,
            prefix TEXT DEFAULT '',
            student_count INTEGER DEFAULT 33,
            UNIQUE(teacher_id, class_name)
        )
    ''')
    
    # 课表设置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id TEXT NOT NULL,
            class_name TEXT NOT NULL,
            weekday TEXT NOT NULL,
            period TEXT NOT NULL,
            enabled INTEGER DEFAULT 0,
            start_time TEXT DEFAULT '08:20',
            end_time TEXT DEFAULT '09:00',
            early_start TEXT DEFAULT '08:10',
            late_end TEXT DEFAULT '08:30',
            UNIQUE(teacher_id, class_name, weekday, period)
        )
    ''')
    
    # 学生表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id TEXT NOT NULL,
            class_name TEXT NOT NULL,
            student_id TEXT NOT NULL,
            UNIQUE(teacher_id, class_name, student_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# 初始化默认数据
def init_default_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查是否已有默认班级
    cursor.execute("SELECT COUNT(*) FROM classes")
    if cursor.fetchone()[0] == 0:
        # 添加默认班级
        default_classes = [
            ('0001', '一班', '1', 33),
            ('0001', '二班', '2', 33),
            ('0001', '三班', '3', 33),
        ]
        cursor.executemany('INSERT INTO classes (teacher_id, class_name, prefix, student_count) VALUES (?, ?, ?, ?)', 
                          default_classes)
        
        # 添加默认学生
        students = []
        for teacher_id, class_name, prefix, count in default_classes:
            for i in range(1, count + 1):
                student_id = f"{prefix}{str(i).zfill(2)}"
                students.append((teacher_id, class_name, student_id))
        cursor.executemany('INSERT INTO students (teacher_id, class_name, student_id) VALUES (?, ?, ?)', students)
    
    conn.commit()
    conn.close()

# 获取老师的班级列表
def get_teacher_class_list(teacher_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM classes WHERE teacher_id = ?', (teacher_id,))
    classes = []
    for row in cursor.fetchall():
        classes.append({
            'id': row[0],
            'teacher_id': row[1],
            'name': row[2],
            'prefix': row[3],
            'student_count': row[4]
        })
    conn.close()
    return classes

# 获取班级的学生列表
def get_students_by_class(teacher_id, class_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT student_id FROM students WHERE teacher_id = ? AND class_name = ?', (teacher_id, class_name))
    students = [row[0] for row in cursor.fetchall()]
    conn.close()
    return students

# 根据学生ID获取班级
def get_class_by_student_id(teacher_id, student_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT class_name FROM students WHERE teacher_id = ? AND student_id = ?', (teacher_id, student_id))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# 添加班级
def add_teacher_class(teacher_id, class_name, prefix='', student_count=33):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO classes (teacher_id, class_name, prefix, student_count) VALUES (?, ?, ?, ?)',
                      (teacher_id, class_name, prefix, student_count))
        
        # 添加学生
        for i in range(1, student_count + 1):
            student_id = f"{prefix}{str(i).zfill(2)}" if prefix else f"{str(i).zfill(3)}"
            cursor.execute('INSERT INTO students (teacher_id, class_name, student_id) VALUES (?, ?, ?)',
                          (teacher_id, class_name, student_id))
        
        conn.commit()
        conn.close()
        return True, f"班级 {class_name} 添加成功"
    except Exception as e:
        return False, str(e)

# 删除班级
def remove_teacher_class(teacher_id, class_name):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM students WHERE teacher_id = ? AND class_name = ?', (teacher_id, class_name))
        cursor.execute('DELETE FROM classes WHERE teacher_id = ? AND class_name = ?', (teacher_id, class_name))
        conn.commit()
        conn.close()
        return True, f"班级 {class_name} 删除成功"
    except Exception as e:
        return False, str(e)

# 添加学生到班级
def add_student_to_class(teacher_id, class_name, student_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO students (teacher_id, class_name, student_id) VALUES (?, ?, ?)',
                      (teacher_id, class_name, student_id))
        conn.commit()
        conn.close()
        return True, f"学生 {student_id} 添加成功"
    except Exception as e:
        return False, str(e)

# 更新班级人数
def update_class_student_count(teacher_id, class_name, new_count):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 获取当前人数
        cursor.execute('SELECT student_count, prefix FROM classes WHERE teacher_id = ? AND class_name = ?', 
                      (teacher_id, class_name))
        result = cursor.fetchone()
        if not result:
            return False, "班级不存在"
        
        current_count, prefix = result
        
        if new_count > current_count:
            # 添加新学生
            for i in range(current_count + 1, new_count + 1):
                student_id = f"{prefix}{str(i).zfill(2)}" if prefix else f"{str(i).zfill(3)}"
                cursor.execute('INSERT INTO students (teacher_id, class_name, student_id) VALUES (?, ?, ?)',
                              (teacher_id, class_name, student_id))
        elif new_count < current_count:
            # 删除多余学生
            students = get_students_by_class(teacher_id, class_name)
            students_to_delete = students[new_count:]
            for student_id in students_to_delete:
                cursor.execute('DELETE FROM students WHERE teacher_id = ? AND class_name = ? AND student_id = ?',
                              (teacher_id, class_name, student_id))
        
        cursor.execute('UPDATE classes SET student_count = ? WHERE teacher_id = ? AND class_name = ?',
                      (new_count, teacher_id, class_name))
        
        conn.commit()
        conn.close()
        return True, f"班级 {class_name} 人数已更新为 {new_count}"
    except Exception as e:
        return False, str(e)

# 加载课表
def load_teacher_schedule(teacher_id, class_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT weekday, period, enabled, start_time, end_time, early_start, late_end '
                  'FROM schedules WHERE teacher_id = ? AND class_name = ?', (teacher_id, class_name))
    
    schedule = {}
    for row in cursor.fetchall():
        weekday, period, enabled, start_time, end_time, early_start, late_end = row
        if weekday not in schedule:
            schedule[weekday] = {}
        schedule[weekday][period] = {
            'enabled': bool(enabled),
            'start_time': start_time,
            'end_time': end_time,
            'early_start': early_start,
            'late_end': late_end
        }
    conn.close()
    return schedule

# 保存课表
def save_teacher_schedule(teacher_id, class_name, schedule):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for weekday, periods in schedule.items():
        for period, data in periods.items():
            cursor.execute('''
                INSERT OR REPLACE INTO schedules 
                (teacher_id, class_name, weekday, period, enabled, start_time, end_time, early_start, late_end)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (teacher_id, class_name, weekday, period, int(data['enabled']),
                  data['start_time'], data['end_time'], data['early_start'], data['late_end']))
    
    conn.commit()
    conn.close()

# 检查是否有课
def has_class(teacher_id, class_name, date_str, period):
    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    weekday = WEEKDAY_MAP[date.weekday()]
    
    schedule = load_teacher_schedule(teacher_id, class_name)
    return weekday in schedule and period in schedule[weekday] and schedule[weekday][period].get('enabled', False)

# 获取当前时间段和老师
def get_current_period_and_teacher(teacher_id, class_name, now):
    weekday = WEEKDAY_MAP[now.weekday()]
    schedule = load_teacher_schedule(teacher_id, class_name)
    
    if weekday not in schedule:
        return None, None
    
    current_time = now.strftime('%H:%M')
    
    for period, period_data in schedule[weekday].items():
        if period_data.get('enabled', False):
            start_time = period_data['start_time']
            end_time = period_data['end_time']
            
            if start_time <= current_time <= end_time:
                return period, {
                    'start_time': start_time,
                    'end_time': end_time,
                    'early_start': period_data['early_start'],
                    'late_end': period_data['late_end']
                }
    
    return None, None

# 检查考勤状态
def check_attendance_status(schedule, now):
    current_time = now.strftime('%H:%M')
    
    if current_time < schedule['early_start']:
        return 'early'
    elif current_time <= schedule['late_end']:
        return 'present'
    elif current_time <= schedule['end_time']:
        return 'late'
    else:
        return 'absent'

# 记录考勤
def record_attendance(teacher_id, class_name, student_id, period, status, checkin_time):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO attendance
            (teacher_id, class_name, student_id, date_str, period, checkin_time, status, teacher)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (teacher_id, class_name, student_id, 
              datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d'),
              period, checkin_time, status, teacher_id))
        
        conn.commit()
        conn.close()
        return True, f"✅ 已签到 ({status})"
    except Exception as e:
        return False, str(e)

# 加载考勤数据
def load_attendance(teacher_id, class_name, date_str, period):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT student_id, checkin_time, status, remark, teacher
        FROM attendance
        WHERE teacher_id = ? AND class_name = ? AND date_str = ? AND period = ?
    ''', (teacher_id, class_name, date_str, period))
    
    data = []
    for row in cursor.fetchall():
        data.append({
            '学号': row[0],
            '签到时间': row[1],
            '状态': row[2],
            '备注': row[3],
            '任课老师': row[4]
        })
    
    conn.close()
    
    if data:
        df = pd.DataFrame(data).set_index('学号')
    else:
        df = pd.DataFrame(columns=['学号', '签到时间', '状态', '备注', '任课老师']).set_index('学号')
    
    return df, f"{DATA_DIR}/{teacher_id}_{class_name}_{date_str}_{period}.csv"

# 更新考勤状态
def update_attendance_status(teacher_id, class_name, date_str, period, student_id, status, remark='', checkin_time=''):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO attendance
            (teacher_id, class_name, student_id, date_str, period, checkin_time, status, remark, teacher)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (teacher_id, class_name, student_id, date_str, period, checkin_time, status, remark, teacher_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

# 导出CSV
def export_to_csv(teacher_id, class_name, date_str, period):
    df, filepath = load_attendance(teacher_id, class_name, date_str, period)
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = f"{DATA_DIR}/{teacher_id}_{class_name}_{date_str}_{period}.csv"
    df.to_csv(filepath, encoding='utf-8-sig')
    return filepath

# 获取下一个班级编号
def get_next_class_number(teacher_id):
    classes = get_teacher_class_list(teacher_id)
    numbers = []
    for cls in classes:
        name = cls['name']
        if name.endswith('班'):
            try:
                num = int(name[:-1])
                numbers.append(num)
            except:
                pass
    return max(numbers) + 1 if numbers else 1

# 初始化
init_db()
init_default_data()
