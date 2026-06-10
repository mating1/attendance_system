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

            if status == 'early':
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
                # 获取所有老师的班级
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

            # 如果当前选中的班级不在可选列表中，重置
            if st.session_state.selected_class not in class_names:
                st.session_state.selected_class = class_names[0] if class_names else None

            st.markdown(f"### 考勤记录 - {st.session_state.selected_class}")

            col1, col2, col3 = st.columns(3)
            with col1:
                selected_date = st.date_input("选择日期", get_beijing_now())
            with col2:
                selected_period = st.selectbox("选择节次", PERIODS)
            with col3:
                st.write("")  # 占位
                query_clicked = st.button("查询", use_container_width=True)

            date_str = selected_date.strftime('%Y-%m-%d')
            period = selected_period

            # 获取当前班级对应的老师（超级管理员需要知道是哪个老师的课）
            current_teacher_id = st.session_state.teacher_id
            if st.session_state.user_id == SUPER_ADMIN_ID:
                for cls in all_classes:
                    if cls['name'] == st.session_state.selected_class:
                        current_teacher_id = cls['teacher_id']
                        break

            # 存储查询条件和编辑数据到session_state
            if 'query_date' not in st.session_state:
                st.session_state.query_date = None
            if 'query_period' not in st.session_state:
                st.session_state.query_period = None
            if 'query_clicked' not in st.session_state:
                st.session_state.query_clicked = False

            # 点击查询按钮后更新session_state
            if query_clicked:
                # 检查是否有课
                if not has_class(current_teacher_id, selected_class, date_str, period):
                    st.error(f"该班级在 {date_str} {period} 没有课程安排！")
                else:
                    st.session_state.query_date = date_str
                    st.session_state.query_period = period
                    st.session_state.query_clicked = True
                    # 清除编辑器缓存，确保重新加载
                    for key in list(st.session_state.keys()):
                        if key.startswith('editor_data_'):
                            del st.session_state[key]

            # 只有查询过才显示编辑器
            if st.session_state.query_clicked and st.session_state.query_date == date_str and st.session_state.query_period == period:
                # 获取该班级所有学生
                students = get_students_by_class(current_teacher_id, st.session_state.selected_class)

                # 加载当前考勤数据
                df, filepath = load_attendance(current_teacher_id, st.session_state.selected_class, date_str,
                                               period)

                # 构建可编辑的数据表
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

                # 使用唯一的key确保每次都是新数据
                editor_key = f"editor_data_{date_str}_{period}"

                # 使用 data_editor
                edited_df = st.data_editor(
                    edit_data,
                    column_config={
                        "学号": st.column_config.TextColumn("学号", disabled=True),
                        "签到时间": st.column_config.TextColumn("签到时间"),
                        "状态": st.column_config.SelectboxColumn("状态", options=['出勤', '迟到', '缺勤']),
                        "任课老师": st.column_config.TextColumn("任课老师"),
                        "备注": st.column_config.TextColumn("备注"),
                    },
                    hide_index=True,
                    use_container_width=True,
                    key=editor_key
                )

                # 从编辑器数据计算汇总
                present_count = sum(1 for row in edited_df if row['状态'] == '出勤')
                late_count = sum(1 for row in edited_df if row['状态'] == '迟到')
                absent_count = sum(1 for row in edited_df if row['状态'] == '缺勤')
                total_count = len(edited_df)

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("出勤", present_count)
                with col2:
                    st.metric("迟到", late_count)
                with col3:
                    st.metric("缺勤", absent_count)
                with col4:
                    st.metric("总计", total_count)

                st.write("---")

                # 保存按钮
                if st.button("保存修改", use_container_width=True, type="primary"):
                    for row in edited_df:
                        student_id = row["学号"]
                        new_status = str(row["状态"])
                        remark = str(row.get("备注", ""))
                        checkin_time = str(row.get("签到时间", ""))
                        update_attendance_status(
                            current_teacher_id, 
                            st.session_state.selected_class, 
                            date_str,
                            period, 
                            student_id, 
                            new_status, 
                            remark,
                            checkin_time
                        )
                    st.success("保存成功！")
                    st.rerun()

                # 导出按钮
                if st.button("导出CSV", use_container_width=True):
                    filepath = export_to_csv(current_teacher_id, st.session_state.selected_class, date_str, period)
                    with open(filepath, 'rb') as f:
                        st.download_button("下载CSV", f,
                                           file_name=f"考勤_{st.session_state.selected_class}_{date_str}_{period}.csv")

        # ========== 课表设置页面 ==========
        elif st.session_state.page == 'schedule':
            st.markdown(f"### 课表设置 - {st.session_state.selected_class}")

            selected_weekday = st.selectbox("选择星期", WEEKDAYS)

            schedule = load_teacher_schedule(st.session_state.teacher_id, st.session_state.selected_class)
            weekday_schedule = schedule.get(selected_weekday, {})

            st.write("---")

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

            for period in PERIODS:
                period_data = weekday_schedule.get(period, DEFAULT_PERIOD_TIMES[period].copy())

                col1, col2, col3, col4, col5 = st.columns([0.5, 1, 1, 1, 1])
                with col1:
                    enabled = st.checkbox("", value=period_data.get('enabled', False),
                                          key=f"en_{st.session_state.selected_class}_{selected_weekday}_{period}")
                with col2:
                    st.write(period)
                with col3:
                    start_time = st.time_input("上课",
                                               value=datetime.strptime(period_data['start_time'], '%H:%M').time(),
                                               key=f"start_{st.session_state.selected_class}_{selected_weekday}_{period}",
                                               label_visibility="collapsed")
                with col4:
                    early_start = st.time_input("签到开始",
                                                value=datetime.strptime(period_data['early_start'], '%H:%M').time(),
                                                key=f"early_{st.session_state.selected_class}_{selected_weekday}_{period}",
                                                label_visibility="collapsed")
                with col5:
                    late_end = st.time_input("迟到截止",
                                             value=datetime.strptime(period_data['late_end'], '%H:%M').time(),
                                             key=f"late_{st.session_state.selected_class}_{selected_weekday}_{period}",
                                             label_visibility="collapsed")

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

            if st.button("保存课表", use_container_width=True, type="primary"):
                save_teacher_schedule(st.session_state.teacher_id, st.session_state.selected_class, schedule)
                st.success(f"{st.session_state.selected_class} {selected_weekday} 课表保存成功")

        # ========== 班级管理页面 ==========
        elif st.session_state.page == 'class':
            st.markdown("### 班级管理")

            tab1, tab2 = st.tabs(["添加班级", "现有班级"])

            with tab1:
                st.markdown("#### 添加新班级")

                next_num = get_next_class_number(st.session_state.teacher_id)
                default_name = f'{next_num}班'
                default_prefix = str(next_num)

                class_name = st.text_input("班级名称", value=default_name)
                prefix = st.text_input("班级前缀（学号首位）", value=default_prefix)
                student_count = st.number_input("学生人数", min_value=1, max_value=99, value=33, step=1)

                if st.button("添加班级", use_container_width=True, type="primary"):
                    if not class_name or not prefix:
                        st.error("请填写完整信息")
                    else:
                        ok, msg = add_teacher_class(st.session_state.teacher_id, class_name, prefix, student_count)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

            with tab2:
                st.markdown("#### 现有班级")
                classes = get_teacher_class_list(st.session_state.teacher_id)

                for cls in classes:
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    with col1:
                        st.write(f"**{cls['name']}**")
                    with col2:
                        st.write(f"前缀: {cls['prefix']}")
                    with col3:
                        st.write(f"人数: {cls['student_count']}")
                    with col4:
                        if cls['name'] not in ['一班', '二班', '三班']:
                            if st.button("删除", key=f"del_{cls['name']}", use_container_width=True):
                                ok, msg = remove_teacher_class(st.session_state.teacher_id, cls['name'])
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                    st.divider()

                st.markdown("#### 修改班级人数")
                class_to_edit = st.selectbox("选择班级", [c['name'] for c in classes])
                new_count = st.number_input("新人数", min_value=1, max_value=99, value=33, step=1)
                if st.button("修改人数", use_container_width=True):
                    ok, msg = update_class_student_count(st.session_state.teacher_id, class_to_edit, new_count)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
