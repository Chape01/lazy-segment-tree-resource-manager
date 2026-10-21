import streamlit as st
import pandas as pd

from src.manager import CloudResourceManager
from src.models import Task
from src.observers import StatsCollector
from src.policies import StrictPolicy, ReservePolicy


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Cloud Resource Allocation",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# CUSTOM CSS  (CRT / retro terminal theme)
# --------------------------------------------------
# Palette
#   background  : #050a06  (CRT black-green)
#   panel       : #0b140d
#   phosphor    : #39ff6a  (primary green)
#   amber       : #ffb000  (accent)
#   cyan        : #35e0ff  (info)
#   red         : #ff4d4d  (errors)
#   text        : #c9ffd8  (high-contrast soft green-white)

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap');

        :root {
            --bg: #050a06;
            --panel: #0b140d;
            --panel-2: #102014;
            --border: #1f5a30;
            --phosphor: #39ff6a;
            --amber: #ffb000;
            --cyan: #35e0ff;
            --red: #ff4d4d;
            --text: #c9ffd8;
            --muted: #7fb892;
            color-scheme: dark;
        }

        /* ---------- Base ---------- */
        html, body, .stApp, [class*="css"] {
            font-family: 'Share Tech Mono', 'Courier New', monospace;
            color: var(--text);
        }

        .stApp {
            background:
                radial-gradient(ellipse at center, #0c1a0f 0%, #050a06 70%, #020403 100%);
        }

        /* CRT scanlines + vignette overlay (does not block clicks) */
        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            z-index: 9999;
            background:
                repeating-linear-gradient(
                    to bottom,
                    rgba(0, 0, 0, 0) 0px,
                    rgba(0, 0, 0, 0) 2px,
                    rgba(0, 0, 0, 0.18) 3px
                );
        }

        .stApp::after {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            z-index: 9998;
            box-shadow: inset 0 0 160px rgba(0, 0, 0, 0.65);
        }

        header[data-testid="stHeader"] {
            background: transparent;
        }

        header[data-testid="stHeader"] * {
            color: var(--muted) !important;
        }

        .block-container {
            padding-top: 2rem;
            max-width: 1300px;
        }

        /* ---------- Headings ---------- */
        h1, h2, h3, h4, h5 {
            font-family: 'VT323', monospace !important;
            color: var(--phosphor) !important;
            letter-spacing: 1px;
            text-shadow: 0 0 8px rgba(57, 255, 106, 0.55);
        }

        h2 { font-size: 2rem !important; }
        h3 { font-size: 1.7rem !important; }

        p, li, label, span, div[data-testid="stMarkdownContainer"] {
            color: var(--text);
        }

        label p {
            color: var(--phosphor) !important;
            font-size: 14px !important;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }

        /* ---------- Custom header ---------- */
        .hero {
            border: 2px solid var(--phosphor);
            background: linear-gradient(180deg, #0b140d 0%, #07100a 100%);
            padding: 22px 28px;
            border-radius: 6px;
            margin-bottom: 22px;
            box-shadow:
                0 0 18px rgba(57, 255, 106, 0.35),
                inset 0 0 24px rgba(57, 255, 106, 0.08);
        }

        .hero-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
            color: var(--muted);
            border-bottom: 1px dashed var(--border);
            padding-bottom: 8px;
            margin-bottom: 12px;
            letter-spacing: 1px;
        }

        .status-dot {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--phosphor);
            box-shadow: 0 0 10px var(--phosphor);
            margin-right: 8px;
            animation: pulse 1.6s infinite;
        }

        .main-title {
            font-family: 'VT323', monospace;
            font-size: 52px;
            line-height: 1.05;
            color: var(--phosphor);
            text-shadow:
                0 0 6px rgba(57, 255, 106, 0.9),
                0 0 22px rgba(57, 255, 106, 0.45);
            margin-bottom: 6px;
        }

        .main-title::after {
            content: "█";
            margin-left: 8px;
            color: var(--amber);
            animation: blink 1s steps(1) infinite;
        }

        .subtitle {
            color: var(--amber);
            font-size: 16px;
            letter-spacing: 1px;
        }

        .subtitle::before {
            content: "> ";
            color: var(--phosphor);
        }

        .section-title {
            font-family: 'VT323', monospace;
            font-size: 28px;
            color: var(--phosphor);
            text-shadow: 0 0 8px rgba(57, 255, 106, 0.5);
            border-left: 4px solid var(--amber);
            padding-left: 12px;
            margin: 14px 0 10px 0;
        }

        @keyframes blink {
            0%, 49% { opacity: 1; }
            50%, 100% { opacity: 0; }
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.35; }
        }

        /* ---------- Sidebar ---------- */
        section[data-testid="stSidebar"] {
            background: #07100a;
            border-right: 2px solid var(--border);
            box-shadow: 4px 0 18px rgba(57, 255, 106, 0.12);
        }

        section[data-testid="stSidebar"] * {
            color: var(--text);
        }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: var(--phosphor) !important;
        }

        /* ---------- Metric cards ---------- */
        div[data-testid="stMetric"] {
            background: var(--panel);
            border: 1px solid var(--border);
            border-top: 3px solid var(--phosphor);
            padding: 16px 18px;
            border-radius: 6px;
            box-shadow:
                0 0 12px rgba(57, 255, 106, 0.15),
                inset 0 0 16px rgba(57, 255, 106, 0.05);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }

        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow:
                0 0 20px rgba(57, 255, 106, 0.4),
                inset 0 0 16px rgba(57, 255, 106, 0.08);
        }

        div[data-testid="stMetricLabel"] p {
            color: var(--muted) !important;
            font-size: 13px !important;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        div[data-testid="stMetricValue"] {
            font-family: 'VT323', monospace;
            font-size: 2.6rem;
            color: var(--amber) !important;
            text-shadow: 0 0 10px rgba(255, 176, 0, 0.55);
        }

        /* ---------- Buttons ---------- */
        div.stButton > button,
        div[data-testid="stFormSubmitButton"] > button {
            font-family: 'Share Tech Mono', monospace;
            background: transparent;
            color: var(--phosphor);
            border: 2px solid var(--phosphor);
            border-radius: 4px;
            font-weight: 700;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            box-shadow: 0 0 10px rgba(57, 255, 106, 0.3);
            transition: all 0.15s ease;
        }

        div.stButton > button:hover,
        div[data-testid="stFormSubmitButton"] > button:hover {
            background: var(--phosphor);
            color: #031004;
            box-shadow: 0 0 22px rgba(57, 255, 106, 0.8);
            border-color: var(--phosphor);
        }

        div.stButton > button:active,
        div[data-testid="stFormSubmitButton"] > button:active {
            transform: scale(0.98);
        }

        /* ---------- Inputs ---------- */
        div[data-baseweb="input"],
        div[data-baseweb="base-input"],
        div[data-baseweb="select"] > div,
        div[data-baseweb="textarea"] {
            background-color: #040804 !important;
            border: 1px solid var(--border) !important;
            border-radius: 4px !important;
        }

        div[data-baseweb="input"]:focus-within,
        div[data-baseweb="select"] > div:focus-within {
            border-color: var(--phosphor) !important;
            box-shadow: 0 0 10px rgba(57, 255, 106, 0.5) !important;
        }

        input, textarea {
            color: var(--phosphor) !important;
            font-family: 'Share Tech Mono', monospace !important;
            caret-color: var(--amber);
            -webkit-text-fill-color: var(--phosphor) !important;
        }

        input::placeholder {
            color: #4f8a62 !important;
            -webkit-text-fill-color: #4f8a62 !important;
        }

        div[data-baseweb="select"] span,
        div[data-baseweb="select"] div {
            color: var(--phosphor) !important;
        }

        ul[role="listbox"] {
            background: #07100a !important;
            border: 1px solid var(--phosphor);
        }

        ul[role="listbox"] li {
            color: var(--text) !important;
        }

        ul[role="listbox"] li:hover {
            background: var(--panel-2) !important;
        }

        button[data-testid="stNumberInputStepUp"],
        button[data-testid="stNumberInputStepDown"] {
            background: var(--panel-2);
            color: var(--phosphor);
        }

        /* Slider */
        div[data-testid="stSlider"] [role="slider"] {
            background-color: var(--phosphor) !important;
            box-shadow: 0 0 10px var(--phosphor);
        }

        div[data-testid="stSlider"] div[data-testid="stTickBarMin"],
        div[data-testid="stSlider"] div[data-testid="stTickBarMax"] {
            color: var(--muted);
        }

        /* ---------- Forms ---------- */
        div[data-testid="stForm"] {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 18px;
            box-shadow: inset 0 0 20px rgba(57, 255, 106, 0.05);
        }

        /* ---------- Tabs ---------- */
        div[data-baseweb="tab-list"] {
            gap: 6px;
            border-bottom: 2px solid var(--border);
        }

        button[data-baseweb="tab"] {
            font-family: 'Share Tech Mono', monospace;
            background: var(--panel);
            border: 1px solid var(--border);
            border-bottom: none;
            border-radius: 6px 6px 0 0;
            padding: 10px 18px;
            color: var(--muted);
            letter-spacing: 1px;
        }

        button[data-baseweb="tab"] p {
            color: inherit !important;
            font-size: 15px !important;
            text-transform: none;
        }

        button[data-baseweb="tab"]:hover {
            color: var(--phosphor);
            background: var(--panel-2);
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            background: var(--phosphor);
            color: #031004;
            font-weight: 700;
            box-shadow: 0 0 14px rgba(57, 255, 106, 0.6);
        }

        div[data-baseweb="tab-highlight"] {
            background-color: var(--amber) !important;
        }

        div[data-baseweb="tab-border"] {
            background-color: var(--border) !important;
        }

        /* ---------- Alerts ---------- */
        div[data-testid="stAlert"] {
            background: var(--panel);
            border: 1px solid var(--border);
            border-left: 5px solid var(--cyan);
            border-radius: 4px;
            color: var(--text);
        }

        div[data-testid="stAlert"] p {
            color: var(--text) !important;
        }

        div[data-testid="stAlertContentSuccess"] {
            border-left-color: var(--phosphor);
        }

        div[data-testid="stAlertContentError"] {
            border-left-color: var(--red);
        }

        div[data-testid="stAlertContentWarning"] {
            border-left-color: var(--amber);
        }

        /* ---------- Tables / charts ---------- */
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 6px;
            box-shadow: 0 0 12px rgba(57, 255, 106, 0.12);
            overflow: hidden;
        }

        div[data-testid="stArrowVegaLiteChart"],
        div[data-testid="stVegaLiteChart"] {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 10px;
        }

        /* ---------- Expander ---------- */
        div[data-testid="stExpander"] {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 6px;
        }

        div[data-testid="stExpander"] summary p {
            color: var(--amber) !important;
        }

        /* ---------- Misc ---------- */
        hr {
            border: none;
            border-top: 1px dashed var(--border);
        }

        div[data-testid="stCaptionContainer"] p,
        small {
            color: var(--muted) !important;
        }

        ::-webkit-scrollbar { width: 10px; height: 10px; }
        ::-webkit-scrollbar-track { background: #040804; }
        ::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 5px;
        }
        ::-webkit-scrollbar-thumb:hover { background: var(--phosphor); }

        ::selection { background: var(--phosphor); color: #031004; }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

# Streamlit reruns the script after most user actions.
# Session state preserves the manager between reruns.

if "manager" not in st.session_state:
    st.session_state.manager = None

if "stats" not in st.session_state:
    st.session_state.stats = None

if "configuration" not in st.session_state:
    st.session_state.configuration = None


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def crt_style(df):
    """Give tables dark CRT colours. Falls back to the plain table on any problem."""
    try:
        return df.style.set_properties(
            **{
                "background-color": "#050a06",
                "color": "#c9ffd8",
            }
        )
    except Exception:
        return df


def initialize_manager(total_cpu, time_slots, policy_name, reserve_ratio):
    """Create the existing backend manager."""

    if policy_name == "Reserve":
        policy = ReservePolicy(reserve_ratio)
    else:
        policy = StrictPolicy()

    manager = CloudResourceManager(
        total_cpu=total_cpu,
        time_slots=time_slots,
        policy=policy,
    )

    stats = StatsCollector()
    manager.add_observer(stats)

    st.session_state.manager = manager
    st.session_state.stats = stats
    st.session_state.configuration = (
        total_cpu,
        time_slots,
        policy_name,
        reserve_ratio,
    )


def get_manager():
    """Return the configured manager, if one exists."""
    return st.session_state.manager


def show_cpu_chart(manager):
    """Display free and used CPU for every time slot."""

    free_cpu = manager.usage_report()

    df = pd.DataFrame(
        {
            "Time Slot": list(range(manager.time_slots)),
            "Free CPU": free_cpu,
            "Used CPU": [
                manager.total_cpu - free
                for free in free_cpu
            ],
        }
    )

    st.markdown(
        '<p class="section-title">CPU Usage by Time Slot</p>',
        unsafe_allow_html=True,
    )

    chart_df = df.set_index("Time Slot")[
        ["Free CPU", "Used CPU"]
    ]

    # Green = free, amber = used (matches the CRT theme)
    st.bar_chart(chart_df, color=["#39ff6a", "#ffb000"])

    with st.expander("View detailed CPU usage table"):
        st.dataframe(
            crt_style(df),
            use_container_width=True,
            hide_index=True,
        )


def show_active_tasks(manager):
    """Display active task information."""

    tasks = manager.active_tasks()

    st.markdown(
        '<p class="section-title">Active Tasks</p>',
        unsafe_allow_html=True,
    )

    if not tasks:
        st.info("No active tasks. Allocate a task to get started.")
        return

    df = pd.DataFrame(
        [
            {
                "Task ID": task.task_id,
                "CPU Requested": task.cpu,
                "Start Slot": task.start,
                "End Slot (Exclusive)": task.end,
                "Duration": task.end - task.start,
            }
            for task in tasks
        ]
    )

    st.dataframe(
        crt_style(df),
        use_container_width=True,
        hide_index=True,
    )


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("☁️ CLOUD RESOURCE MANAGER")
st.sidebar.caption("Configuration and navigation")

st.sidebar.subheader("System Configuration")

configured = get_manager() is not None

if configured:
    current = st.session_state.configuration

    st.sidebar.success("Resource manager initialized")

    st.sidebar.write(f"Total CPU: **{current[0]} cores**")
    st.sidebar.write(f"Time slots: **{current[1]}**")
    st.sidebar.write(f"Policy: **{current[2]}**")

    if st.sidebar.button(
        "Reset system",
        use_container_width=True,
    ):
        st.session_state.manager = None
        st.session_state.stats = None
        st.session_state.configuration = None
        st.rerun()

else:
    with st.sidebar.form("configuration_form"):
        total_cpu_input = st.number_input(
            "Total CPU capacity",
            min_value=1,
            max_value=100000,
            value=16,
            step=1,
        )

        time_slots_input = st.number_input(
            "Number of time slots",
            min_value=1,
            max_value=100000,
            value=24,
            step=1,
        )

        policy_input = st.selectbox(
            "Admission policy",
            ["Strict", "Reserve"],
        )

        reserve_input = st.slider(
            "CPU reserve percentage",
            min_value=0,
            max_value=50,
            value=10,
            step=5,
            help="Used only by the Reserve policy.",
        )

        initialize_button = st.form_submit_button(
            "Initialize Resource Manager",
            use_container_width=True,
        )

    if initialize_button:
        try:
            initialize_manager(
                int(total_cpu_input),
                int(time_slots_input),
                policy_input,
                reserve_input / 100,
            )

            st.sidebar.success("System initialized successfully!")
            st.rerun()

        except (ValueError, TypeError) as error:
            st.sidebar.error(str(error))


# --------------------------------------------------
# MAIN HEADER
# --------------------------------------------------

_online = get_manager() is not None
_status_text = "SYSTEM ONLINE" if _online else "AWAITING CONFIGURATION"

st.markdown(
    f"""
    <div class="hero">
        <div class="hero-top">
            <span><span class="status-dot"></span>{_status_text}</span>
            <span>CRT-TERMINAL v1.0 &nbsp;|&nbsp; SEGMENT TREE + LAZY PROP</span>
        </div>
        <div class="main-title">☁️ Cloud Resource Allocation &amp; Monitoring</div>
        <div class="subtitle">
            Efficient CPU scheduling using a Segment Tree with Lazy Propagation.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


manager = get_manager()


if manager is None:
    st.info(
        "👈 Configure your system in the sidebar and click "
        "'Initialize Resource Manager' to begin."
    )

    st.markdown("### Project Overview")

    col1, col2, col3 = st.columns(3)

    col1.info(
        "**Fast availability checks**\n\n"
        "Check the minimum free CPU across a time interval."
    )

    col2.info(
        "**Efficient allocation**\n\n"
        "Range updates use the existing lazy segment tree."
    )

    col3.info(
        "**Live monitoring**\n\n"
        "View CPU usage, active tasks, and utilization."
    )

    st.stop()


# --------------------------------------------------
# DASHBOARD METRICS
# --------------------------------------------------

free_cpu = manager.usage_report()

used_cpu_values = [
    manager.total_cpu - free
    for free in free_cpu
]

total_capacity = manager.total_cpu
total_slots = manager.time_slots

peak_used = manager.peak_usage()
average_utilization = manager.average_utilization() * 100

total_allocated_cpu = sum(used_cpu_values)
average_used_cpu = total_allocated_cpu / total_slots

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total CPU Capacity",
    f"{total_capacity} cores",
)

col2.metric(
    "Peak CPU Usage",
    f"{peak_used} cores",
)

col3.metric(
    "Average CPU Usage",
    f"{average_used_cpu:.2f} cores",
)

col4.metric(
    "Average Utilization",
    f"{average_utilization:.1f}%",
)

st.divider()


# --------------------------------------------------
# NAVIGATION TABS
# --------------------------------------------------

tab_dashboard, tab_allocate, tab_release, tab_check, tab_tasks, tab_stats = (
    st.tabs(
        [
            "📊 Dashboard",
            "➕ Allocate Task",
            "➖ Release Task",
            "🔍 Availability",
            "📋 Active Tasks",
            "📈 Statistics",
        ]
    )
)


# --------------------------------------------------
# DASHBOARD TAB
# --------------------------------------------------

with tab_dashboard:
    st.subheader("Resource Monitoring")

    free_slots = sum(
        1 for free in free_cpu
        if free == total_capacity
    )

    full_slots = sum(
        1 for free in free_cpu
        if free == 0
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Active Tasks",
        len(manager.active_tasks()),
    )

    col2.metric(
        "Completely Free Slots",
        free_slots,
    )

    col3.metric(
        "Fully Utilized Slots",
        full_slots,
    )

    show_cpu_chart(manager)

    st.caption(
        "The chart shows CPU used and CPU free in each time slot. "
        "Changes are calculated by your existing resource manager."
    )


# --------------------------------------------------
# ALLOCATE TASK TAB
# --------------------------------------------------

with tab_allocate:
    st.subheader("Allocate CPU Resources")

    st.write(
        "Enter the task details. The system will accept the task "
        "only if the configured admission policy allows it."
    )

    with st.form("allocate_form"):
        task_id = st.text_input(
            "Task ID",
            placeholder="Example: TASK-001",
        ).strip()

        col1, col2, col3 = st.columns(3)

        with col1:
            start_slot = st.number_input(
                "Start slot (inclusive)",
                min_value=0,
                max_value=manager.time_slots - 1,
                value=0,
                step=1,
            )

        with col2:
            end_slot = st.number_input(
                "End slot (exclusive)",
                min_value=1,
                max_value=manager.time_slots,
                value=min(10, manager.time_slots),
                step=1,
            )

        with col3:
            cpu_required = st.number_input(
                "CPU cores required",
                min_value=1,
                max_value=manager.total_cpu,
                value=min(4, manager.total_cpu),
                step=1,
            )

        allocate_button = st.form_submit_button(
            "Allocate Task",
            use_container_width=True,
        )

    if allocate_button:
        try:
            if not task_id:
                st.error("Please enter a task ID.")

            elif start_slot >= end_slot:
                st.error(
                    "The end slot must be greater than the start slot."
                )

            else:
                task = Task(
                    task_id=task_id,
                    start=int(start_slot),
                    end=int(end_slot),
                    cpu=int(cpu_required),
                )

                result = manager.allocate(task)

                if result.accepted:
                    st.success(
                        f"✅ Task {task_id} accepted! "
                        f"{cpu_required} CPU cores reserved for "
                        f"slots [{start_slot}, {end_slot})."
                    )

                else:
                    st.error(result.message)

        except (ValueError, IndexError) as error:
            st.error(f"Could not allocate task: {error}")


# --------------------------------------------------
# RELEASE TASK TAB
# --------------------------------------------------

with tab_release:
    st.subheader("Release Allocated Resources")

    active_tasks = manager.active_tasks()

    if not active_tasks:
        st.info("There are no active tasks to release.")

    else:
        task_ids = [
            task.task_id
            for task in active_tasks
        ]

        with st.form("release_form"):
            selected_task = st.selectbox(
                "Select a task to release",
                task_ids,
            )

            release_button = st.form_submit_button(
                "Release Task",
                use_container_width=True,
            )

        if release_button:
            if manager.release(selected_task):
                st.success(
                    f"Task {selected_task} released successfully. "
                    "Its reserved CPU is now available."
                )
            else:
                st.error("The selected task could not be released.")


# --------------------------------------------------
# AVAILABILITY TAB
# --------------------------------------------------

with tab_check:
    st.subheader("Check CPU Availability")

    st.write(
        "Check the minimum amount of free CPU across a time interval. "
        "The check does not allocate resources."
    )

    with st.form("availability_form"):
        col1, col2 = st.columns(2)

        with col1:
            check_start = st.number_input(
                "Start slot",
                min_value=0,
                max_value=manager.time_slots - 1,
                value=0,
                step=1,
                key="check_start",
            )

        with col2:
            check_end = st.number_input(
                "End slot (exclusive)",
                min_value=1,
                max_value=manager.time_slots,
                value=min(10, manager.time_slots),
                step=1,
                key="check_end",
            )

        check_button = st.form_submit_button(
            "Check Availability",
            use_container_width=True,
        )

    if check_button:
        try:
            if check_start >= check_end:
                st.error(
                    "The end slot must be greater than the start slot."
                )

            else:
                minimum_free = manager.check_availability(
                    int(check_start),
                    int(check_end),
                )

                st.metric(
                    "Minimum Free CPU",
                    f"{minimum_free} cores",
                )

                st.caption(
                    f"Checked interval [{check_start}, {check_end})."
                )

                st.write(
                    "This is the minimum free CPU across all "
                    "slots in the selected interval."
                )

        except (ValueError, IndexError) as error:
            st.error(str(error))

    st.divider()

    st.subheader("Dry Run: Test a Request")

    st.write(
        "Check whether a hypothetical request would be accepted "
        "without changing the current allocations."
    )

    with st.form("dry_run_form"):
        dry_id = st.text_input(
            "Hypothetical task ID",
            value="TEST-001",
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            dry_start = st.number_input(
                "Start slot",
                min_value=0,
                max_value=manager.time_slots - 1,
                value=0,
                step=1,
                key="dry_start",
            )

        with col2:
            dry_end = st.number_input(
                "End slot (exclusive)",
                min_value=1,
                max_value=manager.time_slots,
                value=min(10, manager.time_slots),
                step=1,
                key="dry_end",
            )

        with col3:
            dry_cpu = st.number_input(
                "CPU requested",
                min_value=1,
                max_value=manager.total_cpu,
                value=min(4, manager.total_cpu),
                step=1,
                key="dry_cpu",
            )

        dry_button = st.form_submit_button(
            "Run Dry Test",
            use_container_width=True,
        )

    if dry_button:
        try:
            if dry_start >= dry_end:
                st.error(
                    "The end slot must be greater than the start slot."
                )

            elif not dry_id.strip():
                st.error("Please enter a hypothetical task ID.")

            elif dry_id.strip() in {
                task.task_id for task in manager.active_tasks()
            }:
                st.error(
                    "This task ID is already active. "
                    "Choose a different ID for the dry run."
                )

            else:
                would_fit = manager.can_fit(
                    int(dry_start),
                    int(dry_end),
                    int(dry_cpu),
                )

                if would_fit:
                    st.success(
                        "✅ The request would be accepted "
                        "under the current admission policy."
                    )
                else:
                    conflict_slot = manager.first_conflict_slot(
                        int(dry_start),
                        int(dry_end),
                        int(dry_cpu),
                    )

                    if conflict_slot != -1:
                        st.error(
                            "❌ The request would be rejected. "
                            f"Insufficient free CPU at slot {conflict_slot}."
                        )
                    else:
                        st.error(
                            "❌ The request would be rejected "
                            "because it violates the reserve policy."
                        )

        except (ValueError, IndexError) as error:
            st.error(str(error))


# --------------------------------------------------
# ACTIVE TASKS TAB
# --------------------------------------------------

with tab_tasks:
    show_active_tasks(manager)


# --------------------------------------------------
# STATISTICS TAB
# --------------------------------------------------

with tab_stats:
    st.subheader("Allocation Statistics")

    stats = st.session_state.stats

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Accepted Requests",
        stats.accepted,
    )

    col2.metric(
        "Rejected Requests",
        stats.rejected,
    )

    col3.metric(
        "Released Tasks",
        stats.released,
    )

    st.divider()

    st.subheader("CPU Usage Summary")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Peak CPU in Use",
            f"{manager.peak_usage()} cores",
        )

        st.metric(
            "Lowest CPU in Use",
            f"{manager.lowest_usage()} cores",
        )

    with col2:
        st.metric(
            "Average Utilization",
            f"{manager.average_utilization() * 100:.2f}%",
        )

        st.metric(
            "Average Free CPU",
            f"{sum(free_cpu) / len(free_cpu):.2f} cores",
        )

    st.caption(
        "Statistics are collected by your existing StatsCollector. "
        "CPU metrics are calculated by CloudResourceManager."
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Cloud Resource Allocation & Monitoring | "
    "Segment Tree + Lazy Propagation | "
    "Existing backend preserved"
)