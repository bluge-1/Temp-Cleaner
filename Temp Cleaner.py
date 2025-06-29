import os
import tempfile
import threading
import tkinter as tk
from tkinter import messagebox, ttk, filedialog

# --- Ayarlar ---
ayarlar = {
    "sil_temp": True,
    "sil_windows_temp": True,
    "ek_klasorler": [],
    "extensions": [],  # Uzantı filtresi boş, tüm dosyalar temizlenecek
    "dark_mode": False,
    "language": "tr",
    "cancel_requested": False
}

# --- Dil Desteği ---
diller = {
    "tr": {
        "menu_file": "Dosya",
        "menu_settings": "Ayarlar",
        "menu_exit": "Çıkış",
        "menu_help": "Yardım",
        "menu_about": "Hakkında",
        "start_clean": "💥 Temizliği Başlat",
        "cancel": "İptal",
        "disk_before": "Temizlik Öncesi Boş Alan: ",
        "disk_after": "Temizlik Sonrası Boş Alan: ",
        "confirm_exit": "Çıkmak istediğinizden emin misiniz?",
        "about_title": "Hakkında",
        "about_text": "Temp Cleaner Uygulaması\nSürüm: 1.0\nGeliştirici: bluge\n\n- Geçici dosyaları temizler.",
        "settings_title": "Ayarlar",
        "settings_temp": "Kullanıcı TEMP klasörünü temizle",
        "settings_win_temp": "Windows TEMP klasörünü temizle",
        "settings_add_folder": "Ek Klasör Ekle",
        "settings_remove_folder": "Seçili Klasörü Kaldır",
        "settings_extensions": "Filtre (Uzantılar - Virgül ile ayırın, boş ise tümü temizlenir)",
        "settings_language": "Dil Seçimi",
        "settings_dark_mode": "Dark Mode",
        "settings_save": "Kaydet",
        "filter_label": "Filtreler",
        "appearance_label": "Görünüm",
        "folders_label": "Klasörler",
        "error": "Hata",
    },
    "en": {
        "menu_file": "File",
        "menu_settings": "Settings",
        "menu_exit": "Exit",
        "menu_help": "Help",
        "menu_about": "About",
        "start_clean": "💥 Start Cleaning",
        "cancel": "Cancel",
        "disk_before": "Free Space Before Cleaning: ",
        "disk_after": "Free Space After Cleaning: ",
        "confirm_exit": "Are you sure you want to exit?",
        "about_title": "About",
        "about_text": "Temp Cleaner Application\nVersion: 1.0\nDeveloper: bluge\n\n- Cleans temp files\n- Removes empty folders\n",
        "settings_title": "Settings",
        "settings_temp": "Clean User TEMP Folder",
        "settings_win_temp": "Clean Windows TEMP Folder",
        "settings_add_folder": "Add Extra Folder",
        "settings_remove_folder": "Remove Selected Folder",
        "settings_extensions": "Filter (Extensions - comma separated, empty means all)",
        "settings_language": "Language",
        "settings_dark_mode": "Dark Mode",
        "settings_save": "Save",
        "filter_label": "Filters",
        "appearance_label": "Appearance",
        "folders_label": "Folders",
        "error": "Error",
    }
}

def T(key):
    return diller[ayarlar["language"]].get(key, key)

# --- Tema Uygulaması ---
def apply_theme(pencere):
    if ayarlar["dark_mode"]:
        bg_color = "#2e2e2e"
        fg_color = "#ffffff"
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background=bg_color, foreground=fg_color)
        style.configure('TButton', background="#444444", foreground=fg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color)
        style.configure('TCheckbutton', background=bg_color, foreground=fg_color)
        pencere.configure(bg=bg_color)
    else:
        style = ttk.Style()
        style.theme_use('default')
        pencere.configure(bg=None)

# --- Disk Alanı Bilgisi ---
def disk_bos_alan_yaz(disk_label):
    try:
        total, used, free = shutil.disk_usage(os.getenv("SystemDrive", "C:") + "\\")
        disk_label.config(text=f"{T('disk_before') if 'öncesi' in disk_label.cget('text') else T('disk_after')}{boyut_formatla(free)}")
    except:
        disk_label.config(text="")

# --- Boyut Formatlama ---
def boyut_formatla(boyut):
    for birim in ['B','KB','MB','GB']:
        if boyut < 1024:
            return f"{boyut:.2f} {birim}"
        boyut /= 1024
    return f"{boyut:.2f} TB"

# --- Dosya Silinebilir Mi? ---
def dosya_silinmeli(dosya_yolu):
    if "Roblox" in dosya_yolu:
        return False
    if ayarlar["extensions"]:
        return any(dosya_yolu.lower().endswith(ext.strip().lower()) for ext in ayarlar["extensions"])
    return True

# --- Klasörü Temizle ---
def temizle_klasor(klasor_yolu, progress_callback=None):
    toplam_eleman = 0
    for root, dirs, files in os.walk(klasor_yolu):
        toplam_eleman += len(files) + len(dirs)

    islem_sayaci = 0
    silinen_dosyalar = []

    for root, dirs, files in os.walk(klasor_yolu, topdown=False):
        if ayarlar["cancel_requested"]:
            break
        for dosya in files:
            dosya_yolu = os.path.join(root, dosya)
            if dosya_silinmeli(dosya_yolu):
                try:
                    os.remove(dosya_yolu)
                    silinen_dosyalar.append(dosya_yolu)
                except:
                    pass
            islem_sayaci += 1
            if progress_callback:
                progress_callback(islem_sayaci, toplam_eleman)
        for klasor in dirs:
            klasor_yolu = os.path.join(root, klasor)
            try:
                os.rmdir(klasor_yolu)
            except:
                pass
            islem_sayaci += 1
            if progress_callback:
                progress_callback(islem_sayaci, toplam_eleman)
    return silinen_dosyalar

# --- Temizliği Başlat ---
def temizligi_baslat(progress_var, progressbar, log_text, disk_before_label, disk_after_label, btn_start, btn_cancel):
    ayarlar["cancel_requested"] = False
    btn_start.config(state="disabled")
    btn_cancel.config(state="normal")

    disk_bos_alan_yaz(disk_before_label)

    toplam_silinen_listesi = []

    def progress_callback(islem, toplam):
        if toplam > 0:
            progress_var.set(islem / toplam * 100)
        else:
            progress_var.set(100)
        progressbar.update()

    klasorler = []
    if ayarlar["sil_temp"]:
        klasorler.append(tempfile.gettempdir())
    if ayarlar["sil_windows_temp"]:
        klasorler.append(r"C:\Windows\Temp")
    klasorler.extend(ayarlar["ek_klasorler"])

    for klasor in klasorler:
        if ayarlar["cancel_requested"]:
            break
        if os.path.exists(klasor):
            silinen_list = temizle_klasor(klasor, progress_callback)
            toplam_silinen_listesi.extend(silinen_list)

    log_metni = f"Toplam Silinen Dosya: {len(toplam_silinen_listesi)}\n\n"
    log_metni += "Silinen Dosyalar:\n"
    for dosya in toplam_silinen_listesi:
        log_metni += dosya + "\n"

    log_text.config(state="normal")
    log_text.delete(1.0, tk.END)
    log_text.insert(tk.END, log_metni)
    log_text.config(state="disabled")

    disk_bos_alan_yaz(disk_after_label)

    progress_var.set(0)
    btn_start.config(state="normal")
    btn_cancel.config(state="disabled")

    if ayarlar["cancel_requested"]:
        messagebox.showinfo("", "Temizlik iptal edildi.")
    else:
        messagebox.showinfo("", "Temizlik işlemi tamamlandı!")

# --- Temizliği Başlat Thread ---
def baslat_thread(progress_var, progressbar, log_text, disk_before_label, disk_after_label, btn_start, btn_cancel):
    threading.Thread(target=temizligi_baslat, args=(progress_var, progressbar, log_text, disk_before_label, disk_after_label, btn_start, btn_cancel), daemon=True).start()

# --- İptal Et ---
def iptal_et(btn_start, btn_cancel):
    ayarlar["cancel_requested"] = True
    btn_cancel.config(state="disabled")

# --- Ayarlar Penceresi ---
def ayarlar_penceresi(parent):
    win = tk.Toplevel(parent)
    win.title(T("settings_title"))
    win.geometry("500x400")

    apply_theme(win)

    notebook = ttk.Notebook(win)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    # Filtreler Sekmesi
    frame_filtre = ttk.Frame(notebook)
    notebook.add(frame_filtre, text=T("filter_label"))

    # Uzantı filtresi
    ttk.Label(frame_filtre, text=T("settings_extensions")).pack(anchor="w", pady=(10,0))
    ext_var = tk.StringVar(value=",".join(ayarlar["extensions"]))
    ext_entry = ttk.Entry(frame_filtre, textvariable=ext_var)
    ext_entry.pack(fill="x", padx=10, pady=5)

    # Görünüm Sekmesi
    frame_gorunum = ttk.Frame(notebook)
    notebook.add(frame_gorunum, text=T("appearance_label"))

    dark_var = tk.BooleanVar(value=ayarlar["dark_mode"])
    ttk.Checkbutton(frame_gorunum, text=T("settings_dark_mode"), variable=dark_var).pack(anchor="w", padx=20, pady=15)

    # Klasörler Sekmesi
    frame_klasor = ttk.Frame(notebook)
    notebook.add(frame_klasor, text=T("folders_label"))

    sil_temp_var = tk.BooleanVar(value=ayarlar["sil_temp"])
    ttk.Checkbutton(frame_klasor, text=T("settings_temp"), variable=sil_temp_var).pack(anchor="w", padx=20, pady=5)

    sil_win_temp_var = tk.BooleanVar(value=ayarlar["sil_windows_temp"])
    ttk.Checkbutton(frame_klasor, text=T("settings_win_temp"), variable=sil_win_temp_var).pack(anchor="w", padx=20, pady=5)

    ttk.Label(frame_klasor, text="").pack()  # Boşluk

    ttk.Label(frame_klasor, text="Ek Klasörler:").pack(anchor="w", padx=20)

    ek_klasor_listbox = tk.Listbox(frame_klasor, height=5)
    ek_klasor_listbox.pack(fill="x", padx=20, pady=5)
    for k in ayarlar["ek_klasorler"]:
        ek_klasor_listbox.insert(tk.END, k)

    def ekle_klasor():
        klasor = filedialog.askdirectory()
        if klasor and klasor not in ayarlar["ek_klasorler"]:
            ayarlar["ek_klasorler"].append(klasor)
            ek_klasor_listbox.insert(tk.END, klasor)

    def sil_klasor():
        sec = ek_klasor_listbox.curselection()
        if sec:
            idx = sec[0]
            ayarlar["ek_klasorler"].pop(idx)
            ek_klasor_listbox.delete(idx)

    ttk.Button(frame_klasor, text=T("settings_add_folder"), command=ekle_klasor).pack(pady=2, padx=20, anchor="w")
    ttk.Button(frame_klasor, text=T("settings_remove_folder"), command=sil_klasor).pack(pady=2, padx=20, anchor="w")

    # Dil Seçimi
    ttk.Label(frame_gorunum, text=T("settings_language")).pack(anchor="w", padx=20)
    lang_var = tk.StringVar(value=ayarlar["language"])
    ttk.Radiobutton(frame_gorunum, text="Türkçe", variable=lang_var, value="tr").pack(anchor="w", padx=40)
    ttk.Radiobutton(frame_gorunum, text="English", variable=lang_var, value="en").pack(anchor="w", padx=40)

    def kaydet():
        ayarlar["sil_temp"] = sil_temp_var.get()
        ayarlar["sil_windows_temp"] = sil_win_temp_var.get()
        ayarlar["extensions"] = [e.strip() for e in ext_var.get().split(",") if e.strip()]
        ayarlar["dark_mode"] = dark_var.get()
        ayarlar["language"] = lang_var.get()

        win.destroy()
        apply_theme(parent)
        refresh_gui(parent)

    ttk.Button(win, text=T("settings_save"), command=kaydet).pack(pady=10)

# --- GUI Yenile ---
def refresh_gui(pencere):
    for widget in pencere.winfo_children():
        widget.destroy()
    ana_pencere_olustur(pencere)

# --- Ana Pencere ---
def ana_pencere_olustur(pencere):
    pencere.title("Temp Cleaner")
    pencere.geometry("700x500")
    apply_theme(pencere)

    menubar = tk.Menu(pencere)
    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label=T("menu_settings"), command=lambda: ayarlar_penceresi(pencere))
    file_menu.add_separator()
    file_menu.add_command(label=T("menu_exit"), command=lambda: cikis(pencere))
    menubar.add_cascade(label=T("menu_file"), menu=file_menu)

    help_menu = tk.Menu(menubar, tearoff=0)
    help_menu.add_command(label=T("menu_about"), command=about_penceresi)
    menubar.add_cascade(label=T("menu_help"), menu=help_menu)

    pencere.config(menu=menubar)

    btn_start = ttk.Button(pencere, text=T("start_clean"))
    btn_start.pack(pady=10)

    progress_var = tk.DoubleVar()
    progressbar = ttk.Progressbar(pencere, maximum=100, variable=progress_var)
    progressbar.pack(fill="x", padx=20)

    btn_cancel = ttk.Button(pencere, text=T("cancel"), state="disabled")
    btn_cancel.pack(pady=10)

    disk_before_label = ttk.Label(pencere, text=T("disk_before"))
    disk_before_label.pack(pady=(10, 2))

    disk_after_label = ttk.Label(pencere, text=T("disk_after"))
    disk_after_label.pack(pady=(0, 10))

    log_text = tk.Text(pencere, height=15, state="disabled", bg="#000000" if ayarlar["dark_mode"] else "white",
                       fg="#00FF00" if ayarlar["dark_mode"] else "black", font=("Consolas", 9))
    log_text.pack(fill="both", expand=True, padx=10, pady=10)

    btn_start.config(command=lambda: baslat_thread(progress_var, progressbar, log_text, disk_before_label, disk_after_label, btn_start, btn_cancel))
    btn_cancel.config(command=lambda: iptal_et(btn_start, btn_cancel))

# --- Hakkında Penceresi ---
def about_penceresi():
    messagebox.showinfo(T("about_title"), T("about_text"))

# --- Çıkış ---
def cikis(pencere):
    if messagebox.askyesno("", T("confirm_exit")):
        pencere.destroy()

# --- Program Başlangıcı ---
if __name__ == "__main__":
    import shutil
    root = tk.Tk()
    ana_pencere_olustur(root)
    root.mainloop()
