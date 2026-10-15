import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk

from appWindow.colors import COLOR_COUNT, task_color_indices, most_advanced_completed_task

PAGE_WIDTH = 20
PAGE_HEIGHT = 30
PAGE_SPACING = 20
SPREAD_GAP = 0
SPREAD_COLUMN_SPACING = 24
MAX_CHILDREN_PER_LINE = 1000


class GlobalView(Gtk.ScrolledWindow):
    SEPARATED = "separadas"
    SPREAD = "enfrentadas"

    def __init__(self, on_page_click=None):
        super().__init__()
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.on_page_click = on_page_click
        self.pages_mode = GlobalView.SEPARATED
        self._project = None
        self._color_index = {}
        self.page_widgets = []
        self.page_boxes = []

        self.container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=PAGE_SPACING)
        self.container.set_margin_top(16)
        self.container.set_margin_bottom(16)
        self.container.set_margin_start(16)
        self.container.set_margin_end(16)
        self.set_child(self.container)

        self.show_empty()

    def _clear(self):
        child = self.container.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.container.remove(child)
            child = next_child

    def show_empty(self):
        self._clear()
        self.page_widgets = []
        self.page_boxes = []
        self._project = None
        label = Gtk.Label(label="No hay ningún proyecto abierto")
        label.add_css_class("dim-label")
        label.set_valign(Gtk.Align.CENTER)
        label.set_vexpand(True)
        self.container.append(label)

    def set_pages_mode(self, mode):
        self.pages_mode = mode
        if self._project is not None:
            self.show_project(self._project)

    def show_project(self, project):
        self._clear()
        self.page_widgets = []
        self.page_boxes = []
        self._project = project
        self._color_index = task_color_indices(project)

        pages = list(enumerate(project.getPages(), start=1))
        if self.pages_mode == GlobalView.SPREAD:
            self._build_spread(pages)
        else:
            self._build_separated(pages)

    def _build_separated(self, pages):
        flow = Gtk.FlowBox()
        flow.add_css_class("global-flow")
        flow.set_column_spacing(PAGE_SPACING)
        flow.set_row_spacing(PAGE_SPACING)
        flow.set_max_children_per_line(MAX_CHILDREN_PER_LINE)
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_halign(Gtk.Align.FILL)
        flow.set_valign(Gtk.Align.START)
        flow.set_hexpand(True)
        for page_index, page in pages:
            flow.append(self._build_page_widget(page, page_index))
        self.container.append(flow)

    def _build_spread(self, pages):
        spreads = [pages[0:1]]
        remaining = pages[1:]
        for index in range(0, len(remaining), 2):
            spreads.append(remaining[index:index + 2])

        flow = Gtk.FlowBox()
        flow.add_css_class("global-flow")
        flow.set_column_spacing(SPREAD_COLUMN_SPACING)
        flow.set_row_spacing(PAGE_SPACING)
        flow.set_max_children_per_line(MAX_CHILDREN_PER_LINE)
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_halign(Gtk.Align.FILL)
        flow.set_valign(Gtk.Align.START)
        flow.set_hexpand(True)
        for row_pages in spreads:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=SPREAD_GAP)
            row.set_valign(Gtk.Align.START)
            row.set_halign(Gtk.Align.CENTER)
            row.set_hexpand(False)
            row.add_css_class("global-spread-row")
            for page_index, page in row_pages:
                row.append(self._build_page_widget(page, page_index))
            flow.append(row)
        self.container.append(flow)

    def _build_page_widget(self, page, page_index):
        rect = Gtk.Box()
        rect.set_size_request(PAGE_WIDTH, PAGE_HEIGHT)
        rect.set_halign(Gtk.Align.CENTER)
        rect.set_valign(Gtk.Align.START)
        rect.set_hexpand(False)
        rect.add_css_class("global-page")

        gesture = Gtk.GestureClick()
        gesture.set_button(1)
        gesture.connect("released", self._on_page_released, page)
        rect.add_controller(gesture)

        self.page_widgets.append((page, page_index, rect))
        self.page_boxes.append(rect)
        self._apply_fill(page, page_index, rect)
        return rect

    def _on_page_released(self, gesture, n_press, x, y, page):
        if self.on_page_click is not None:
            self.on_page_click(page)

    def refresh_status(self):
        for page, page_index, rect in self.page_widgets:
            self._apply_fill(page, page_index, rect)

    def _apply_fill(self, page, page_index, rect):
        for css_class in list(rect.get_css_classes()):
            if css_class == "global-page-neutral" or css_class.startswith("global-page-fill-"):
                rect.remove_css_class(css_class)
        task = most_advanced_completed_task(page.getTasks())
        if task is None:
            rect.add_css_class("global-page-neutral")
        else:
            index = self._color_index.get(task.getTaskName(), 0) % COLOR_COUNT
            rect.add_css_class("global-page-fill-{}".format(index))
        rect.set_tooltip_text(
            "Página {} — {:.0f} % completado".format(
                page_index, page.getPercentileCompleted()
            )
        )