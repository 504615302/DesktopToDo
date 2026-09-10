from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from model.report import ReportTemplate
from service.report_service import ReportService
from ui.framed_dialog import FramedDialog
from ui.styles import Theme


class TemplateEditDialog(FramedDialog):
    def __init__(self, theme: Theme, template: ReportTemplate | None = None, parent=None):
        super().__init__(theme, "编辑模板" if template else "新增模板", parent, width=460)
        self.name_edit = QLineEdit(template.name if template else "")
        self.name_edit.setPlaceholderText("公司标准模板")
        self.content_edit = QPlainTextEdit(template.content if template else "")
        self.content_edit.setPlaceholderText("支持 {{start_date}} {{end_date}} {{completed_tasks}} {{memos}} {{unfinished_tasks}} {{user_notes}}")
        self.content_edit.setMinimumHeight(220)
        save = QPushButton("保存")
        save.setObjectName("primaryButton")
        save.setFixedHeight(36)
        save.clicked.connect(self.accept)
        self.root.addWidget(self.caption("模板名称"))
        self.root.addWidget(self.name_edit)
        self.root.addWidget(self.caption("模板内容"))
        self.root.addWidget(self.content_edit)
        self.root.addWidget(save)

    def result_values(self) -> tuple[str, str]:
        return self.name_edit.text().strip(), self.content_edit.toPlainText()


class TemplateListDialog(FramedDialog):
    def __init__(self, theme: Theme, reports: ReportService, parent=None):
        super().__init__(theme, "周报模板", parent, width=460)
        self._theme = theme
        self._reports = reports
        self.box = QVBoxLayout()
        self.root.addLayout(self.box)
        add = QPushButton("新增模板")
        add.setObjectName("primaryButton")
        add.clicked.connect(lambda: self._edit(None))
        self.root.addWidget(add)
        self._reload()

    def _reload(self) -> None:
        while self.box.count():
            item = self.box.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        templates = self._reports.templates()
        for template in templates:
            row = QWidget()
            layout = QHBoxLayout(row)
            layout.setContentsMargins(0, 0, 0, 0)
            mark = "默认 · " if template.is_default else ""
            label = QLabel(f"{mark}{template.name}")
            edit = QPushButton("编辑")
            copy = QPushButton("复制")
            default = QPushButton("设为默认")
            delete = QPushButton("删除")
            delete.setObjectName("dangerButton")
            edit.clicked.connect(lambda _=False, item=template: self._edit(item))
            copy.clicked.connect(lambda _=False, item=template: self._copy(item))
            default.clicked.connect(lambda _=False, item=template: self._default(item))
            delete.clicked.connect(lambda _=False, item=template: self._delete(item))
            layout.addWidget(label, 1)
            layout.addWidget(edit)
            layout.addWidget(copy)
            layout.addWidget(default)
            layout.addWidget(delete)
            self.box.addWidget(row)

    def _edit(self, template: ReportTemplate | None) -> None:
        dialog = TemplateEditDialog(self._theme, template, self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        name, content = dialog.result_values()
        if not name or not content.strip():
            QMessageBox.information(self, "提示", "名称和内容不能为空")
            return
        item = template or ReportTemplate(name=name, content=content)
        item.name = name
        item.content = content
        self._reports.save_template(item)
        self._reload()

    def _copy(self, template: ReportTemplate) -> None:
        copy = ReportTemplate(name=template.name + " 副本", content=template.content)
        self._reports.save_template(copy)
        self._reload()

    def _default(self, template: ReportTemplate) -> None:
        template.is_default = True
        self._reports.save_template(template)
        self._reload()

    def _delete(self, template: ReportTemplate) -> None:
        if template.id is None:
            return
        if QMessageBox.question(self, "删除模板", f"确认删除 {template.name}？") != QMessageBox.StandardButton.Yes:
            return
        self._reports.delete_template(template.id)
        self._reload()
