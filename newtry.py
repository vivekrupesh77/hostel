import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from datetime import datetime
import re

# ----------------- DB CONFIG -----------------
DB_CONFIG = {
    "host": "localhost",
    "user": "vivek",
    "password": "vivek",
    "database": "mainhostel"
}

# ----------------- DB UTIL -----------------
def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as e:
        messagebox.showerror("Database Error", f"Could not connect: {e}")
        return None

def call_proc(proc_name, params=()):
    conn = get_connection()
    if not conn:
        return None, None
    cur = conn.cursor()
    try:
        cur.callproc(proc_name, params)
        results = []
        columns = None
        for res in cur.stored_results():
            rows = res.fetchall()
            results.append(rows)
            if columns is None:
                columns = [col[0] for col in res.description] if res.description else None
        conn.commit()
        return results, columns
    except mysql.connector.Error as e:
        messagebox.showerror("Execution Error", str(e))
        return None, None
    finally:
        cur.close()
        conn.close()

# ----------------- Helper UI -----------------
def center_window(win, width=600, height=400):
    win.update_idletasks()
    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()
    x = (screen_w // 2) - (width // 2)
    y = (screen_h // 2) - (height // 2) - 30
    win.geometry(f"{width}x{height}+{x}+{y}")

# ----------------- Result Table Window -----------------
def show_results_window(title, resultsets, columns=None):
    w = tk.Toplevel()
    w.title(title)
    center_window(w, width=700, height=400)
    if not resultsets or len(resultsets) == 0 or (len(resultsets) == 1 and len(resultsets[0]) == 0):
        ttk.Label(w, text="No records found.", font=("Segoe UI", 11)).pack(pady=20)
        return

    rows = resultsets[0]
    if not columns:
        columns = [f"col{i+1}" for i in range(len(rows[0]))]

    tree = ttk.Treeview(w, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=max(80, 120//len(columns)))

    for row in rows:
        tree.insert("", "end", values=row)

    vsb = ttk.Scrollbar(w, orient="vertical", command=tree.yview)
    tree.configure(yscroll=vsb.set)
    tree.pack(side="left", fill="both", expand=True, padx=(10,0), pady=10)
    vsb.pack(side="left", fill="y", pady=10)

# ----------------- Forms -----------------
def add_student_window():
    w = tk.Toplevel()
    w.title("Add Student")
    center_window(w, width=450, height=380)
    frm = ttk.Frame(w, padding=16)
    frm.pack(fill="both", expand=True)

    labels = ["Student ID (int)", "Admission Date (YYYY-MM-DD)", "Email", "Contact Number (10 digits)", "Warden ID (int)"]
    entries = {}

    for i, lbl in enumerate(labels):
        ttk.Label(frm, text=lbl).grid(row=i, column=0, sticky="w", pady=6)
        ent = ttk.Entry(frm, width=30)
        ent.grid(row=i, column=1, pady=6, padx=8)
        entries[i] = ent

    def submit():
        try:
            sid = int(entries[0].get().strip())
            adate = entries[1].get().strip()
            datetime.strptime(adate, "%Y-%m-%d")
            email = entries[2].get().strip()
            phone = entries[3].get().strip()
            if not re.fullmatch(r"\d{10}", phone):
                raise ValueError("Phone must be 10 digits.")
            wid = int(entries[4].get().strip())
        except ValueError as ve:
            messagebox.showerror("Input Error", f"{ve}")
            return

        results, cols = call_proc("AddStudent", (sid, adate, email, phone, wid))
        if results is not None:
            messagebox.showinfo("Success", "Student added successfully (stored procedure ran).")
            w.destroy()

    ttk.Button(frm, text="Add Student", command=submit).grid(row=len(labels), column=0, columnspan=2, pady=12)

def get_students_by_warden_window():
    w = tk.Toplevel()
    w.title("Get Students by Warden")
    center_window(w, width=480, height=160)
    frm = ttk.Frame(w, padding=18)
    frm.pack(fill="both", expand=True)

    ttk.Label(frm, text="Warden ID:").grid(row=0, column=0, sticky="w")
    wid_entry = ttk.Entry(frm, width=20)
    wid_entry.grid(row=0, column=1, padx=8)

    def submit():
        try:
            wid = int(wid_entry.get().strip())
        except ValueError:
            messagebox.showerror("Input Error", "Warden ID must be an integer.")
            return
        results, cols = call_proc("GetStudentsByWarden", (wid,))
        if results is not None:
            show_results_window(f"Students under Warden {wid}", results, cols)
            # ❌ Removed w.destroy() here

    ttk.Button(frm, text="Show Students", command=submit).grid(row=1, column=0, columnspan=2, pady=12)

def add_complaint_window():
    w = tk.Toplevel()
    w.title("Add Complaint")
    center_window(w, width=520, height=360)
    frm = ttk.Frame(w, padding=16)
    frm.pack(fill="both", expand=True)

    ttk.Label(frm, text="Student ID (int)").grid(row=0, column=0, sticky="w")
    sid_e = ttk.Entry(frm, width=25); sid_e.grid(row=0, column=1, pady=6)

    ttk.Label(frm, text="Complaint Date (YYYY-MM-DD)").grid(row=1, column=0, sticky="w")
    cdate_e = ttk.Entry(frm, width=25); cdate_e.grid(row=1, column=1, pady=6)

    ttk.Label(frm, text="Description").grid(row=2, column=0, sticky="nw")
    desc_t = tk.Text(frm, width=36, height=6); desc_t.grid(row=2, column=1, pady=6)

    ttk.Label(frm, text="Warden ID (int)").grid(row=3, column=0, sticky="w")
    wid_e = ttk.Entry(frm, width=25); wid_e.grid(row=3, column=1, pady=6)

    def submit():
        try:
            sid = int(sid_e.get().strip())
            cdate = cdate_e.get().strip()
            datetime.strptime(cdate, "%Y-%m-%d")
            descp = desc_t.get("1.0", "end").strip()
            if not descp:
                raise ValueError("Description cannot be empty.")
            wid = int(wid_e.get().strip())
        except ValueError as ve:
            messagebox.showerror("Input Error", f"{ve}")
            return

        results, cols = call_proc("AddComplaint", (sid, cdate, descp, wid))
        if results is not None:
            messagebox.showinfo("Success", "Complaint recorded successfully.")
            w.destroy()

    ttk.Button(frm, text="Record Complaint", command=submit).grid(row=4, column=0, columnspan=2, pady=10)

def add_billing_window():
    w = tk.Toplevel()
    w.title("Add Billing")
    center_window(w, width=480, height=320)
    frm = ttk.Frame(w, padding=16)
    frm.pack(fill="both", expand=True)

    ttk.Label(frm, text="Student ID (int)").grid(row=0, column=0, sticky="w")
    sid_e = ttk.Entry(frm, width=25); sid_e.grid(row=0, column=1, pady=6)

    ttk.Label(frm, text="Receipt Code").grid(row=1, column=0, sticky="w")
    rcpt_e = ttk.Entry(frm, width=25); rcpt_e.grid(row=1, column=1, pady=6)

    ttk.Label(frm, text="Tracking Code").grid(row=2, column=0, sticky="w")
    trk_e = ttk.Entry(frm, width=25); trk_e.grid(row=2, column=1, pady=6)

    ttk.Label(frm, text="Warden ID (int)").grid(row=3, column=0, sticky="w")
    wid_e = ttk.Entry(frm, width=25); wid_e.grid(row=3, column=1, pady=6)

    def submit():
        try:
            sid = int(sid_e.get().strip())
            rcpt = rcpt_e.get().strip()
            trk = trk_e.get().strip()
            wid = int(wid_e.get().strip())
            if not rcpt or not trk:
                raise ValueError("Receipt and Tracking cannot be empty.")
        except ValueError as ve:
            messagebox.showerror("Input Error", f"{ve}")
            return

        results, cols = call_proc("AddBilling", (sid, rcpt, trk, wid))
        if results is not None:
            messagebox.showinfo("Success", "Billing added successfully.")
            w.destroy()

    ttk.Button(frm, text="Add Billing", command=submit).grid(row=4, column=0, columnspan=2, pady=10)

def view_complaints_by_warden_window():
    w = tk.Toplevel()
    w.title("View Complaints by Warden")
    center_window(w, width=480, height=160)
    frm = ttk.Frame(w, padding=18)
    frm.pack(fill="both", expand=True)

    ttk.Label(frm, text="Warden ID:").grid(row=0, column=0, sticky="w")
    wid_entry = ttk.Entry(frm, width=20)
    wid_entry.grid(row=0, column=1, padx=8)

    def submit():
        try:
            wid = int(wid_entry.get().strip())
        except ValueError:
            messagebox.showerror("Input Error", "Warden ID must be an integer.")
            return
        results, cols = call_proc("ViewComplaintsByWarden", (wid,))
        if results is not None:
            show_results_window(f"Complaints handled by {wid}", results, cols)
            # ❌ Removed w.destroy() here

    ttk.Button(frm, text="Show Complaints", command=submit).grid(row=1, column=0, columnspan=2, pady=12)

# ----------------- Dashboard -----------------
def open_dashboard():
    dash = tk.Tk()
    dash.title("Hostel Management - Dashboard")
    center_window(dash, width=640, height=460)
    dash.configure(bg="#f6f8fb")

    header = ttk.Frame(dash, padding=(20,14))
    header.pack(fill="x")
    ttk.Label(header, text="Hostel Management", font=("Segoe UI", 18, "bold")).pack(anchor="w")
    ttk.Label(header, text="Choose an action below", font=("Segoe UI", 11)).pack(anchor="w")

    btn_frame = ttk.Frame(dash, padding=20)
    btn_frame.pack(fill="both", expand=True)

    style = ttk.Style()
    style.configure("Big.TButton", font=("Segoe UI", 11), padding=10)

    ttk.Button(btn_frame, text="➕ Add Student", style="Big.TButton", command=add_student_window).grid(row=0, column=0, padx=12, pady=12, sticky="ew")
    ttk.Button(btn_frame, text="👁 View Students by Warden", style="Big.TButton", command=get_students_by_warden_window).grid(row=0, column=1, padx=12, pady=12, sticky="ew")
    ttk.Button(btn_frame, text="📝 Add Complaint", style="Big.TButton", command=add_complaint_window).grid(row=1, column=0, padx=12, pady=12, sticky="ew")
    ttk.Button(btn_frame, text="💳 Add Billing", style="Big.TButton", command=add_billing_window).grid(row=1, column=1, padx=12, pady=12, sticky="ew")
    ttk.Button(btn_frame, text="📢 View Complaints by Warden", style="Big.TButton", command=view_complaints_by_warden_window).grid(row=2, column=0, columnspan=2, padx=12, pady=12, sticky="ew")

    btn_frame.columnconfigure(0, weight=1)
    btn_frame.columnconfigure(1, weight=1)

    dash.mainloop()

# ----------------- Login -----------------
def launch_login():
    root = tk.Tk()
    root.title("Login - Hostel Management System")
    center_window(root, width=520, height=360)
    root.configure(bg="#e9eef6")

    card = tk.Frame(root, bg="white", bd=0, relief="ridge")
    card.place(relx=0.5, rely=0.5, anchor="center", width=420, height=280)

    left = tk.Frame(card, bg="#2b8fe6", width=120)
    left.pack(side="left", fill="y")
    ttk.Label(left, text="Hostel\nSystem", foreground="white", background="#2b8fe6", font=("Segoe UI", 14, "bold")).place(relx=0.5, rely=0.5, anchor="center")

    form = tk.Frame(card, bg="white", padx=14, pady=12)
    form.pack(side="right", fill="both", expand=True)

    ttk.Label(form, text="Welcome Back", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(4,8))
    ttk.Label(form, text="Sign in to continue", font=("Segoe UI", 9)).pack(anchor="w")

    ttk.Label(form, text="Username").pack(anchor="w", pady=(12,2))
    username = ttk.Entry(form, width=28)
    username.pack(anchor="w")

    ttk.Label(form, text="Password").pack(anchor="w", pady=(8,2))
    password = ttk.Entry(form, width=28, show="*")
    password.pack(anchor="w")

    def attempt_login():
        u = username.get().strip()
        p = password.get().strip()
        if u == "abc" and p == "abc":
            root.destroy()
            open_dashboard()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")

    btn = ttk.Button(form, text="Login", command=attempt_login)
    btn.pack(pady=(16,6), anchor="center")

    root.mainloop()

if __name__ == "__main__":
    launch_login()
