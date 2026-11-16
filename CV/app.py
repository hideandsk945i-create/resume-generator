import streamlit as st
import sqlite3
import hashlib
from fpdf import FPDF

# إعدادات الصفحة الأساسية
st.set_page_config(page_title="Resume Generator", layout="wide")

# ==========================================
# 1. إعداد قاعدة البيانات (SQLite)
# ==========================================
def init_db():
    conn = sqlite3.connect("resumes.db")
    c = conn.cursor()
    # جدول المستخدمين
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    # جدول السير الذاتية
    c.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            location TEXT,
            summary TEXT,
            skills TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(email, password):
    conn = sqlite3.connect("resumes.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(email, password):
    conn = sqlite3.connect("resumes.db")
    c = conn.cursor()
    c.execute("SELECT id, email FROM users WHERE email = ? AND password = ?", (email, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

def get_user_resumes(user_id):
    conn = sqlite3.connect("resumes.db")
    c = conn.cursor()
    c.execute("SELECT id, title, full_name, email, phone, location, summary, skills FROM resumes WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def create_resume(user_id):
    conn = sqlite3.connect("resumes.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO resumes (user_id, title, full_name, email, phone, location, summary, skills)
        VALUES (?, 'My CV', '', '', '', '', '', '')
    """, (user_id,))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return new_id

def get_resume_by_id(resume_id, user_id):
    conn = sqlite3.connect("resumes.db")
    c = conn.cursor()
    c.execute("SELECT id, title, full_name, email, phone, location, summary, skills FROM resumes WHERE id = ? AND user_id = ?", (resume_id, user_id))
    row = c.fetchone()
    conn.close()
    return row

def update_resume(resume_id, user_id, title, full_name, email, phone, location, summary, skills):
    conn = sqlite3.connect("resumes.db")
    c = conn.cursor()
    c.execute("""
        UPDATE resumes 
        SET title = ?, full_name = ?, email = ?, phone = ?, location = ?, summary = ?, skills = ?
        WHERE id = ? AND user_id = ?
    """, (title, full_name, email, phone, location, summary, skills, resume_id, user_id))
    conn.commit()
    conn.close()

def delete_resume(resume_id, user_id):
    conn = sqlite3.connect("resumes.db")
    c = conn.cursor()
    c.execute("DELETE FROM resumes WHERE id = ? AND user_id = ?", (resume_id, user_id))
    conn.commit()
    conn.close()

# ==========================================
# 2. دالة توليد ملف PDF
# ==========================================
def generate_pdf_bytes(full_name, email, phone, location, summary, skills):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # الاسم الكامل
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 12, full_name if full_name else "Your Name", ln=True)

    # بيانات التواصل
    pdf.set_font("Helvetica", "", 10)
    contact_parts = [p for p in [email, phone, location] if p.strip()]
    if contact_parts:
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 8, " | ".join(contact_parts), ln=True)
    
    pdf.ln(4)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # النبذة التعريفية (Summary)
    if summary.strip():
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Professional Summary", ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 6, summary)
        pdf.ln(6)

    # المهارات (Skills)
    if skills.strip():
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Skills", ln=True)
        pdf.set_font("Helvetica", "", 11)
        skill_list = [s.strip() for s in skills.split(",") if s.strip()]
        pdf.multi_cell(0, 6, " • ".join(skill_list))

    return bytes(pdf.output())

# تشغيل تهيئة قاعدة البيانات
init_db()

# إدارة حالة الجلسة (Session State)
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "current_resume_id" not in st.session_state:
    st.session_state.current_resume_id = None

# ==========================================
# 3. القائمة الجانبية (Sidebar)
# ==========================================
with st.sidebar:
    if st.button("📁 Dashboard", use_container_width=True, type="secondary" if st.session_state.page != "Dashboard" else "primary"):
        if st.session_state.user:
            st.session_state.page = "Dashboard"
            st.rerun()

    if st.button("✏️ Editor", use_container_width=True, type="secondary" if st.session_state.page != "Editor" else "primary"):
        if st.session_state.user:
            if not st.session_state.current_resume_id:
                resumes = get_user_resumes(st.session_state.user["id"])
                if resumes:
                    st.session_state.current_resume_id = resumes[0][0]
                else:
                    st.session_state.current_resume_id = create_resume(st.session_state.user["id"])
            st.session_state.page = "Editor"
            st.rerun()

    if st.session_state.user:
        st.divider()
        st.caption("Signed in as")
        st.markdown(f"**{st.session_state.user['email']}**")
        if st.button("Log out", use_container_width=True):
            st.session_state.user = None
            st.session_state.current_resume_id = None
            st.session_state.page = "Dashboard"
            st.rerun()

# ==========================================
# 4. شاشة تسجيل الدخول وإنشاء الحساب
# ==========================================
if not st.session_state.user:
    st.title("Resume Generator")
    tab_login, tab_register = st.tabs(["Log in", "Register"])

    with tab_login:
        with st.container(border=True):
            st.subheader("Sign in to your account")
            login_email = st.text_input("Email", key="login_email")
            login_pass = st.text_input("Password", type="password", key="login_pass")
            if st.button("Log in", use_container_width=True):
                if login_email and login_pass:
                    user = login_user(login_email.strip(), login_pass)
                    if user:
                        st.session_state.user = {"id": user[0], "email": user[1]}
                        st.session_state.page = "Dashboard"
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")
                else:
                    st.warning("Please enter both email and password.")

    with tab_register:
        with st.container(border=True):
            st.subheader("Create an account")
            reg_email = st.text_input("Email", key="reg_email")
            reg_pass = st.text_input("Password", type="password", key="reg_pass")
            reg_confirm = st.text_input("Confirm password", type="password", key="reg_confirm")
            if st.button("Create account", use_container_width=True):
                if not reg_email or not reg_pass or not reg_confirm:
                    st.warning("Please fill in all fields.")
                elif reg_pass != reg_confirm:
                    st.error("Passwords do not match.")
                else:
                    if register_user(reg_email.strip(), reg_pass):
                        st.success("Account created successfully! Please switch to the 'Log in' tab.")
                    else:
                        st.error("An account with this email already exists.")

# ==========================================
# 5. شاشة لوحة التحكم (Dashboard)
# ==========================================
elif st.session_state.page == "Dashboard":
    st.title("Your resumes")
    
    if st.button("➕ New resume"):
        new_id = create_resume(st.session_state.user["id"])
        st.session_state.current_resume_id = new_id
        st.session_state.page = "Editor"
        st.rerun()

    resumes = get_user_resumes(st.session_state.user["id"])
    
    if not resumes:
        st.info("No resumes yet. Click **New resume** to create one.")
    else:
        for r in resumes:
            r_id, r_title, r_name, r_email, r_phone, r_loc, r_sum, r_skills = r
            with st.container(border=True):
                col1, col2, col3 = st.columns([6, 1, 1])
                with col1:
                    st.subheader(r_title)
                    st.caption(f"Name: {r_name if r_name else 'Not set'}")
                with col2:
                    if st.button("Edit", key=f"edit_{r_id}", use_container_width=True):
                        st.session_state.current_resume_id = r_id
                        st.session_state.page = "Editor"
                        st.rerun()
                with col3:
                    if st.button("Delete", key=f"del_{r_id}", use_container_width=True):
                        delete_resume(r_id, st.session_state.user["id"])
                        st.rerun()

# ==========================================
# 6. شاشة المحرر والمعاينة الحية (Editor)
# ==========================================
elif st.session_state.page == "Editor":
    resume_data = get_resume_by_id(st.session_state.current_resume_id, st.session_state.user["id"])
    
    if not resume_data:
        st.session_state.page = "Dashboard"
        st.rerun()

    r_id, r_title, r_name, r_email, r_phone, r_loc, r_sum, r_skills = resume_data

    if st.button("← Back to dashboard"):
        st.session_state.page = "Dashboard"
        st.rerun()

    st.header(f"Editing: {r_title}")

    col_form, col_preview = st.columns([1.2, 1], gap="large")

    # العمود الأيسر: نموذج الإدخال
    with col_form:
        with st.container(border=True):
            title = st.text_input("Resume title", value=r_title)
            
            st.subheader("Personal details")
            full_name = st.text_input("Full name", value=r_name)
            email = st.text_input("Email", value=r_email)
            phone = st.text_input("Phone", value=r_phone)
            location = st.text_input("Location", value=r_loc)
            summary = st.text_area("Summary", value=r_sum, height=120)

            st.subheader("Skills")
            skills = st.text_area("Comma-separated skills", value=r_skills, height=100)
            st.caption("Work experience, education, and projects support full add/remove editing in a future iteration — this form covers the fields needed for a complete first pass.")

            if st.button("💾 Save", use_container_width=True):
                update_resume(r_id, st.session_state.user["id"], title, full_name, email, phone, location, summary, skills)
                st.success("Resume saved successfully!")
                st.rerun()

        # زر توليد وتحميل PDF
        pdf_bytes = generate_pdf_bytes(full_name, email, phone, location, summary, skills)
        st.download_button(
            label="🖨️ Generate PDF",
            data=pdf_bytes,
            file_name=f"{title.replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    # العمود الأيمن: المعاينة الحية (Live Preview)
    with col_preview:
        st.subheader("Live preview")
        with st.container(border=True):
            st.markdown(f"## {full_name if full_name.strip() else 'Your Name'}")
            
            contact_info = [item for item in [email, phone, location] if item.strip()]
            if contact_info:
                st.caption(" | ".join(contact_info))
            
            st.divider()
            
            if summary.strip():
                st.markdown("**Professional Summary**")
                st.write(summary)
                st.write("")
                
            if skills.strip():
                st.markdown("**Skills**")
                skills_list = [s.strip() for s in skills.split(",") if s.strip()]
                st.write(" • ".join(skills_list))