import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import shutil
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import webbrowser

class OrderFlowPro:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("?? OrderFlowPRO v2.0 - Sistema de Gestión de Pedidos")
        self.root.geometry("1300x850")
        self.root.configure(bg="#f8fafc")
        self.root.resizable(True, True)
        
        # Configurar estilos
        self.setup_styles()
        
        # Datos órdenes (JSON local)
        self.data_file = Path("orderflow_data.json")
        self.backup_folder = Path("backups")
        self.backup_folder.mkdir(exist_ok=True)
        
        self.ordenes = self.cargar_datos()
        self.orden_seleccionada = None
        self.filtro_actual = "Todas"
        
        self.setup_modern_gui()
        
        # Atajos de teclado
        self.setup_shortcuts()
    
    def setup_styles(self):
        """Configurar estilos de colores"""
        self.colores = {
            'primary': "#3182ce",
            'success': "#48bb78",
            'danger': "#f56565",
            'warning': "#ed8936",
            'info': "#4299e1",
            'bg': "#f8fafc",
            'text': "#2d3748",
            'text_light': "#4a5568"
        }
    
    def setup_modern_gui(self):
        """Interfaz principal mejorada"""
        # Header profesional
        header = tk.Frame(self.root, bg=self.colores['primary'], height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title_frame = tk.Frame(header, bg=self.colores['primary'])
        title_frame.pack(side=tk.LEFT, padx=30, pady=20)
        
        title = tk.Label(title_frame, text="?? OrderFlowPRO", 
                        font=("Segoe UI", 28, "bold"), bg=self.colores['primary'], fg="white")
        title.pack(side=tk.LEFT)
        
        version = tk.Label(title_frame, text="v2.0", 
                          font=("Segoe UI", 10), bg=self.colores['primary'], fg="#e2e8f0")
        version.pack(side=tk.LEFT, padx=(10, 0))
        
        # Panel de estadísticas rápidas
        stats_frame = tk.Frame(header, bg=self.colores['primary'])
        stats_frame.pack(side=tk.RIGHT, padx=20, pady=15)
        
        self.total_ventas_label = tk.Label(stats_frame, text="Total: $0", 
                                          font=("Segoe UI", 14, "bold"), 
                                          bg=self.colores['primary'], fg="white")
        self.total_ventas_label.pack(side=tk.RIGHT, padx=15)
        
        self.total_ordenes_label = tk.Label(stats_frame, text="Órdenes: 0", 
                                           font=("Segoe UI", 14, "bold"), 
                                           bg=self.colores['primary'], fg="white")
        self.total_ordenes_label.pack(side=tk.RIGHT, padx=15)
        
        # Botones header
        btn_frame = tk.Frame(header, bg=self.colores['primary'])
        btn_frame.pack(side=tk.RIGHT, padx=20, pady=15)
        
        btn_nueva = tk.Button(btn_frame, text="? NUEVA ORDEN", 
                             command=self.nueva_orden,
                             bg=self.colores['success'], fg="white", 
                             font=("Segoe UI", 12, "bold"),
                             padx=15, pady=5, relief="flat", cursor="hand2")
        btn_nueva.pack(side=tk.RIGHT, padx=5)
        
        btn_backup = tk.Button(btn_frame, text="?? BACKUP", 
                              command=self.crear_backup,
                              bg=self.colores['info'], fg="white", 
                              font=("Segoe UI", 12, "bold"),
                              padx=15, pady=5, relief="flat", cursor="hand2")
        btn_backup.pack(side=tk.RIGHT, padx=5)
        
        # Paneles principales
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Izquierda: Lista órdenes con filtros
        left_frame = tk.Frame(main_paned, bg=self.colores['bg'])
        main_paned.add(left_frame, weight=1)
        
        # Filtros
        filter_frame = tk.Frame(left_frame, bg=self.colores['bg'])
        filter_frame.pack(fill=tk.X, padx=20, pady=(10, 5))
        
        tk.Label(filter_frame, text="?? Filtrar:", 
                font=("Segoe UI", 11), bg=self.colores['bg']).pack(side=tk.LEFT, padx=(0, 10))
        
        self.filtro_var = tk.StringVar(value="Todas")
        filtros = ["Todas", "Pendiente", "Preparando", "Enviado", "Entregado", "Cancelado"]
        filtro_combo = ttk.Combobox(filter_frame, textvariable=self.filtro_var, 
                                    values=filtros, state="readonly", width=15)
        filtro_combo.pack(side=tk.LEFT)
        filtro_combo.bind("<<ComboboxSelected>>", self.aplicar_filtro)
        
        tk.Label(filter_frame, text="Buscar:", 
                font=("Segoe UI", 11), bg=self.colores['bg']).pack(side=tk.LEFT, padx=(20, 10))
        
        self.busqueda_var = tk.StringVar()
        busqueda_entry = tk.Entry(filter_frame, textvariable=self.busqueda_var, 
                                 font=("Segoe UI", 11), width=20)
        busqueda_entry.pack(side=tk.LEFT)
        busqueda_entry.bind("<KeyRelease>", self.buscar_ordenes)
        
        # Treeview órdenes mejorado
        columns = ("ID", "Cliente", "Producto", "Cantidad", "Total", "Estado", "Fecha")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=20)
        
        # Configurar columnas
        col_widths = {"ID": 120, "Cliente": 150, "Producto": 150, 
                     "Cantidad": 80, "Total": 100, "Estado": 100, "Fecha": 140}
        
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.ordenar_por_columna(c))
            self.tree.column(col, width=col_widths[col])
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        self.tree.bind("<<TreeviewSelect>>", self.seleccionar_orden)
        
        # Derecha: Detalles + acciones
        right_frame = tk.Frame(main_paned, bg=self.colores['bg'])
        main_paned.add(right_frame, weight=1)
        
        # Notebook para pestañas
        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Pestaña de detalles
        detalles_frame = ttk.Frame(notebook)
        notebook.add(detalles_frame, text="?? Detalles de Orden")
        
        # Formulario detalles mejorado
        self.crear_formulario_detalles(detalles_frame)
        
        # Pestaña de notas adicionales
        notas_frame = ttk.Frame(notebook)
        notebook.add(notas_frame, text="?? Notas")
        
        self.notas_text = scrolledtext.ScrolledText(notas_frame, wrap=tk.WORD, 
                                                     font=("Segoe UI", 11), height=15)
        self.notas_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pestaña de historial
        historial_frame = ttk.Frame(notebook)
        notebook.add(historial_frame, text="?? Historial")
        
        self.historial_text = scrolledtext.ScrolledText(historial_frame, wrap=tk.WORD, 
                                                        font=("Segoe UI", 10), height=15)
        self.historial_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panel de acciones
        action_frame = tk.Frame(right_frame, bg=self.colores['bg'])
        action_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        buttons = [
            ("?? GUARDAR", self.guardar_orden, self.colores['success']),
            ("??? ELIMINAR", self.eliminar_orden, self.colores['danger']),
            ("?? FACTURA PDF", self.generar_factura_pdf, self.colores['warning']),
            ("?? ENVIAR EMAIL", self.enviar_email, self.colores['info']),
            ("??? IMPRIMIR", self.imprimir_orden, self.colores['primary'])
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(action_frame, text=text, command=command,
                           bg=color, fg="white", font=("Segoe UI", 11, "bold"),
                           padx=15, pady=8, relief="flat", cursor="hand2")
            btn.pack(side=tk.LEFT, padx=5)
        
        # Panel de reportes
        self.crear_panel_reportes()
        
        # Actualizar estadísticas
        self.actualizar_estadisticas()
    
    def crear_formulario_detalles(self, parent):
        """Crear formulario de detalles mejorado"""
        form_frame = tk.Frame(parent, bg=self.colores['bg'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Configurar grid
        form_frame.grid_columnconfigure(1, weight=1)
        form_frame.grid_columnconfigure(3, weight=1)
        
        # Campos del formulario
        campos = [
            ("ID:", "id_entry", tk.Entry, {}),
            ("Cliente:*", "cliente_entry", tk.Entry, {}),
            ("Teléfono:", "telefono_entry", tk.Entry, {}),
            ("Email:", "email_entry", tk.Entry, {}),
            ("Producto:*", "producto_entry", tk.Entry, {}),
            ("Cantidad:*", "cantidad_entry", tk.Entry, {}),
            ("Precio Unit:*", "precio_entry", tk.Entry, {}),
            ("Total:", "total_entry", tk.Entry, {"state": "readonly"}),
            ("Dirección:", "direccion_entry", tk.Entry, {}),
            ("Estado:", "estado_entry", ttk.Combobox, {"values": ["Pendiente", "Preparando", "Enviado", "Entregado", "Cancelado"], "state": "readonly"})
        ]
        
        self.entries = {}
        row = 0
        
        for i, (label, var, widget_type, kwargs) in enumerate(campos):
            col = (i % 2) * 2
            row = i // 2
            
            # Label
            lbl = tk.Label(form_frame, text=label, font=("Segoe UI", 11, "bold"),
                          bg=self.colores['bg'], fg=self.colores['text'])
            lbl.grid(row=row, column=col, sticky="w", pady=8, padx=(0, 10))
            
            # Widget de entrada
            if widget_type == tk.Entry:
                entry = widget_type(form_frame, font=("Segoe UI", 11), 
                                   bg="white", relief="solid", bd=1)
                if var == "total_entry":
                    entry.config(state="readonly")
            else:
                entry = widget_type(form_frame, **kwargs)
                entry.configure(font=("Segoe UI", 11))
            
            entry.grid(row=row, column=col+1, sticky="ew", pady=8, padx=(0, 20))
            self.entries[var] = entry
            
            # Eventos para cálculo automático
            if var in ["cantidad_entry", "precio_entry"]:
                entry.bind("<KeyRelease>", self.calcular_total)
        
        # Botón calcular
        calc_btn = tk.Button(form_frame, text="?? Calcular Total", 
                            command=self.calcular_total,
                            bg=self.colores['info'], fg="white",
                            font=("Segoe UI", 10), relief="flat")
        calc_btn.grid(row=row+1, column=1, pady=10, sticky="e")
    
    def crear_panel_reportes(self):
        """Crear panel de reportes avanzados"""
        report_frame = tk.LabelFrame(self.root, text="?? Reportes Avanzados", 
                                    font=("Segoe UI", 13, "bold"), 
                                    bg=self.colores['bg'], fg=self.colores['text'])
        report_frame.pack(fill=tk.X, padx=40, pady=(0, 20))
        
        # Frame para botones de reportes
        btn_report_frame = tk.Frame(report_frame, bg=self.colores['bg'])
        btn_report_frame.pack(pady=15)
        
        reportes = [
            ("?? VENTAS HOY", self.reporte_hoy, self.colores['primary']),
            ("?? VENTAS SEMANA", self.reporte_semana, self.colores['success']),
            ("?? VENTAS MES", self.reporte_mes, self.colores['warning']),
            ("?? TOP PRODUCTOS", self.reporte_top_productos, self.colores['info']),
            ("?? CLIENTES FRECUENTES", self.reporte_clientes, self.colores['danger']),
            ("?? EXPORTAR CSV", self.exportar_csv, self.colores['text_light'])
        ]
        
        for text, command, color in reportes:
            btn = tk.Button(btn_report_frame, text=text, command=command,
                           bg=color, fg="white", font=("Segoe UI", 10, "bold"),
                           padx=12, pady=5, relief="flat", cursor="hand2")
            btn.pack(side=tk.LEFT, padx=5)
        
        # Panel de estadísticas detalladas
        stats_detail_frame = tk.Frame(report_frame, bg=self.colores['bg'])
        stats_detail_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        self.stats_labels = {}
        estadisticas = [
            ("promedio", "Promedio por orden: $0"),
            ("pendientes", "Pendientes: 0"),
            ("entregadas", "Entregadas: 0")
        ]
        
        for i, (key, text) in enumerate(estadisticas):
            label = tk.Label(stats_detail_frame, text=text, 
                            font=("Segoe UI", 10), bg=self.colores['bg'], 
                            fg=self.colores['text_light'])
            label.pack(side=tk.LEFT, padx=20)
            self.stats_labels[key] = label
    
    def setup_shortcuts(self):
        """Configurar atajos de teclado"""
        self.root.bind("<Control-n>", lambda e: self.nueva_orden())
        self.root.bind("<Control-s>", lambda e: self.guardar_orden())
        self.root.bind("<Delete>", lambda e: self.eliminar_orden())
        self.root.bind("<Control-f>", lambda e: self.busqueda_var.set(""))
    
    def cargar_datos(self):
        """Cargar datos con manejo de errores mejorado"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Asegurar que todos los registros tengan los campos necesarios
                    for orden in data:
                        if 'notas' not in orden:
                            orden['notas'] = ""
                        if 'email' not in orden:
                            orden['email'] = ""
                        if 'historial' not in orden:
                            orden['historial'] = []
                    return data
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar datos: {e}")
                return []
        return []
    
    def guardar_datos(self):
        """Guardar datos con backup automático"""
        try:
            # Crear backup antes de guardar
            if self.data_file.exists():
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                shutil.copy(self.data_file, self.backup_folder / backup_name)
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.ordenes, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar datos: {e}")
    
    def crear_backup(self):
        """Crear backup manual"""
        try:
            backup_name = f"backup_manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            shutil.copy(self.data_file, self.backup_folder / backup_name)
            messagebox.showinfo("Backup", f"Backup creado: {backup_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear backup: {e}")
    
    def calcular_total(self, event=None):
        """Calcular total automáticamente"""
        try:
            cantidad = float(self.entries["cantidad_entry"].get() or 0)
            precio = float(self.entries["precio_entry"].get() or 0)
            total = cantidad * precio
            
            self.entries["total_entry"].config(state="normal")
            self.entries["total_entry"].delete(0, tk.END)
            self.entries["total_entry"].insert(0, f"{total:.2f}")
            self.entries["total_entry"].config(state="readonly")
        except ValueError:
            pass
    
    def nueva_orden(self):
        """Crear nueva orden"""
        self.orden_seleccionada = None
        self.limpiar_formulario()
        self.tree.selection_remove(self.tree.selection())
        self.entries["id_entry"].config(state="normal")
        self.entries["id_entry"].insert(0, datetime.now().strftime("%Y%m%d-%H%M%S"))
        self.entries["id_entry"].config(state="readonly")
        
        # Enfocar primer campo
        self.entries["cliente_entry"].focus()
    
    def limpiar_formulario(self):
        """Limpiar todos los campos del formulario"""
        for key, entry in self.entries.items():
            if isinstance(entry, tk.Entry):
                entry.delete(0, tk.END)
            elif isinstance(entry, ttk.Combobox):
                entry.set("")
        
        self.notas_text.delete(1.0, tk.END)
    
    def seleccionar_orden(self, event):
        """Seleccionar orden y mostrar detalles"""
        seleccion = self.tree.selection()
        if seleccion:
            item = self.tree.item(seleccion[0])
            orden_id = item['values'][0]
            orden = next((o for o in self.ordenes if o['id'] == orden_id), None)
            
            if orden:
                self.orden_seleccionada = orden
                self.llenar_formulario(orden)
    
    def llenar_formulario(self, orden):
        """Llenar formulario con datos de orden"""
        for key, value in orden.items():
            if key in self.entries:
                if isinstance(self.entries[key], tk.Entry):
                    self.entries[key].delete(0, tk.END)
                    self.entries[key].insert(0, str(value))
                elif isinstance(self.entries[key], ttk.Combobox):
                    self.entries[key].set(str(value))
        
        # Llenar notas
        self.notas_text.delete(1.0, tk.END)
        self.notas_text.insert(1.0, orden.get('notas', ''))
        
        # Llenar historial
        self.historial_text.delete(1.0, tk.END)
        historial = orden.get('historial', [])
        for evento in historial:
            self.historial_text.insert(tk.END, f"{evento}\n")
    
    def guardar_orden(self):
        """Guardar orden (nueva o existente)"""
        try:
            # Validar campos requeridos
            campos_requeridos = ['cliente', 'producto', 'cantidad', 'precio']
            for campo in campos_requeridos:
                if not self.entries[f"{campo}_entry"].get().strip():
                    messagebox.showwarning("Validación", f"El campo {campo} es requerido")
                    return
            
            # Preparar datos
            datos = {
                'id': self.entries['id_entry'].get() or datetime.now().strftime("%Y%m%d-%H%M%S"),
                'cliente': self.entries['cliente_entry'].get(),
                'telefono': self.entries['telefono_entry'].get(),
                'email': self.entries['email_entry'].get(),
                'producto': self.entries['producto_entry'].get(),
                'cantidad': int(self.entries['cantidad_entry'].get()),
                'precio': float(self.entries['precio_entry'].get()),
                'total': float(self.entries['total_entry'].get() or 0),
                'direccion': self.entries['direccion_entry'].get(),
                'estado': self.entries['estado_entry'].get(),
                'notas': self.notas_text.get(1.0, tk.END).strip(),
                'fecha': datetime.now().isoformat()
            }
            
            # Registrar cambio de estado en historial
            if self.orden_seleccionada:
                estado_anterior = self.orden_seleccionada.get('estado')
                if estado_anterior != datos['estado']:
                    historial_evento = f"{datetime.now().strftime('%Y-%m-%d %H:%M')} - Estado cambiado: {estado_anterior} ? {datos['estado']}"
                    datos['historial'] = self.orden_seleccionada.get('historial', []) + [historial_evento]
                else:
                    datos['historial'] = self.orden_seleccionada.get('historial', [])
            else:
                datos['historial'] = [f"{datetime.now().strftime('%Y-%m-%d %H:%M')} - Orden creada"]
            
            # Guardar
            if self.orden_seleccionada:
                idx = next(i for i, o in enumerate(self.ordenes) if o['id'] == self.orden_seleccionada['id'])
                self.ordenes[idx] = datos
                messagebox.showinfo("Guardado", f"? Orden {datos['id']} actualizada")
            else:
                self.ordenes.append(datos)
                messagebox.showinfo("Guardado", f"? Nueva orden {datos['id']} creada")
            
            self.guardar_datos()
            self.aplicar_filtro()
            self.actualizar_estadisticas()
            
        except ValueError as e:
            messagebox.showerror("Error", f"Error en datos numéricos: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {e}")
    
    def eliminar_orden(self):
        """Eliminar orden con confirmación"""
        if self.orden_seleccionada:
            respuesta = messagebox.askyesno("Confirmar", 
                                          f"¿Eliminar orden #{self.orden_seleccionada['id']}?")
            if respuesta:
                self.ordenes = [o for o in self.ordenes if o['id'] != self.orden_seleccionada['id']]
                self.guardar_datos()
                self.aplicar_filtro()
                self.limpiar_formulario()
                self.orden_seleccionada = None
                self.actualizar_estadisticas()
                messagebox.showinfo("Eliminado", "? Orden eliminada")
    
    def aplicar_filtro(self, event=None):
        """Aplicar filtro de estado y búsqueda"""
        filtro = self.filtro_var.get()
        busqueda = self.busqueda_var.get().lower()
        
        ordenes_filtradas = self.ordenes.copy()
        
        # Filtrar por estado
        if filtro != "Todas":
            ordenes_filtradas = [o for o in ordenes_filtradas if o.get('estado') == filtro]
        
        # Filtrar por búsqueda
        if busqueda:
            ordenes_filtradas = [o for o in ordenes_filtradas if 
                                busqueda in o.get('id', '').lower() or
                                busqueda in o.get('cliente', '').lower() or
                                busqueda in o.get('producto', '').lower() or
                                busqueda in o.get('telefono', '').lower()]
        
        self.actualizar_lista(ordenes_filtradas)
    
    def buscar_ordenes(self, event=None):
        """Buscar órdenes en tiempo real"""
        self.aplicar_filtro()
    
    def ordenar_por_columna(self, col):
        """Ordenar órdenes por columna"""
        # Obtener índice de columna
        columns = ("ID", "Cliente", "Producto", "Cantidad", "Total", "Estado", "Fecha")
        col_index = columns.index(col)
        
        # Ordenar datos
        ordenes_ordenadas = sorted(self.ordenes, 
                                  key=lambda x: list(x.values())[col_index] if col_index < len(x) else "")
        
        self.actualizar_lista(ordenes_ordenadas)
    
    def actualizar_lista(self, ordenes=None):
        """Actualizar Treeview con órdenes"""
        if ordenes is None:
            ordenes = self.ordenes
        
        # Limpiar tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Llenar con órdenes
        for orden in ordenes[-100:]:  # Últimas 100
            self.tree.insert("", "end", values=(
                orden.get('id', 'N/A'),
                orden.get('cliente', 'N/A'),
                orden.get('producto', 'N/A'),
                orden.get('cantidad', 0),
                f"${orden.get('total', 0):.2f}",
                orden.get('estado', 'Pendiente'),
                orden.get('fecha', '')[:16]
            ))
    
    def actualizar_estadisticas(self):
        """Actualizar estadísticas en tiempo real"""
        total_ventas = sum(float(o.get('total', 0)) for o in self.ordenes)
        total_ordenes = len(self.ordenes)
        promedio = total_ventas / total_ordenes if total_ordenes > 0 else 0
        pendientes = len([o for o in self.ordenes if o.get('estado') == 'Pendiente'])
        entregadas = len([o for o in self.ordenes if o.get('estado') == 'Entregado'])
        
        self.total_ventas_label.config(text=f"Total: ${total_ventas:,.2f}")
        self.total_ordenes_label.config(text=f"Órdenes: {total_ordenes}")
        self.stats_labels['promedio'].config(text=f"Promedio por orden: ${promedio:.2f}")
        self.stats_labels['pendientes'].config(text=f"Pendientes: {pendientes}")
        self.stats_labels['entregadas'].config(text=f"Entregadas: {entregadas}")
    
    def generar_factura_pdf(self):
        """Generar factura profesional en PDF"""
        if not self.orden_seleccionada:
            messagebox.showwarning("Advertencia", "Selecciona una orden primero")
            return
        
        try:
            orden = self.orden_seleccionada
            filename = f"factura_{orden['id']}.pdf"
            
            doc = SimpleDocTemplate(filename, pagesize=letter)
            story = []
            
            # Estilos
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#3182ce'),
                spaceAfter=30
            )
            
            # Encabezado
            story.append(Paragraph("?? OrderFlowPRO", title_style))
            story.append(Paragraph(f"FACTURA #{orden['id']}", styles['Heading2']))
            story.append(Spacer(1, 20))
            
            # Datos del cliente
            client_data = [
                ["Cliente:", orden.get('cliente', 'N/A')],
                ["Teléfono:", orden.get('telefono', 'N/A')],
                ["Email:", orden.get('email', 'N/A')],
                ["Fecha:", datetime.now().strftime('%d/%m/%Y %H:%M')]
            ]
            
            client_table = Table(client_data, colWidths=[100, 300])
            client_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4a5568')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(client_table)
            story.append(Spacer(1, 20))
            
            # Detalles del producto
            product_data = [
                ["Producto", "Cantidad", "Precio Unit.", "Total"],
                [orden.get('producto', 'N/A'), 
                 str(orden.get('cantidad', 0)),
                 f"${orden.get('precio', 0):.2f}",
                 f"${orden.get('total', 0):.2f}"]
            ]
            
            product_table = Table(product_data, colWidths=[200, 80, 100, 100])
            product_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3182ce')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(product_table)
            story.append(Spacer(1, 20))
            
            # Total
            total_data = [["TOTAL:", f"${orden.get('total', 0):.2f}"]]
            total_table = Table(total_data, colWidths=[300, 100])
            total_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 14),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2d3748'))
            ]))
            story.append(total_table)
            story.append(Spacer(1, 30))
            
            # Notas
            if orden.get('notas'):
                story.append(Paragraph("Notas:", styles['Heading4']))
                story.append(Paragraph(orden['notas'], styles['Normal']))
                story.append(Spacer(1, 20))
            
            # Pie de página
            story.append(Paragraph("¡Gracias por tu compra!", styles['Italic']))
            story.append(Paragraph("OrderFlowPRO - Sistema de Gestión de Pedidos", styles['Normal']))
            
            # Generar PDF
            doc.build(story)
            
            messagebox.showinfo("Factura", f"Factura generada: {filename}")
            webbrowser.open(filename)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar factura: {e}")
    
    def enviar_email(self):
        """Enviar factura por email (simulado)"""
        if not self.orden_seleccionada:
            messagebox.showwarning("Advertencia", "Selecciona una orden primero")
            return
        
        email = self.orden_seleccionada.get('email')
        if not email:
            messagebox.showwarning("Advertencia", "La orden no tiene email registrado")
            return
        
        # Simulación de envío de email
        messagebox.showinfo("Email", f"Factura enviada a {email}")
    
    def imprimir_orden(self):
        """Imprimir orden (simulado)"""
        if not self.orden_seleccionada:
            messagebox.showwarning("Advertencia", "Selecciona una orden primero")
            return
        
        self.generar_factura_pdf()
        messagebox.showinfo("Impresión", "Documento listo para imprimir")
    
    def reporte_hoy(self):
        """Reporte de ventas del día"""
        hoy = datetime.now().strftime("%Y-%m-%d")
        ventas_hoy = [o for o in self.ordenes if hoy in o.get('fecha', '')]
        total_hoy = sum(float(o.get('total', 0)) for o in ventas_hoy)
        
        detalle = "\n".join([f"{o.get('id')} - {o.get('cliente')}: ${o.get('total', 0):.2f}" 
                            for o in ventas_hoy[-10