import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.simpledialog import Dialog
import time
import uuid

class PasswordDialog:
    _instance = None  # Class-level flag to track active instance

    def __init__(self, parent, controller):
        if PasswordDialog._instance is not None:
            PasswordDialog._instance.window.lift()  # Bring existing dialog to front
            PasswordDialog._instance.pass_entry.focus_set()  # Focus on password field
            return
        PasswordDialog._instance = self  # Set this as the active instance
        
        self.parent, self.controller = parent, controller
        self.attempts, self.last_attempt_time = 0, 0
        self.font_base, self.font_boton = ("Segoe UI", 10), ("Segoe UI", 10, "bold")
        
        self.window = tk.Toplevel(parent)
        self.window.title("🔒 Acceso Restringido")
        self.window.geometry("350x200")
        self.window.resizable(False, False)
        self.window.configure(bg="#f0f2f5")
        self.window.attributes('-topmost', True)
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)  # Handle window close
        
        self._build_ui()
        self._bind_keys()
        self._center_window()

    def _build_ui(self):
        main_frame = tk.Frame(self.window, bg="#f0f2f5", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(main_frame, text="INGRESE LA CONTRASEÑA", font=self.font_boton, bg="#f0f2f5").pack(pady=(0, 15))
        
        pass_frame = tk.Frame(main_frame, bg="#f0f2f5")
        pass_frame.pack(fill=tk.X, pady=5)
        
        self.pass_var, self.show_pass = tk.StringVar(), tk.BooleanVar(value=False)
        tk.Label(pass_frame, text="Contraseña:", bg="#f0f2f5", font=self.font_base).pack(side=tk.LEFT)
        
        self.pass_entry = ttk.Entry(pass_frame, textvariable=self.pass_var, show="*", width=20, font=self.font_base)
        self.pass_entry.pack(side=tk.LEFT, padx=5)
        self.pass_entry.focus_set()
        
        ttk.Checkbutton(pass_frame, text="Mostrar", variable=self.show_pass, command=self._toggle_password).pack(side=tk.LEFT)
        
        btn_frame = tk.Frame(main_frame, bg="#f0f2f5")
        btn_frame.pack(pady=(15, 0))
        ttk.Button(btn_frame, text="Aceptar", command=self._verify_password, style='Accent.TButton').pack(side=tk.LEFT, padx=5)

    def _bind_keys(self):
        self.window.bind('<Return>', lambda e: self._verify_password())
        self.window.bind('<Escape>', lambda e: self._on_close())
        self.window.bind('<Control-Key-m>', lambda e: self.show_pass.set(not self.show_pass.get()) or self._toggle_password())

    def _center_window(self):
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - self.window.winfo_width()) // 2
        y = (self.window.winfo_screenheight() - self.window.winfo_height()) // 2
        self.window.geometry(f'+{x}+{y}')

    def _toggle_password(self):
        self.pass_entry.config(show="" if self.show_pass.get() else "*")

    def _verify_password(self):
        current_time = time.time()
        if self.attempts >= 3 and (current_time - self.last_attempt_time) < 10:
            messagebox.showwarning("Bloqueado", f"Espere {int(10 - (current_time - self.last_attempt_time))} segundos.", parent=self.window)
            return

        if self.pass_var.get() == "password&clave&contrasena":
            self.window.destroy()
            PasswordDialog._instance = None  # Clear instance on successful login
            GestionUnidadesDialog(self.parent, self.controller.model, self.controller)
            self.attempts = 0
        else:
            self.attempts += 1
            self.last_attempt_time = current_time
            self.pass_var.set("")
            self.pass_entry.focus_set()
            
            if self.attempts >= 3:
                messagebox.showwarning("🚫 Bloqueado", "⚠️ Espere 10 segundos para reintentar.", parent=self.window)
                self.controller.view.menu_gestion_unidades.entryconfig(0, state=tk.DISABLED)
                self.parent.after(10000, lambda: self.controller.view.menu_gestion_unidades.entryconfig(0, state=tk.NORMAL) or setattr(self, 'attempts', 0))
            else:
                messagebox.showerror("❌ Error", f"🔐 Contraseña incorrecta. Intentos restantes: {3 - self.attempts}", parent=self.window)

    def _on_close(self):
        self.window.destroy()
        PasswordDialog._instance = None  # Clear instance on close

class GestionUnidadesDialog(Dialog):
    def __init__(self, parent, model, controller):
        self.model, self.controller = model, controller
        self.style = ttk.Style()
        self._configure_styles()
        super().__init__(parent, "⚙️ Gestión de Unidades")

    def _configure_styles(self):
        self.style.theme_use('clam')
        self.style.configure('Gestion.TButton', font=("Segoe UI", 10), padding=6)
        self.style.configure('Accent.TButton', font=("Segoe UI", 10, "bold"), foreground='white', background='#4a6baf')
        self.style.map('Accent.TButton', background=[('active', '#3a5a9f'), ('pressed', '#2a4a8f')])
        self.style.configure('TCombobox', font=("Segoe UI", 10))
        self.style.configure('Treeview', font=("Segoe UI", 9), rowheight=25)
        self.style.configure('Treeview.Heading', font=("Segoe UI", 9, "bold"))

    def body(self, master):
        self.geometry("400x350")
        self.resizable(False, False)
        self.configure(bg="#f0f2f5")
        self.bind('<Escape>', lambda e: self.destroy())
        self.bind('<Control-Key-a>', lambda e: self._agregar_unidad())
        self.bind('<Control-Key-e>', lambda e: self._editar_unidad())
        self.bind('<Delete>', lambda e: self._eliminar_unidad())

        main_frame = tk.Frame(master, bg="#f0f2f5", padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(main_frame, bg="#f0f2f5")
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        for text, cmd in [("➕ Agregar unidad", self._agregar_unidad), ("✏️ Editar alias o código", self._editar_unidad), ("🗑️ Dar de baja unidad", self._eliminar_unidad)]:
            ttk.Button(btn_frame, text=text, command=cmd, style='Gestion.TButton').pack(fill=tk.X, pady=5)

        self.lista_frame = tk.Frame(main_frame, bg="#f0f2f5")
        self.lista_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.tree = ttk.Treeview(self.lista_frame, columns=('alias', 'codigo', 'tipo'), show='headings', height=8)
        self.tree.heading('alias', text='🏁 Alias')
        self.tree.heading('codigo', text='🚦Código')
        self.tree.heading('tipo', text='🚔 Tipo')
        self.tree.column('alias', width=150)
        self.tree.column('codigo', width=100)
        self.tree.column('tipo', width=80)
        
        scrollbar = ttk.Scrollbar(self.lista_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind('<Double-1>', lambda e: self._editar_unidad())
        self._actualizar_lista()

    def _actualizar_lista(self):
        self.tree.delete(*self.tree.get_children())
        for alias, codigo in self.model.ALIAS_UNIDADES.items():
            tipo = "Camioneta" if codigo in self.model.CAMIONETAS else "Auto"
            self.tree.insert('', tk.END, values=(alias, codigo, tipo))

    def _create_unit_dialog(self, title, default_values=None, is_edit=False):
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.geometry("400x250")
        dialog.resizable(False, False)
        dialog.configure(bg="#f0f2f5")
        dialog.attributes('-topmost', True)
        dialog.bind('<Escape>', lambda e: dialog.destroy())
        dialog.bind('<Return>', lambda e: guardar())

        tk.Label(dialog, text="Alias (ej: H1 / EUI-621):", bg="#f0f2f5", font=self.style.lookup('TLabel', 'font')).pack(pady=(10, 0))
        alias_entry = ttk.Entry(dialog)
        alias_entry.pack(pady=5, padx=20, fill=tk.X)
        
        tk.Label(dialog, text="Código interno (ej: EUI-621):", bg="#f0f2f5").pack()
        codigo_entry = ttk.Entry(dialog)
        codigo_entry.pack(pady=5, padx=20, fill=tk.X)
        
        tk.Label(dialog, text="Tipo de unidad:", bg="#f0f2f5").pack()
        tipo_var = tk.StringVar(value=default_values[2].upper() if is_edit else "PICKUP")
        tipo_frame = tk.Frame(dialog, bg="#f0f2f5")
        tipo_frame.pack()
        
        for text, value in [("Camioneta (PICKUP)", "PICKUP"), ("Auto (SEDAN)", "AUTO")]:
            ttk.Radiobutton(tipo_frame, text=text, variable=tipo_var, value=value).pack(side=tk.LEFT, padx=10)
        
        if is_edit:
            alias_entry.insert(0, default_values[0])
            codigo_entry.insert(0, default_values[1])

        def guardar():
            alias, codigo, tipo = alias_entry.get().strip(), codigo_entry.get().strip(), tipo_var.get()
            if not alias or not codigo:
                messagebox.showwarning("⚠️ Campos Incompletos", "📄 Complete todos los campos.", parent=dialog)
                return
            
            if is_edit:
                if self.model.editar_unidad(default_values[0], alias, codigo, tipo):
                    messagebox.showinfo("✅ Edición Exitosa", f"Unidad '{default_values[0]}' actualizada a '{alias}'.", parent=self)
                    dialog.destroy()
                    self._actualizar_vista()
                else:
                    messagebox.showwarning("⚠️ Error", "✏️ No se pudo editar la unidad.", parent=dialog)
            else:
                if alias in self.model.ALIAS_UNIDADES or codigo in self.model.ALIAS_UNIDADES.values():
                    messagebox.showwarning("⚠️ Duplicado", "🚫 Alias o código ya existe.", parent=dialog)
                    return
                self.model.agregar_unidad(alias, codigo, tipo)
                messagebox.showinfo("✅ Unidad Agregada", f"Unidad '{alias}' agregada.", parent=self)
                dialog.destroy()
                self._actualizar_vista()

        btn_frame = tk.Frame(dialog, bg="#f0f2f5")
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Guardar", command=guardar, style='Accent.TButton').pack(side=tk.RIGHT, padx=10)

    def _agregar_unidad(self):
        self._create_unit_dialog("➕ Agregar Unidad")

    def _editar_unidad(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("⚠️ Advertencia", "🗂️ Seleccione una unidad.", parent=self)
            return
        self._create_unit_dialog("✏️ Editar Unidad", self.tree.item(seleccion[0])['values'], is_edit=True)

    def _eliminar_unidad(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("⚠️ Advertencia", "🗂️ Seleccione una unidad.", parent=self)
            return
        alias = self.tree.item(seleccion[0])['values'][0]
        if messagebox.askyesno("🗑️ Confirmar", f"📂 ¿Eliminar unidad '{alias}'?", parent=self):
            if self.model.eliminar_unidad(alias):
                messagebox.showinfo("✅ Eliminación Exitosa", f"Unidad '{alias}' eliminada.", parent=self)
                self._actualizar_vista()
            else:
                messagebox.showerror("❌ Error", f"No se pudo eliminar la unidad '{alias}'.", parent=self)

    def _actualizar_vista(self):
        self._actualizar_lista()
        self.controller.model._cargar_unidades_desde_archivo()
        filtro_actual = self.controller.view.get_filtro_var()
        selected_units = [fila['alias'] for fila in self.controller.view.fila_widgets_data if fila['var_chk'].get()] if filtro_actual == "MANUAL" else []
        self.controller.view.rebuild_unit_table()
        self.controller.aplicar_filtro(filtro_actual)
        if filtro_actual == "MANUAL" and selected_units:
            self.controller.view.update_unit_display(units_to_display=selected_units, filter_type="MANUAL", 
                                                    is_editing_mode=self.controller.editing_mode, selected_units_by_checkbox=selected_units)

    def buttonbox(self):
        pass