from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Input, Label, Static, Switch

from bagels.components.autocomplete import AutoComplete, Dropdown, DropdownItem
from bagels.forms.form import Form, FormField
from bagels.utils.format import parse_formula_expression

_RESTRICT_TYPES = {
    "any": None,
    "integer": r"^-?\d+$",
    "number": r"^-?\d*\.?\d*(?:[+\-*\/]-?\d*\.?\d+)*[+\-*\/\.]?$",
}


class Fields(Static):
    """Container for multiple form fields"""

    def __init__(self, fields: Form):  # should rename, but whatever
        super().__init__()
        self.form = fields

    def compose(self) -> ComposeResult:
        for field in self.form.fields:
            yield Field(field)


class Field(Static):
    """Individual form field that can be text, number, boolean, or autocomplete"""

    BINDINGS = [
        Binding("tab", "focus_next", "Focus next", False),
        Binding("shift+tab", "focus_prev", "Focus previous", False),
    ]

    def __init__(self, field: FormField):
        super().__init__()
        self.field = field

        # Create base input widget
        self.input = Input(placeholder=field.placeholder or "", id=f"field-{field.key}")

        # Configure input based on field type
        match self.field.type:
            case "hidden":
                pass
            case "integer" | "number":
                self.input.restrict = _RESTRICT_TYPES.get(self.field.type, None)
                self.input.value = field.default_value or ""

            case "autocomplete":
                self.input.heldValue = field.default_value or ""
                self.input.value = field.default_value_text or field.default_value or ""

            case type_ if type_ != "boolean":
                self.input.value = field.default_value or ""

    def on_auto_complete_selected(self, event: AutoComplete.Selected) -> None:
        """Handle autocomplete selection"""
        # self.screen.focus_next()

        # Find matching option and set held value
        for item in self.field.options.items:
            item_text = str(item.text or item.value)
            selected_dropdown_text = str(event.item.main)
            if item_text == selected_dropdown_text:
                self.input.heldValue = item.value
                break

    def on_input_changed(self, event: Input.Changed):
        if self.field.type == "number":
            num_val = parse_formula_expression(event.value)
            self.query_one(".label").update(f"{self.field.title} - {num_val}")

    def action_focus_next(self):
        self.screen.focus_next()

    def action_focus_prev(self):
        self.screen.focus_previous()

    def compose(self) -> ComposeResult:
        if self.field.type == "hidden":
            # Hidden fields just need a static widget to hold the value
            self.input = Static(id=f"field-{self.field.key}", classes="hidden-field")
            self.input.value = self.input.heldValue = self.field.default_value
            yield self.input
            return

        # Visible fields get a container with label and input
        with Container(classes="field-row", id=f"row-field-{self.field.key}"):
            yield Label(f"{self.field.title}", classes="label")

            if self.field.type == "autocomplete":
                # Build dropdown items list
                dropdown_items = [
                    DropdownItem(
                        item.text or item.value,
                        item.prefix or "",
                        item.postfix or "",
                    )
                    for item in self.field.options.items
                ]
                dropdown = Dropdown(
                    items=dropdown_items,
                    show_on_focus=True,
                    id=f"dropdown-{self.field.key}",
                    create_option=self.field.create_action,
                    show_when_empty=self.field.autocomplete_selector,
                )

                yield AutoComplete(
                    self.input,
                    dropdown,
                    classes="field-autocomplete",
                    create_action=self.field.create_action,
                    backspace_clears=self.field.autocomplete_selector,
                )

            elif self.field.type == "boolean":
                with Container(classes="switch-group"):
                    yield Label(str(self.field.labels[0]), classes="left")
                    yield Switch(
                        id=f"field-{self.field.key}",
                        value=self.field.default_value or False,
                    )
                    yield Label(str(self.field.labels[1]), classes="right")

            else:
                yield self.input
