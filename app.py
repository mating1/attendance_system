import streamlit as st
from datetime import datetime
from data_manager import *

st.set_page_config(page_title="学生考勤系统", page_icon="📋", layout="centered")

# 简单背景色
st.markdown("""
<style>
.stApp {
    background: #e6f3ff;
}
div.stButton > button {
    width: 100%;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# 初始化session
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'teacher_id' not in st.session_state:
    st.session_state.teacher_id = None
if 'selected_class' not in st.session_state:
    st.session_state.selected_class = '一班'

# 标题
st.title("📋 学生考勤系统")

# ========== 登录界面 ==========
if st.session_state.user_type is None:
    user_id = st.text_input("账号", max_chars=4, placeholder="请输入账号")
    if st.button("登录", use_container_width=True):
        if user_id in STUDENT_IDS:
            st.session_state.user_type = 'student'
            st.session_state.user_id = user_id
            st.rerun()
        elif user_id in TEACHER_IDS:
            st.session_state.user_type = 'teacher'
            st.session_state.user_id = user_id
            st.session_state.teacher_id = user_id
            st.rerun()
        else:
            st.error("账号不存在")

# ========== 学生签到 ==========
elif st.session_state.user_type == 'student':
    # 自动识别班级
    student_class = get_class_by_student_id(st.session_state.user_id)

    st.subheader(f"学生签到 - 学号 {st.session_state.user_id} ({student_class})")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("退出", use_container_width=True):
            st.session_state.user_type = None
            st.rerun()

    now = datetime.now()
    weekday = WEEKDAY_MAP[now.weekday()]
    st.write(f"当前时间：{now.strftime('%Y-%m-%d %H:%M:%S')} {weekday}")

    if weekday not in WEEKDAYS:
        st.warning("周末无课程")
    else:
        # 自动判断当前是第几节课、哪个老师
        teacher_id, period, schedule = get_current_period_and_teacher(student_class, now)

        if teacher_id is None:
            st.warning("当前没有进行中的课程")
        else:
            st.markdown(f"### 📚 {period}")
            st.write(f"老师账号：{teacher_id}")
            st.write(f"上课时间：{schedule['start_time']} - {schedule['end_time']}")
            st.write(f"签到开始：{schedule['early_start']}")
            st.write(f"迟到截止：{schedule['late_end']}")

            # 判断签到状态
            status = check_attendance_status(schedule, now)

            if status == 'early':
                st.error(f"签到时间未到，请在 {schedule['early_start']} 后签到")
            elif status == 'absent':
                st.error("签到时间已过，已记为缺勤，请联系老师补录")
            elif status == 'present':
                if st.button("签到", use_container_width=True, type="primary"):
                    ok, msg = record_attendance(
                        teacher_id,
                        student_class,
                        st.session_state.user_id,
                        period,
                        '出勤',
                        now.strftime('%H:%M:%S')
                    )
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
            elif status == 'late':
                if st.button("签到", use_container_width=True, type="primary"):
                    ok, msg = record_attendance(
                        teacher_id,
                        student_class,
                        st.session_state.user_id,
                        period,
                        '迟到',
                        now.strftime('%H:%M:%S')
                    )
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
            else:
                st.error("无法判断签到状态")

# ========== 老师管理 ==========
elif st.session_state.user_type == 'teacher':
    st.subheader(f"老师管理 - {st.session_state.user_id}")

    # 选择班级
    selected_class = st.selectbox("选择班级", CLASSES, key="class_selector")
    st.session_state.selected_class = selected_class

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("考勤记录", use_container_width=True):
            st.session_state.page = 'attendance'
    with col2:
        if st.button("课表设置", use_container_width=True):
            st.session_state.page = 'schedule'
    with col3:
        if st.button("临时调休", use_container_width=True):
            st.session_state.page = 'temp'

    if st.button("退出登录", use_container_width=True):
        st.session_state.user_type = None
        st.session_state.page = None
        st.rerun()

    st.divider()

    # 获取当前班级的学生列表
    class_students = get_students_by_class(st.session_state.selected_class)

    # ========== 考勤记录页面 ==========
    if st.session_state.get('page') == 'attendance' or st.session_state.get('page') is None:
        st.session_state.page = 'attendance'
        st.markdown(f"### 考勤记录 - {st.session_state.selected_class}")

        col1, col2 = st.columns(2)
        with col1:
            selected_date = st.date_input("选择日期", datetime.now())
        with col2:
            selected_period = st.selectbox("选择节次", PERIODS)

        if st.button("查询", use_container_width=True):
            date_str = selected_date.strftime('%Y-%m-%d')
            df, _ = load_attendance(st.session_state.teacher_id, st.session_state.selected_class, date_str,
                                    selected_period)

            # 汇总
            summary = get_attendance_summary(st.session_state.teacher_id, st.session_state.selected_class, date_str,
                                             selected_period)
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.write(f"出勤: {summary['present']}")
            with col2:
                st.write(f"迟到: {summary['late']}")
            with col3:
                st.write(f"缺勤: {summary['absent']}")
            with col4:
                st.write(f"总计: {summary['total']}")

            # 表格
            st.write("---")
            for student_id in class_students:
                col1, col2, col3, col4 = st.columns([1, 1.5, 1.5, 2])
                with col1:
                    st.write(student_id)
                with col2:
                    time_val = df.loc[student_id, '签到时间'] if student_id in df.index else ''
                    st.write(time_val if time_val else '--')
                with col3:
                    status_val = df.loc[student_id, '状态'] if student_id in df.index else '缺勤'
                    st.write(status_val)
                with col4:
                    # 三个按钮横着并排
                    btn_col1, btn_col2, btn_col3 = st.columns(3)
                    with btn_col1:
                        if st.button("出勤", key=f"to_present_{student_id}", use_container_width=True):
                            update_attendance_status(st.session_state.teacher_id, st.session_state.selected_class,
                                                     date_str, selected_period, student_id, '出勤', '')
                            st.rerun()
                    with btn_col2:
                        if st.button("迟到", key=f"to_late_{student_id}", use_container_width=True):
                            update_attendance_status(st.session_state.teacher_id, st.session_state.selected_class,
                                                     date_str, selected_period, student_id, '迟到', '')
                            st.rerun()
                    with btn_col3:
                        if st.button("缺勤", key=f"to_absent_{student_id}", use_container_width=True):
                            update_attendance_status(st.session_state.teacher_id, st.session_state.selected_class,
                                                     date_str, selected_period, student_id, '缺勤', '')
                            st.rerun()

            # 导出
            if st.button("导出CSV", use_container_width=True):
                filepath = export_to_csv(st.session_state.teacher_id, st.session_state.selected_class, date_str,
                                         selected_period)
                with open(filepath, 'rb') as f:
                    st.download_button("下载CSV", f,
                                       file_name=f"考勤_{st.session_state.selected_class}_{date_str}_{selected_period}.csv")

    # ========== 课表设置页面 ==========
    elif st.session_state.get('page') == 'schedule':
        st.markdown(f"### 课表设置 - {st.session_state.selected_class}")

        # 选择星期
        selected_weekday = st.selectbox("选择星期", WEEKDAYS)

        # 加载当前星期的课表
        schedule = load_teacher_schedule(st.session_state.teacher_id, st.session_state.selected_class)
        weekday_schedule = schedule.get(selected_weekday, {})

        # 显示表格
        st.write("---")

        # 表头
        col1, col2, col3, col4, col5 = st.columns([0.5, 1, 1, 1, 1])
        with col1:
            st.write("启用")
        with col2:
            st.write("节次")
        with col3:
            st.write("上课时间")
        with col4:
            st.write("签到开始")
        with col5:
            st.write("迟到截止")

        # 每一行
        for period in PERIODS:
            period_data = weekday_schedule.get(period, DEFAULT_PERIOD_TIMES[period].copy())

            col1, col2, col3, col4, col5 = st.columns([0.5, 1, 1, 1, 1])
            with col1:
                enabled = st.checkbox("", value=period_data.get('enabled', False),
                                      key=f"en_{st.session_state.selected_class}_{selected_weekday}_{period}")
            with col2:
                st.write(period)
            with col3:
                start_time = st.time_input(
                    "上课",
                    value=datetime.strptime(period_data['start_time'], '%H:%M').time(),
                    key=f"start_{st.session_state.selected_class}_{selected_weekday}_{period}",
                    label_visibility="collapsed"
                )
            with col4:
                early_start = st.time_input(
                    "签到开始",
                    value=datetime.strptime(period_data['early_start'], '%H:%M').time(),
                    key=f"early_{st.session_state.selected_class}_{selected_weekday}_{period}",
                    label_visibility="collapsed"
                )
            with col5:
                late_end = st.time_input(
                    "迟到截止",
                    value=datetime.strptime(period_data['late_end'], '%H:%M').time(),
                    key=f"late_{st.session_state.selected_class}_{selected_weekday}_{period}",
                    label_visibility="collapsed"
                )

            # 保存修改到内存
            if selected_weekday not in schedule:
                schedule[selected_weekday] = {}
            schedule[selected_weekday][period] = {
                'enabled': enabled,
                'start_time': start_time.strftime('%H:%M'),
                'early_start': early_start.strftime('%H:%M'),
                'late_end': late_end.strftime('%H:%M'),
                'end_time': period_data.get('end_time', '09:00')
            }

        st.write("---")

        # 保存按钮
        if st.button("保存课表", use_container_width=True, type="primary"):
            save_teacher_schedule(st.session_state.teacher_id, st.session_state.selected_class, schedule)
            st.success(f"{st.session_state.selected_class} {selected_weekday} 课表保存成功")

    # ========== 临时调休页面 ==========
    elif st.session_state.get('page') == 'temp':
        st.markdown(f"### 临时调休 - {st.session_state.selected_class}")

        # 添加调休
        st.markdown("#### 添加调休")
        col1, col2 = st.columns(2)
        with col1:
            temp_date = st.date_input("选择日期", datetime.now())
        with col2:
            temp_period = st.selectbox("选择节次", PERIODS)

        # 获取默认时间
        default_schedule = get_period_schedule(st.session_state.teacher_id, st.session_state.selected_class,
                                               temp_period, temp_date)
        if default_schedule:
            default_start = datetime.strptime(default_schedule['start_time'], '%H:%M').time()
            default_early = datetime.strptime(default_schedule['early_start'], '%H:%M').time()
            default_late = datetime.strptime(default_schedule['late_end'], '%H:%M').time()
        else:
            default_start = datetime.strptime('09:00', '%H:%M').time()
            default_early = datetime.strptime('08:30', '%H:%M').time()
            default_late = datetime.strptime('09:20', '%H:%M').time()

        col1, col2, col3 = st.columns(3)
        with col1:
            temp_start = st.time_input("上课时间", value=default_start)
        with col2:
            temp_early = st.time_input("开始签到", value=default_early)
        with col3:
            temp_late = st.time_input("迟到截止", value=default_late)

        if st.button("添加调休", use_container_width=True):
            new_schedule = {
                'enabled': True,
                'start_time': temp_start.strftime('%H:%M'),
                'early_start': temp_early.strftime('%H:%M'),
                'late_end': temp_late.strftime('%H:%M'),
                'end_time': '09:40'
            }
            add_temp_schedule(st.session_state.teacher_id, st.session_state.selected_class,
                              temp_date.strftime('%Y-%m-%d'), temp_period, new_schedule)
            st.success(f"已添加 {temp_date} {temp_period} 的调休")
            st.rerun()

        st.write("---")

        # 显示已有调休
        st.markdown("#### 已设置的调休")
        temp_list = get_all_temp_schedules(st.session_state.teacher_id, st.session_state.selected_class)

        if len(temp_list) == 0:
            st.info("暂无调休设置")
        else:
            for item in temp_list:
                col1, col2, col3, col4 = st.columns([2, 1.5, 3, 1])
                with col1:
                    st.write(item['date'])
                with col2:
                    st.write(item['period'])
                with col3:
                    s = item['schedule']
                    st.write(f"{s['start_time']} | {s['early_start']} | {s['late_end']}")
                with col4:
                    if st.button("删除", key=f"del_{st.session_state.selected_class}_{item['date']}_{item['period']}"):
                        remove_temp_schedule(st.session_state.teacher_id, st.session_state.selected_class, item['date'],
                                             item['period'])
                        st.rerun()