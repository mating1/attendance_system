import streamlit as st
from datetime import datetime, timezone, timedelta
from data_manager import *

# 时区设置（北京时间 UTC+8）
BEIJING_TZ = timezone(timedelta(hours=8))

def get_beijing_now():
    """获取北京时间"""
    return datetime.now(BEIJING_TZ)

st.set_page_config(page_title="学生考勤系统", page_icon="📋", layout="wide")

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
    st.session_state.selected_class = None
if 'page' not in st.session_state:
    st.session_state.page = 'attendance'

st.title("📋 学生考勤系统")

# 登录界面
if st.session_state.user_type is None:
    user_id = st.text_input("学号或老师账号", max_chars=5, placeholder="学生:101~333  老师:0001~0004")
    if st.button("登录", use_container_width=True):
        if user_id in TEACHER_IDS or user_id == SUPER_ADMIN_ID:
            st.session_state.user_type = 'teacher'
            st.session_state.user_id = user_id
            st.session_state.teacher_id = user_id
            st.rerun()
        else:
            found = False
            for teacher_id in TEACHER_IDS:
                classes = get_teacher_class_list(teacher_id)
                for cls in classes:
                    students = get_students_by_class(teacher_id, cls['name'])
                    if user_id in students:
                        st.session_state.user_type = 'student'
                        st.session_state.user_id = user_id
                        st.session_state.teacher_id = teacher_id
                        found = True
                        break
                if found:
                    break
            if not found:
                st.error("账号不存在")

# 学生签到页面
elif st.session_state.user_type == 'student':
    student_class = get_class_by_student_id(st.session_state.teacher_id, st.session_state.user_id)

    st.subheader(f"学生签到 - 学号 {st.session_state.user_id} ({student_class})")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("退出", use_container_width=True):
            st.session_state.user_type = None
            st.rerun()

    now = get_beijing_now()
    weekday = WEEKDAY_MAP[now.weekday()]
    st.write(f"当前时间：{now.strftime('%Y-%m-%d %H:%M:%S')} {weekday}")

    if weekday not in WEEKDAYS:
        st.warning("周末无课程")
    else:
        period, schedule = get_current_period_and_teacher(st.session_state.teacher_id, student_class, now)

        if period is None:
            st.warning("当前没有进行中的课程")
        else:
            st.markdown(f"### 📚 {period}")
            st.write(f"上课时间：{schedule['start_time']} - {schedule['end_time']}")
            st.write(f"签到开始：{schedule['early_start']}")
            st.write(f"迟到截止：{schedule['late_end']}")

            status = check_attendance_status(schedule, now)

            # 检查是否已经签到
            date_str = now.strftime('%Y-%m-%d')
            attendance_df, _ = load_attendance(st.session_state.teacher_id, student_class, date_str, period)
            has_checkin = False
            checkin_status = ''
            checkin_time = ''
            if str(st.session_state.user_id) in attendance_df.index:
                checkin_time = attendance_df.loc[str(st.session_state.user_id), '签到时间']
                checkin_status = attendance_df.loc[str(st.session_state.user_id), '状态']
                has_checkin = checkin_time != ''

            # 如果已经签到，显示签到状态
            if has_checkin:
                st.success(f"✅ 已签到 ({checkin_status})")
                st.write(f"签到时间：{checkin_time}")
            elif status == 'early':
                st.error(f"签到时间未到，请在 {schedule['early_start']} 后签到")
            elif status == 'absent':
                st.error("签到时间已过，已记为缺勤，请联系老师补录")
            elif status == 'present':
                if st.button("签到", use_container_width=True, type="primary"):
                    ok, msg = record_attendance(st.session_state.teacher_id, student_class, st.session_state.user_id,
                                                period, '出勤', now.strftime('%H:%M:%S'))
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            elif status == 'late':
                if st.button("签到", use_container_width=True, type="primary"):
                    ok, msg = record_attendance(st.session_state.teacher_id, student_class, st.session_state.user_id,
                                                period, '迟到', now.strftime('%H:%M:%S'))
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

# 老师管理页面
elif st.session_state.user_type == 'teacher':
    st.subheader(f"老师管理 - {st.session_state.user_id}")

    class_list = get_teacher_class_list(st.session_state.teacher_id)
    class_names = [c['name'] for c in class_list]

    if len(class_names) == 0:
        st.warning("暂无班级，请先添加班级")
        st.session_state.page = 'class'
    else:
        if st.session_state.selected_class is None or st.session_state.selected_class not in class_names:
            st.session_state.selected_class = class_names[0]

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            selected_class = st.selectbox("选择班级", class_names, index=class_names.index(
                st.session_state.selected_class) if st.session_state.selected_class in class_names else 0)
            st.session_state.selected_class = selected_class
        with col2:
            if st.button("考勤记录", use_container_width=True):
                st.session_state.page = 'attendance'
        with col3:
            if st.button("课表设置", use_container_width=True):
                st.session_state.page = 'schedule'
        with col4:
            if st.button("班级管理", use_container_width=True):
                st.session_state.page = 'class'
        with col5:
            if st.button("退出登录", use_container_width=True):
                st.session_state.user_type = None
                st.session_state.selected_class = None
                st.rerun()

        st.divider()

        # ========== 考勤记录页面 ==========
        if st.session_state.page == 'attendance':
            # 超级管理员可以看到所有班级
            if st.session_state.user_id == SUPER_ADMIN_ID:
                all_classes = []
                for tid in TEACHER_IDS:
                    classes = get_teacher_class_list(tid)
                    for cls in classes:
                        cls['teacher_id'] = tid
                        all_classes.append(cls)
                class_names = [c['name'] for c in all_classes]
            else:
                class_list = get_teacher_class_list(st.session_state.teacher_id)
                class_names = [c['name'] for c in class_list]

            if st.session_state.selected_class not in class_names:
                st.session_state.selected_class = class_names[0] if class_names else None

            st.markdown(f"### 考勤记录 - {st.session_state.selected_class}")

            col1, col2, col3 = st.columns(3)
            with col1:
                selected_date = st.date_input("选择日期", get_beijing_now())
            with col2:
                selected_period = st.selectbox("选择节次", PERIODS, key="attendance_period_select")
            with col3:
                st.write("")
                query_clicked = st.button("查询", use_container_width=True)

            date_str = selected_date.strftime('%Y-%m-%d')
            period = selected_period

            current_teacher_id = st.session_state.teacher_id
            if st.session_state.user_id == SUPER_ADMIN_ID:
                for cls in all_classes:
                    if cls['name'] == st.session_state.selected_class:
                        current_teacher_id = cls['teacher_id']
                        break

            if 'query_date' not in st.session_state:
                st.session_state.query_date = None
            if 'query_period' not in st.session_state:
                st.session_state.query_period = None
            if 'query_clicked' not in st.session_state:
                st.session_state.query_clicked = False

            if query_clicked:
                if not has_class(current_teacher_id, st.session_state.selected_class, date_str, period):
                    st.error(f"该班级在 {date_str} {period} 没有课程安排！")
                else:
                    st.session_state.query_date = date_str
                    st.session_state.query_period = period
                    st.session_state.query_clicked = True
                    for key in list(st.session_state.keys()):
                        if key.startswith('editor_data_'):
                            del st.session_state[key]

            if st.session_state.query_clicked and st.session_state.query_date == date_str and st.session_state.query_period == period:
                students = get_students_by_class(current_teacher_id, st.session_state.selected_class)

                df, filepath = load_attendance(current_teacher_id, st.session_state.selected_class, date_str, period)

                edit_data = []
                for student_id in students:
                    row = {
                        "学号": student_id,
                        "签到时间": df.loc[student_id, '签到时间'] if student_id in df.index else '',
                        "状态": df.loc[student_id, '状态'] if student_id in df.index else '缺勤',
                        "任课老师": df.loc[student_id, '任课老师'] if student_id in df.index else current_teacher_id,
                        "备注": df.loc[student_id, '备注'] if student_id in df.index else ''
                    }
                    edit_data.append(row)

                editor_key = f"editor_data_{date_str}_{period}"

                edited_df = st.data_editor(
                    edit_data,
                    column_config={
                        "学号": st.column_config.TextColumn("学号", disabled=True),
                        "签到时间": st.column_config.TextColumn("签到时间"),
                        "状态": st.column_config.SelectboxColumn("状态", options=['出勤', '迟到', '缺勤'], required=True),
                        "任课老师": st.column_config.TextColumn("任课老师", disabled=True),
                        "备注": st.column_config.TextColumn("备注")
                    },
                    key=editor_key,
                    use_container_width=True
                )

                if st.button("保存修改", use_container_width=True, type="primary"):
                    for row in edited_df:
                        student_id = row["学号"]
                        new_status = row["状态"]
                        remark = row["备注"]
                        checkin_time = row["签到时间"]
                        update_attendance_status(current_teacher_id, st.session_state.selected_class, date_str, period, student_id, new_status, remark, checkin_time)
                    st.success("修改已保存！")
                    for key in list(st.session_state.keys()):
                        if key.startswith('editor_data_'):
                            del st.session_state[key]
                    st.rerun()

        # ========== 课表设置页面 ==========
        elif st.session_state.page == 'schedule':
            st.markdown("### 课表设置")
            
            selected_weekday = st.selectbox("选择星期", WEEKDAYS, key="schedule_weekday_select")
            
            st.write(f"#### {selected_weekday} 的课程安排")
            
            # 使用正确的函数名
            schedule_data = load_teacher_schedule(st.session_state.teacher_id, st.session_state.selected_class)
            
            for idx, period in enumerate(PERIODS[:10]):
                period_data = schedule_data.get(selected_weekday, {}).get(period, {})
                
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                with col1:
                    st.write(f"**{period}**")
                with col2:
                    enabled = st.checkbox("启用", value=period_data.get('enabled', False), key=f"enable_{selected_weekday}_{period}_{idx}")
                with col3:
                    start_time = st.time_input("开始时间", value=datetime.strptime(period_data.get('start_time', '08:20'), '%H:%M').time(), key=f"start_{selected_weekday}_{period}_{idx}")
                with col4:
                    end_time = st.time_input("结束时间", value=datetime.strptime(period_data.get('end_time', '09:00'), '%H:%M').time(), key=f"end_{selected_weekday}_{period}_{idx}")
                with col5:
                    early_start = st.time_input("签到开始", value=datetime.strptime(period_data.get('early_start', '08:10'), '%H:%M').time(), key=f"early_{selected_weekday}_{period}_{idx}")
                with col6:
                    late_end = st.time_input("迟到截止", value=datetime.strptime(period_data.get('late_end', '08:30'), '%H:%M').time(), key=f"late_{selected_weekday}_{period}_{idx}")
                
                if enabled:
                    if not schedule_data.get(selected_weekday):
                        schedule_data[selected_weekday] = {}
                    schedule_data[selected_weekday][period] = {
                        'enabled': enabled,
                        'start_time': start_time.strftime('%H:%M'),
                        'end_time': end_time.strftime('%H:%M'),
                        'early_start': early_start.strftime('%H:%M'),
                        'late_end': late_end.strftime('%H:%M')
                    }
            
            if st.button("保存课表", use_container_width=True, type="primary"):
                # 使用正确的函数名
                save_teacher_schedule(st.session_state.teacher_id, st.session_state.selected_class, schedule_data)
                st.success("课表已保存！")

        # ========== 班级管理页面 ==========
        elif st.session_state.page == 'class':
            st.markdown("### 班级管理")
            
            new_class_name = st.text_input("新班级名称", key="new_class_name_input")
            if st.button("添加班级", use_container_width=True, key="add_class_button"):
                if new_class_name:
                    add_teacher_class(st.session_state.teacher_id, new_class_name)
                    st.success(f"班级 {new_class_name} 添加成功！")
                    st.rerun()
                else:
                    st.error("请输入班级名称")
            
            st.divider()
            
            st.markdown("#### 班级列表")
            class_list = get_teacher_class_list(st.session_state.teacher_id)
            
            for idx, cls in enumerate(class_list):
                col1, col2, col3 = st.columns([2, 3, 1])
                with col1:
                    st.write(f"**{cls['name']}**")
                with col2:
                    st.write(f"学生数: {len(get_students_by_class(st.session_state.teacher_id, cls['name']))}")
                with col3:
                    if st.button(f"删除", key=f"del_class_{cls['name']}_{idx}", use_container_width=True):
                        remove_teacher_class(st.session_state.teacher_id, cls['name'])
                        st.success(f"班级 {cls['name']} 删除成功！")
                        st.rerun()
            
            st.divider()
            
            st.markdown("#### 添加学生")
            class_list_for_student = get_teacher_class_list(st.session_state.teacher_id)
            class_names_for_student = [c['name'] for c in class_list_for_student]
            
            # 使用唯一的key
            selected_class_for_student = st.selectbox("选择班级", class_names_for_student, key="add_student_class_select")
            new_student_id = st.text_input("学生学号", key="new_student_id_input")
            
            if st.button("添加学生", use_container_width=True, key="add_student_button"):
                if new_student_id and selected_class_for_student:
                    add_student_to_class(st.session_state.teacher_id, selected_class_for_student, new_student_id)
                    st.success(f"学生 {new_student_id} 添加到 {selected_class_for_student} 成功！")
                    st.rerun()
                else:
                    st.error("请输入学号并选择班级")
