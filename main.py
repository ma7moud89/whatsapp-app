import flet as ft
import sqlite3
import datetime
import os
import pandas as pd
import shutil

DB_NAME = "app_data.dat"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS customers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        name TEXT, phone TEXT, service TEXT,
                        start_date TEXT, end_date TEXT, 
                        paid TEXT, remaining TEXT, 
                        support TEXT, cust_code TEXT, act_code TEXT
                    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS services (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        name TEXT UNIQUE
                    )''')
    
    cursor.execute("SELECT COUNT(*) FROM services")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO services (name) VALUES ('WA Sender'), ('Business Bot')")
        
    conn.commit()
    conn.close()

def main(page: ft.Page):
    page.title = "إدارة تفعيلات الواتساب"
    page.window.width = 400  
    page.window.height = 700
    page.theme_mode = ft.ThemeMode.LIGHT
    page.rtl = True 
    
    init_db()

    def show_snack(message, color_hex):
        page.overlay.append(ft.SnackBar(ft.Text(message, color="#FFFFFF"), bgcolor=color_hex, open=True))
        page.update()

    def get_status(end_date_str):
        if not end_date_str: return "غير محدد", "#9E9E9E" 
        try:
            end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
            today = datetime.date.today()
            days = (end_date - today).days
            if days < 0: return "منتهي", "#F44336" 
            if days <= 7: return f"ينتهي بعد {days} يوم", "#FF9800" 
            return "نشط", "#4CAF50" 
        except:
            return "خطأ بالتاريخ", "#9E9E9E" 

    def backup_database(e):
        try:
            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            if not os.path.exists(downloads_dir):
                downloads_dir = os.getcwd() 
                
            file_name = f"Backup_Data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.dat"
            file_path = os.path.join(downloads_dir, file_name)
            
            shutil.copy2(DB_NAME, file_path)
            show_snack(f"تم حفظ النسخة بنجاح في التنزيلات", "#4CAF50")
        except Exception as ex:
            show_snack(f"حدث خطأ أثناء النسخ: {str(ex)}", "#F44336")

    def restore_latest_backup(e):
        try:
            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            if not os.path.exists(downloads_dir):
                downloads_dir = os.getcwd()

            backup_files = []
            for f in os.listdir(downloads_dir):
                if f.startswith("Backup_Data_") and f.endswith(".dat"):
                    backup_files.append(os.path.join(downloads_dir, f))

            if not backup_files:
                show_snack("لم يتم العثور على أي نسخة احتياطية في التنزيلات!", "#F44336")
                return

            latest_backup = max(backup_files, key=os.path.getmtime)
            
            shutil.copy2(latest_backup, DB_NAME)
            load_services()
            load_customers()
            show_snack("تمت استعادة أحدث نسخة احتياطية بنجاح!", "#4CAF50")
        except Exception as ex:
            show_snack(f"حدث خطأ أثناء الاستعادة: {str(ex)}", "#F44336")

    page.appbar = ft.AppBar(
        title=ft.Text("إدارة التفعيلات", color="#FFFFFF", weight="bold", size=18),
        bgcolor="#2196F3",
        actions=[
            ft.PopupMenuButton(
                icon=ft.Icons.SETTINGS,
                icon_color="#FFFFFF",
                items=[
                    ft.PopupMenuItem(
                        content=ft.Row([ft.Icon(ft.Icons.BACKUP), ft.Text("نسخ احتياطي")]), 
                        on_click=backup_database
                    ),
                    ft.PopupMenuItem(
                        content=ft.Row([ft.Icon(ft.Icons.RESTORE), ft.Text("استعادة أحدث نسخة")]), 
                        on_click=restore_latest_backup
                    ),
                ]
            )
        ]
    )

    # ------------------ ميزة التقويم (تم حل المشكلة للأندرويد) ------------------
    def on_start_date_change(e):
        if e.control.value:
            txt_start_date.value = e.control.value.strftime("%Y-%m-%d")
            page.update()

    def on_end_date_change(e):
        if e.control.value:
            txt_end_date.value = e.control.value.strftime("%Y-%m-%d")
            page.update()

    start_date_picker = ft.DatePicker(
        on_change=on_start_date_change,
        first_date=datetime.datetime(2020, 1, 1),
        last_date=datetime.datetime(2040, 12, 31)
    )
    end_date_picker = ft.DatePicker(
        on_change=on_end_date_change,
        first_date=datetime.datetime(2020, 1, 1),
        last_date=datetime.datetime(2040, 12, 31)
    )

    # ------------------ دوال إضافة الخدمة ------------------
    txt_new_service = ft.TextField(label="اسم الخدمة الجديدة", width=300)
    
    def load_services():
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM services")
        services = [row[0] for row in cursor.fetchall()]
        conn.close()
        dd_service.options = [ft.dropdown.Option(s) for s in services]
        page.update()

    def save_new_service(e):
        new_service = txt_new_service.value.strip()
        if new_service:
            try:
                conn = sqlite3.connect(DB_NAME)
                conn.execute("INSERT INTO services (name) VALUES (?)", (new_service,))
                conn.commit()
                conn.close()
                show_snack("تمت إضافة الخدمة بنجاح!", "#4CAF50") 
                txt_new_service.value = ""
                dlg_add_service.open = False
                load_services() 
            except sqlite3.IntegrityError:
                show_snack("الخدمة موجودة مسبقاً!", "#F44336") 
        else:
            show_snack("اكتب اسم الخدمة", "#F44336")

    dlg_add_service = ft.AlertDialog(
        title=ft.Text("إضافة خدمة جديدة"),
        content=txt_new_service,
        actions=[
            ft.TextButton("حفظ", on_click=save_new_service),
            ft.TextButton("إلغاء", on_click=lambda e: setattr(dlg_add_service, 'open', False) or page.update())
        ],
    )
    
    def open_service_dialog(e):
        page.open(dlg_add_service)

    # ------------------ صفحة إضافة العميل ------------------
    txt_name = ft.TextField(label="اسم العميل *", width=350)
    txt_phone = ft.TextField(label="رقم الواتساب *", width=350, keyboard_type=ft.KeyboardType.PHONE)
    
    dd_service = ft.Dropdown(label="البرنامج", width=290)
    btn_add_service = ft.IconButton(icon=ft.Icons.ADD_CIRCLE, icon_color="#2196F3", icon_size=35, on_click=open_service_dialog)
    row_service = ft.Row([dd_service, btn_add_service], alignment=ft.MainAxisAlignment.CENTER)
    
    # 🌟 التحديث هنا: استخدام page.open لفتح التقويم بدلاً من pick_date 🌟
    txt_start_date = ft.TextField(label="تاريخ البدء (YYYY-MM-DD)", width=290, value=str(datetime.date.today()))
    btn_start_date = ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, icon_color="#2196F3", on_click=lambda e: page.open(start_date_picker))
    row_start_date = ft.Row([txt_start_date, btn_start_date], alignment=ft.MainAxisAlignment.CENTER)
    
    txt_end_date = ft.TextField(label="تاريخ الانتهاء (YYYY-MM-DD)", width=290)
    btn_end_date = ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, icon_color="#2196F3", on_click=lambda e: page.open(end_date_picker))
    row_end_date = ft.Row([txt_end_date, btn_end_date], alignment=ft.MainAxisAlignment.CENTER)
    
    txt_paid = ft.TextField(label="المدفوع", width=170, keyboard_type=ft.KeyboardType.NUMBER)
    txt_remaining = ft.TextField(label="المتبقي", width=170, keyboard_type=ft.KeyboardType.NUMBER)
    row_money = ft.Row([txt_paid, txt_remaining], alignment=ft.MainAxisAlignment.CENTER)
    
    txt_support = ft.TextField(label="مدة الدعم", width=350)
    txt_cust_code = ft.TextField(label="كود العميل", width=350)
    txt_act_code = ft.TextField(label="كود التفعيل", width=350)

    def save_customer(e):
        if not txt_name.value or not txt_phone.value:
            show_snack("الاسم ورقم الواتساب حقول إجبارية!", "#F44336")
            return

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO customers 
                          (name, phone, service, start_date, end_date, paid, remaining, support, cust_code, act_code) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                       (txt_name.value, txt_phone.value, dd_service.value, txt_start_date.value, 
                        txt_end_date.value, txt_paid.value, txt_remaining.value, 
                        txt_support.value, txt_cust_code.value, txt_act_code.value))
        conn.commit()
        conn.close()

        for txt in [txt_name, txt_phone, txt_end_date, txt_paid, txt_remaining, txt_support, txt_cust_code, txt_act_code]:
            txt.value = ""
        
        show_snack("تم حفظ العميل بنجاح!", "#4CAF50")
        load_customers()

    btn_save = ft.Button("حفظ بيانات العميل", icon=ft.Icons.SAVE, on_click=save_customer, width=350, style=ft.ButtonStyle(bgcolor="#2196F3", color="#FFFFFF"))

    add_container = ft.Column(
        [txt_name, txt_phone, row_service, row_start_date, row_end_date, row_money, txt_support, txt_cust_code, txt_act_code, btn_save],
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10,
        expand=True,
        visible=True
    )

    # ------------------ صفحة قائمة العملاء والبحث ------------------
    txt_search = ft.TextField(label="بحث (بالاسم أو الواتساب)...", width=350, prefix_icon=ft.Icons.SEARCH)
    customers_list = ft.ListView(expand=True, spacing=10)

    def confirm_delete_action(e):
        cust_id = dlg_confirm_delete.data
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM customers WHERE id=?", (cust_id,))
        conn.commit()
        conn.close()
        page.close(dlg_confirm_delete)
        show_snack("تم حذف العميل بنجاح!", "#F44336")
        load_customers()

    dlg_confirm_delete = ft.AlertDialog(
        title=ft.Text("تأكيد الحذف", weight="bold"),
        content=ft.Text("هل أنت متأكد من حذف بيانات هذا العميل نهائياً؟"),
        actions=[
            ft.TextButton("نعم، احذف", on_click=confirm_delete_action, style=ft.ButtonStyle(color="#F44336")),
            ft.TextButton("إلغاء", on_click=lambda e: page.close(dlg_confirm_delete))
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def prompt_delete(e, cust_id):
        dlg_confirm_delete.data = cust_id
        page.open(dlg_confirm_delete)

    # 🌟 التحديث هنا: الرابط المباشر الذي يتخطى أذونات الأندرويد 🌟
    def open_whatsapp(e, phone_num):
        clean_phone = ''.join(filter(str.isdigit, str(phone_num)))
        page.launch_url(f"https://api.whatsapp.com/send?phone={clean_phone}")

    def load_customers(e=None):
        customers_list.controls.clear()
        search_query = txt_search.value.lower() if txt_search.value else ""
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, phone, service, end_date, act_code FROM customers ORDER BY id DESC")
        
        for row in cursor.fetchall():
            c_id, name, phone, service, end_date, act_code = row
            
            if search_query and search_query not in name.lower() and search_query not in phone:
                continue
                
            status_text, status_color = get_status(end_date)
            
            customers_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.PERSON, color="#2196F3"),
                                ft.Text(name, weight="bold", size=16, expand=True),
                                ft.Text(status_text, color=status_color, weight="bold")
                            ]),
                            ft.Text(f"الخدمة: {service} | كود: {act_code}"),
                            ft.Row([
                                ft.Button("واتساب", icon=ft.Icons.CHAT, on_click=lambda e, p=phone: open_whatsapp(e, p), style=ft.ButtonStyle(bgcolor="#4CAF50", color="#FFFFFF")),
                                ft.IconButton(icon=ft.Icons.DELETE, icon_color="#F44336", on_click=lambda e, cid=c_id: prompt_delete(e, cid))
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                        ])
                    )
                )
            )
        conn.close()
        page.update()

    txt_search.on_change = load_customers

    # ------------------ نظام التصدير التلقائي للإكسل ------------------
    def export_excel(e):
        try:
            conn = sqlite3.connect(DB_NAME)
            query = """SELECT 
                        id AS 'م', name AS 'الاسم', phone AS 'الواتساب', service AS 'الخدمة', 
                        start_date AS 'البداية', end_date AS 'النهاية', paid AS 'المدفوع', 
                        remaining AS 'المتبقي', support AS 'الدعم', cust_code AS 'كود العميل', 
                        act_code AS 'كود التفعيل' 
                       FROM customers"""
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            if not os.path.exists(downloads_dir):
                downloads_dir = os.getcwd() 
                
            file_name = f"Customers_List_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            file_path = os.path.join(downloads_dir, file_name)
            
            df.to_excel(file_path, index=False, engine='openpyxl')
            show_snack(f"تم الحفظ بنجاح في التنزيلات", "#4CAF50")
            
        except Exception as ex:
            show_snack(f"حدث خطأ أثناء التصدير: {str(ex)}", "#F44336")

    btn_export = ft.Button("تصدير إكسل", icon=ft.Icons.DOWNLOAD, on_click=export_excel, width=350, style=ft.ButtonStyle(bgcolor="#FF9800", color="#FFFFFF"))

    list_container = ft.Column(
        [
            ft.Row([txt_search], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([btn_export], alignment=ft.MainAxisAlignment.CENTER),
            customers_list
        ],
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        visible=False
    )

    # ------------------ شريط الأزرار العلوي (التنقل) ------------------
    def tab_changed(e, index):
        if index == 0:
            add_container.visible = True
            list_container.visible = False
            btn_tab_add.border = ft.border.Border(bottom=ft.border.BorderSide(3, "#2196F3"))
            btn_tab_add.content.controls[0].color = "#2196F3"
            btn_tab_add.content.controls[1].color = "#2196F3"
            
            btn_tab_list.border = ft.border.Border(bottom=ft.border.BorderSide(3, "transparent"))
            btn_tab_list.content.controls[0].color = "#9E9E9E"
            btn_tab_list.content.controls[1].color = "#9E9E9E"
        else:
            add_container.visible = False
            list_container.visible = True
            btn_tab_list.border = ft.border.Border(bottom=ft.border.BorderSide(3, "#2196F3"))
            btn_tab_list.content.controls[0].color = "#2196F3"
            btn_tab_list.content.controls[1].color = "#2196F3"
            
            btn_tab_add.border = ft.border.Border(bottom=ft.border.BorderSide(3, "transparent"))
            btn_tab_add.content.controls[0].color = "#9E9E9E"
            btn_tab_add.content.controls[1].color = "#9E9E9E"
        page.update()

    btn_tab_add = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.PERSON_ADD, color="#2196F3"), ft.Text("إضافة عميل", color="#2196F3", weight="bold")], alignment=ft.MainAxisAlignment.CENTER),
        padding=10,
        on_click=lambda e: tab_changed(e, 0),
        border=ft.border.Border(bottom=ft.border.BorderSide(3, "#2196F3")),
        expand=True
    )
    
    btn_tab_list = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.LIST, color="#9E9E9E"), ft.Text("العملاء والبحث", color="#9E9E9E", weight="bold")], alignment=ft.MainAxisAlignment.CENTER),
        padding=10,
        on_click=lambda e: tab_changed(e, 1),
        border=ft.border.Border(bottom=ft.border.BorderSide(3, "transparent")),
        expand=True
    )
    
    top_nav = ft.Row([btn_tab_add, btn_tab_list])

    load_services()
    load_customers()
    page.add(top_nav, add_container, list_container)

ft.run(main)
