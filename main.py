import sys
import csv
from pathlib import Path

# Use of AI to get suggestion for workflow
# ChatGPT was used to help guide me on how to make a pretty UI
# ChatGPT was used to help guide me on how to use PySide6

from PySide6.QtCore import Qt, QRectF, QUrl
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtGui import QKeySequence
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QDoubleSpinBox,
    QComboBox,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QCompleter,
    QPushButton,
    QLabel,
    QFrame,
    QProgressBar,
    QSizePolicy,
    QScrollArea,
)

from predict import predict_delivery


# ============================================================
# ROUTE RISK CALCULATION
# ============================================================

def calculate_risk(
    distance,
    weather,
    traffic,
    time_of_day,
    experience
):
    score = 0
    reasons = []

    # Traffic
    if traffic == "High":
        score += 35
        reasons.append("High traffic")

    elif traffic == "Medium":
        score += 15
        reasons.append("Moderate traffic")

    # Weather
    if weather == "Snowy":
        score += 30
        reasons.append("Snowy weather")

    elif weather == "Rainy":
        score += 20
        reasons.append("Rainy weather")

    elif weather == "Foggy":
        score += 15
        reasons.append("Foggy weather")

    elif weather == "Windy":
        score += 10
        reasons.append("Windy weather")

    # Time of day
    if time_of_day == "Evening":
        score += 10
        reasons.append("Evening delivery")

    # Distance
    if distance >= 15:
        score += 10
        reasons.append("Long delivery distance")

    # Courier experience
    if experience < 2:
        score += 10
        reasons.append("Limited courier experience")

    # Risk level
    if score >= 60:
        risk = "HIGH"

    elif score >= 30:
        risk = "MEDIUM"

    else:
        risk = "LOW"

    return score, risk, reasons


# ============================================================
# EXPECTED RANGE BAR
# ============================================================

class RangeBar(QWidget):

    def __init__(self):
        super().__init__()

        self.lower = 0
        self.prediction = 0
        self.upper = 100

        self.setMinimumHeight(55)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

    def set_values(self, lower, prediction, upper):
        self.lower = lower
        self.prediction = prediction
        self.upper = upper
        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        left = 5
        right = width - 5
        line_y = 28

        # Background line
        painter.setPen(
            QPen(QColor("#273142"), 5)
        )

        painter.drawLine(
            left,
            line_y,
            right,
            line_y
        )

        # Calculate prediction position
        if self.upper > self.lower:
            ratio = (
                (self.prediction - self.lower)
                / (self.upper - self.lower)
            )

            ratio = max(0, min(1, ratio))

        else:
            ratio = 0.5

        prediction_x = (
            left +
            ratio * (right - left)
        )

        # Prediction line
        painter.setPen(
            QPen(QColor("#3198FF"), 5)
        )

        painter.drawLine(
            left,
            line_y,
            prediction_x,
            line_y
        )

        # Prediction marker
        painter.setBrush(
            QBrush(QColor("#3198FF"))
        )

        painter.setPen(
            QPen(QColor("#0E1624"), 3)
        )

        painter.drawEllipse(
            QRectF(
                prediction_x - 6,
                line_y - 6,
                12,
                12
            )
        )


# ============================================================
# ITEM SELECTION WINDOW
# ============================================================

class ItemSelectionDialog(QDialog):

    def __init__(self, parent, items):
        super().__init__(parent)

        self.parent_window = parent
        self.items = items
        self.item_lookup = {
            item["item"].strip().lower(): item
            for item in items
        }

        self.setWindowTitle("RouteRisk - Select Delivery Items")
        self.setMinimumSize(720, 600)
        self.resize(760, 650)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 25, 28, 25)
        layout.setSpacing(14)

        title = QLabel("SELECT DELIVERY ITEMS")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Search for the items being ordered. You can select multiple items."
        )
        subtitle.setObjectName("itemDialogSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "Search items (e.g. headphones, LEGO, chips)..."
        )
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumHeight(44)
        layout.addWidget(self.search)

        self.completer = QCompleter(
            [item["item"] for item in items],
            self
        )
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.search.setCompleter(self.completer)

        self.completer.activated.connect(self.add_from_selection)
        self.search.returnPressed.connect(self.add_from_enter)

        selected_header = QLabel("SELECTED ITEMS")
        selected_header.setObjectName("itemDialogHeader")
        layout.addWidget(selected_header)

        self.selected_list = QListWidget()
        self.selected_list.setObjectName("dialogSelectedItems")
        self.selected_list.setMinimumHeight(330)
        layout.addWidget(self.selected_list, 1)

        self.prep_summary = QLabel()
        self.prep_summary.setObjectName("prepSummary")
        self.prep_summary.setWordWrap(True)
        layout.addWidget(self.prep_summary)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        done_button = QPushButton("DONE")
        done_button.setObjectName("dialogDoneButton")
        done_button.setMinimumSize(120, 40)
        done_button.clicked.connect(self.accept)
        button_layout.addWidget(done_button)

        layout.addLayout(button_layout)

        self.refresh_selected_items()

    def add_from_selection(self, text):
        self.add_item(str(text).strip())

    def add_from_enter(self):
        text = self.search.text().strip()
        if not text:
            return

        item = self.item_lookup.get(text.lower())
        if item is not None:
            self.add_item(item["item"])

    def add_item(self, text):
        item = self.item_lookup.get(text.lower())
        if item is None:
            return

        self.parent_window.add_selected_item(item)
        self.search.clear()
        self.refresh_selected_items()

        # Keep the search box ready for the next item.
        self.search.setFocus()

    def refresh_selected_items(self):
        self.selected_list.clear()

        for index, item in enumerate(self.parent_window.selected_items):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(8, 5, 8, 5)
            row_layout.setSpacing(10)

            label = QLabel(
                f"{item['item']}   •   "
                f"{item['min_prep']:.0f}–{item['max_prep']:.0f} min"
            )
            label.setObjectName("dialogItemLabel")
            label.setWordWrap(True)
            row_layout.addWidget(label, 1)

            remove_button = QPushButton("×")
            remove_button.setObjectName("itemRemoveButton")
            remove_button.setFixedSize(34, 34)
            remove_button.setToolTip("Remove this item")
            remove_button.clicked.connect(
                lambda checked=False, i=index: self.remove_item(i)
            )
            row_layout.addWidget(remove_button)

            list_item = QListWidgetItem()
            list_item.setSizeHint(row.sizeHint())
            self.selected_list.addItem(list_item)
            self.selected_list.setItemWidget(list_item, row)

        preparation_time = self.parent_window.get_preparation_time()

        if preparation_time is None:
            self.prep_summary.setText(
                "No items selected yet."
            )
        else:
            self.prep_summary.setText(
                f"Preparation time used by model: {preparation_time:.0f} min "
                "(highest item preparation time)"
            )

    def remove_item(self, index):
        if 0 <= index < len(self.parent_window.selected_items):
            self.parent_window.selected_items.pop(index)
            self.parent_window.update_preparation_summary()
            self.parent_window.update_range_warning()
            self.refresh_selected_items()


# ============================================================
# ROUTERISK APPLICATION
# ============================================================

class RouteRisk(QMainWindow):

    def __init__(self):

        super().__init__()

        # Button click sound
        self.click_sound = QSoundEffect()

        self.click_sound.setSource(
            QUrl.fromLocalFile(
                "sounds/click.wav"
            )
        )

        self.click_sound.setVolume(0.25)

        self.setWindowTitle(
            "RouteRisk - The Last Mile Delivery Intelligence"
        )

        self.setMinimumSize(1200, 720)

        # ====================================================
        # CENTRAL WIDGET
        # ====================================================

        central_widget = QWidget()

        self.setCentralWidget(
            central_widget
        )

        main_layout = QVBoxLayout(
            central_widget
        )

        main_layout.setContentsMargins(
            30, 20, 30, 25
        )

        main_layout.setSpacing(20)

        # ====================================================
        # HEADER
        # ====================================================

        header_layout = QHBoxLayout()

        # Logo
        logo = QLabel("↔")

        logo.setFixedSize(38, 38)

        logo.setAlignment(
            Qt.AlignCenter
        )

        logo.setStyleSheet("""
            QLabel {
                background: qlineargradient(
                    x1:0,
                    y1:0,
                    x2:1,
                    y2:1,
                    stop:0 #2878F0,
                    stop:1 #13B9E8
                );

                color: white;
                border-radius: 10px;
                font-size: 22px;
                font-weight: bold;
            }
        """)

        # Title
        title_layout = QVBoxLayout()

        title_layout.setSpacing(1)

        title = QLabel("RouteRisk")

        title.setObjectName("appTitle")

        subtitle = QLabel(
            "The Last Mile Delivery Intelligence"
        )

        subtitle.setObjectName("subtitle")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        header_layout.addWidget(logo)
        header_layout.addSpacing(12)
        header_layout.addLayout(title_layout)

        header_layout.addStretch()

        main_layout.addLayout(header_layout)

        # ====================================================
        # CONTENT
        # ====================================================

        content_layout = QHBoxLayout()

        content_layout.setSpacing(22)

        main_layout.addLayout(
            content_layout
        )

        # ====================================================
        # TRAINING RANGE WARNING
        # ====================================================

        self.range_warning = QLabel("")

        self.range_warning.setAlignment(
            Qt.AlignCenter
        )

        self.range_warning.setWordWrap(True)

        self.range_warning.setObjectName(
            "rangeWarning"
        )

        main_layout.addWidget(
            self.range_warning
        )

        # ====================================================
        # LEFT CARD
        # ====================================================

        input_card = QFrame()

        input_card.setObjectName(
            "card"
        )

        input_layout = QVBoxLayout(
            input_card
        )

        input_layout.setContentsMargins(
            22, 20, 22, 22
        )

        input_layout.setSpacing(13)

        # Section title
        input_title = QLabel(
            "DELIVERY INFORMATION"
        )

        input_title.setObjectName(
            "sectionTitle"
        )

        input_layout.addWidget(
            input_title
        )

        # Form
        form_layout = QFormLayout()

        form_layout.setVerticalSpacing(11)

        form_layout.setHorizontalSpacing(15)

        # ----------------------------------------------------
        # Distance
        # ----------------------------------------------------

        self.distance_input = QDoubleSpinBox()

        self.distance_input.setRange(
            0,
            9999
        )

        self.distance_input.setDecimals(2)

        self.distance_input.setValue(
            10.0
        )

        form_layout.addRow(
            "⌖  Distance (km)",
            self.distance_input
        )

        # ----------------------------------------------------
        # Weather
        # ----------------------------------------------------

        self.weather_input = QComboBox()

        self.weather_input.addItems([
            "Clear",
            "Rainy",
            "Foggy",
            "Windy",
            "Snowy"
        ])

        form_layout.addRow(
            "☁  Weather",
            self.weather_input
        )

        # ----------------------------------------------------
        # Traffic
        # ----------------------------------------------------

        self.traffic_input = QComboBox()

        self.traffic_input.addItems([
            "Low",
            "Medium",
            "High"
        ])

        form_layout.addRow(
            "⇅  Traffic Level",
            self.traffic_input
        )

        # ----------------------------------------------------
        # Time
        # ----------------------------------------------------

        self.time_input = QComboBox()

        self.time_input.addItems([
            "Morning",
            "Afternoon",
            "Evening",
            "Night"
        ])

        form_layout.addRow(
            "◷  Time of Day",
            self.time_input
        )

        # ----------------------------------------------------
        # Vehicle
        # ----------------------------------------------------

        self.vehicle_input = QComboBox()

        self.vehicle_input.addItems([
            "Bike",
            "Scooter",
            "Car"
        ])

        form_layout.addRow(
            "▰  Vehicle Type",
            self.vehicle_input
        )

        # ----------------------------------------------------
        # Ordered Items
        # ----------------------------------------------------

        self.items = self.load_items_database()
        self.item_lookup = {
            item["item"].lower(): item
            for item in self.items
        }
        self.selected_items = []
        self.item_dialog = None

        item_container = QWidget()
        item_layout = QVBoxLayout(item_container)
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(7)

        self.select_items_button = QPushButton(
            "＋   SELECT ITEMS"
        )
        self.select_items_button.setObjectName("selectItemsButton")
        self.select_items_button.setMinimumHeight(43)
        self.select_items_button.clicked.connect(
            self.open_item_selector
        )
        item_layout.addWidget(self.select_items_button)

        self.selected_items_summary = QLabel(
            "No items selected"
        )
        self.selected_items_summary.setObjectName(
            "selectedItemsSummary"
        )
        self.selected_items_summary.setWordWrap(True)
        item_layout.addWidget(self.selected_items_summary)

        form_layout.addRow(
            "✣  Items Ordered",
            item_container
        )

        # ----------------------------------------------------
        # Experience
        # ----------------------------------------------------

        self.experience_input = QDoubleSpinBox()

        self.experience_input.setRange(
            0,
            9
        )

        self.experience_input.setDecimals(
            1
        )

        self.experience_input.setValue(
            5.0
        )

        form_layout.addRow(
            "♙  Courier Experience (years)",
            self.experience_input
        )

        # Warn when inputs are outside the training data range
        self.distance_input.valueChanged.connect(
            self.update_range_warning
        )

        self.experience_input.valueChanged.connect(
            self.update_range_warning
        )

        self.update_range_warning()

        input_layout.addLayout(
            form_layout
        )

        input_layout.addStretch()

        # ====================================================
        # PREDICT BUTTON
        # ====================================================

        self.predict_button = QPushButton(
            "▷   PREDICT DELIVERY TIME"
        )

        self.predict_button.setMinimumHeight(
            46
        )

        self.predict_button.clicked.connect(
            self.handle_predict_click
        )

        input_layout.addWidget(
            self.predict_button
        )

        content_layout.addWidget(
            input_card,
            1
        )

        # ====================================================
        # RIGHT CARD
        # ====================================================

        result_card = QFrame()

        result_card.setObjectName(
            "card"
        )

        result_layout = QVBoxLayout(
            result_card
        )

        result_layout.setContentsMargins(
            28, 20, 28, 25
        )

        result_layout.setSpacing(12)

        # ====================================================
        # PREDICTION TITLE
        # ====================================================

        prediction_title = QLabel(
            "DELIVERY PREDICTION"
        )

        prediction_title.setObjectName(
            "sectionTitle"
        )

        result_layout.addWidget(
            prediction_title
        )

        # ====================================================
        # PREDICTED TIME
        # ====================================================

        predicted_label = QLabel(
            "Predicted delivery time"
        )

        predicted_label.setObjectName(
            "smallLabel"
        )

        result_layout.addWidget(
            predicted_label
        )

        prediction_layout = QHBoxLayout()

        self.prediction_value = QLabel(
            "—"
        )

        self.prediction_value.setObjectName(
            "predictionValue"
        )

        prediction_layout.addWidget(
            self.prediction_value
        )

        self.minutes_label = QLabel(
            "min"
        )

        self.minutes_label.setObjectName(
            "minutesLabel"
        )

        prediction_layout.addWidget(
            self.minutes_label
        )

        prediction_layout.addStretch()

        result_layout.addLayout(
            prediction_layout
        )

        # ====================================================
        # RANGE LABELS
        # ====================================================

        range_labels = QHBoxLayout()

        self.lower_label = QLabel(
            "MIN"
        )

        self.lower_label.setObjectName(
            "rangeLabel"
        )

        self.upper_label = QLabel(
            "MAX"
        )

        self.upper_label.setObjectName(
            "rangeLabel"
        )

        range_labels.addWidget(
            self.lower_label
        )

        range_labels.addStretch()

        self.predicted_range_label = QLabel(
            "EXPECTED RANGE"
        )

        self.predicted_range_label.setObjectName(
            "rangeLabel"
        )

        range_labels.addWidget(
            self.predicted_range_label
        )

        range_labels.addStretch()

        range_labels.addWidget(
            self.upper_label
        )

        result_layout.addLayout(
            range_labels
        )

        # ====================================================
        # RANGE BAR
        # ====================================================

        self.range_bar = RangeBar()

        result_layout.addWidget(
            self.range_bar
        )

        # ====================================================
        # RANGE VALUES
        # ====================================================

        range_values = QHBoxLayout()

        self.lower_value = QLabel(
            "—"
        )

        self.lower_value.setObjectName(
            "rangeValue"
        )

        self.upper_value = QLabel(
            "—"
        )

        self.upper_value.setObjectName(
            "rangeValue"
        )

        range_values.addWidget(
            self.lower_value
        )

        range_values.addStretch()

        self.prediction_marker_label = QLabel(
            ""
        )

        self.prediction_marker_label.setObjectName(
            "predictionMarker"
        )

        range_values.addWidget(
            self.prediction_marker_label
        )

        range_values.addStretch()

        range_values.addWidget(
            self.upper_value
        )

        result_layout.addLayout(
            range_values
        )

        # ====================================================
        # DIVIDER
        # ====================================================

        divider = QFrame()

        divider.setFrameShape(
            QFrame.HLine
        )

        divider.setObjectName(
            "divider"
        )

        result_layout.addWidget(
            divider
        )

        # ====================================================
        # ROUTE RISK HEADER
        # ====================================================

        risk_header = QHBoxLayout()

        risk_title = QLabel(
            "ROUTE RISK"
        )

        risk_title.setObjectName(
            "sectionTitle"
        )

        risk_header.addWidget(
            risk_title
        )

        risk_header.addStretch()

        self.risk_badge = QLabel(
            "—"
        )

        self.risk_badge.setObjectName(
            "riskBadge"
        )

        self.risk_badge.setAlignment(
            Qt.AlignCenter
        )

        risk_header.addWidget(
            self.risk_badge
        )

        result_layout.addLayout(
            risk_header
        )

        # ====================================================
        # RISK SCORE
        # ====================================================

        risk_score_layout = QHBoxLayout()

        self.risk_score_label = QLabel(
            "0"
        )

        self.risk_score_label.setObjectName(
            "riskScore"
        )

        risk_score_layout.addWidget(
            self.risk_score_label
        )

        slash = QLabel(
            " / 100"
        )

        slash.setObjectName(
            "riskSlash"
        )

        risk_score_layout.addWidget(
            slash
        )

        risk_score_layout.addStretch()

        result_layout.addLayout(
            risk_score_layout
        )

        # ====================================================
        # RISK BAR
        # ====================================================

        self.risk_bar = QProgressBar()

        self.risk_bar.setRange(
            0,
            100
        )

        self.risk_bar.setValue(
            0
        )

        self.risk_bar.setTextVisible(
            False
        )

        self.risk_bar.setFixedHeight(
            7
        )

        self.risk_bar.setObjectName(
            "riskBar"
        )

        result_layout.addWidget(
            self.risk_bar
        )

        # ====================================================
        # RISK SCALE
        # ====================================================

        risk_scale = QHBoxLayout()

        low_label = QLabel("LOW")

        medium_label = QLabel("MED")

        high_label = QLabel("HIGH")

        for label in [
            low_label,
            medium_label,
            high_label
        ]:
            label.setObjectName(
                "riskScale"
            )

        risk_scale.addWidget(
            low_label
        )

        risk_scale.addStretch()

        risk_scale.addWidget(
            medium_label
        )

        risk_scale.addStretch()

        risk_scale.addWidget(
            high_label
        )

        risk_scale.addStretch()

        risk_scale.addWidget(
            QLabel("100")
        )

        result_layout.addLayout(
            risk_scale
        )

        # ====================================================
        # RISK FACTORS
        # ====================================================

        factors_title = QLabel(
            "RISK FACTORS"
        )

        factors_title.setObjectName(
            "sectionTitle"
        )

        result_layout.addWidget(
            factors_title
        )

        # Risk factors container
        risk_factors_widget = QWidget()

        self.risk_factors_layout = QVBoxLayout(
            risk_factors_widget
        )

        self.risk_factors_layout.setContentsMargins(
            0, 0, 8, 0
        )

        self.risk_factors_layout.setSpacing(
            7
        )

        # Scroll area for risk factors
        risk_factors_scroll = QScrollArea()

        risk_factors_scroll.setWidget(
            risk_factors_widget
        )

        risk_factors_scroll.setWidgetResizable(
            True
        )

        risk_factors_scroll.setFrameShape(
            QFrame.NoFrame
        )

        risk_factors_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        risk_factors_scroll.setMaximumHeight(
            180
        )

        result_layout.addWidget(
            risk_factors_scroll
        )

        result_layout.addStretch()

        content_layout.addWidget(
            result_card,
            3
        )

        # ====================================================
        # INITIAL RESULT
        # ====================================================

        self.update_results(
            prediction=0,
            lower=0,
            upper=0,
            score=0,
            risk="LOW",
            reasons=[]
        )

    # ========================================================
    # UPDATE RESULTS
    # ========================================================

    def update_results(
        self,
        prediction,
        lower,
        upper,
        score,
        risk,
        reasons
    ):

        # ----------------------------------------------------
        # Prediction
        # ----------------------------------------------------

        if prediction > 0:

            self.prediction_value.setText(
                f"{prediction:.1f}"
            )

            self.lower_value.setText(
                f"{lower:.1f}"
            )

            self.upper_value.setText(
                f"{upper:.1f}"
            )

            self.range_bar.set_values(
                lower,
                prediction,
                upper
            )

            self.prediction_marker_label.setText(
                f"{prediction:.1f} min"
            )

        else:

            self.prediction_value.setText(
                "—"
            )

            self.lower_value.setText(
                "—"
            )

            self.upper_value.setText(
                "—"
            )

            self.prediction_marker_label.setText(
                ""
            )

        # ----------------------------------------------------
        # Risk score
        # ----------------------------------------------------

        self.risk_score_label.setText(
            str(score)
        )

        self.risk_bar.setValue(
            score
        )

        # ----------------------------------------------------
        # Risk colours
        # ----------------------------------------------------

        if risk == "HIGH":

            risk_color = "#FF5C68"

            badge_background = "#351B20"

            border_color = "#71333B"

            bar_color = "#FF5C68"

        elif risk == "MEDIUM":

            risk_color = "#FFB31A"

            badge_background = "#332B18"

            border_color = "#66531F"

            bar_color = "#FFB31A"

        else:

            risk_color = "#31D48C"

            badge_background = "#123328"

            border_color = "#235B46"

            bar_color = "#31D48C"

        self.risk_score_label.setStyleSheet(
            f"""
            color: {risk_color};
            font-size: 34px;
            font-weight: bold;
            """
        )

        self.risk_badge.setText(
            risk
        )

        self.risk_badge.setStyleSheet(
            f"""
            QLabel {{
                color: {risk_color};
                background-color: {badge_background};
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: bold;
                letter-spacing: 2px;
            }}
            """
        )

        self.risk_bar.setStyleSheet(
            f"""
            QProgressBar {{
                background-color: #263E61;
                border: none;
                border-radius: 3px;
            }}

            QProgressBar::chunk {{
                background-color: {bar_color};
                border-radius: 3px;
            }}
            """
        )

        # ----------------------------------------------------
        # Risk factors
        # ----------------------------------------------------

        # Remove previous factors
        while self.risk_factors_layout.count():

            item = self.risk_factors_layout.takeAt(0)

            widget = item.widget()

            if widget:
                widget.deleteLater()

        if reasons:

            for reason in reasons:

                factor = QLabel(
                    f"⚠   {reason}"
                )

                factor.setObjectName(
                    "riskFactor"
                )

                factor.setStyleSheet(
                    f"""
                    QLabel {{
                        color: #D9DEE8;
                        background-color: #211F1A;
                        border: 1px solid #594A23;
                        border-radius: 7px;
                        padding: 10px 12px;
                    }}
                    """
                )

                self.risk_factors_layout.addWidget(
                    factor
                )

        else:

            factor = QLabel(
                "✓   No significant risk factors."
            )

            factor.setObjectName(
                "safeFactor"
            )

            factor.setStyleSheet(
                """
                QLabel {
                    color: #31D48C;
                    background-color: #102B23;
                    border: 1px solid #245640;
                    border-radius: 7px;
                    padding: 10px 12px;
                }
                """
            )

            self.risk_factors_layout.addWidget(
                factor
            )

    # ========================================================
    # ITEM DATABASE
    # ========================================================

    def load_items_database(self):

        database_path = Path(__file__).resolve().parent / "data" / "items_database.csv"

        if not database_path.exists():
            return []

        items = []

        try:
            with database_path.open("r", encoding="utf-8", newline="") as file:
                reader = csv.DictReader(file)

                for row in reader:
                    try:
                        min_prep = float(row["min_prep"])
                        max_prep = float(row["max_prep"])
                    except (ValueError, TypeError, KeyError):
                        continue

                    min_prep = max(0.0, min_prep)
                    max_prep = min(100.0, max(min_prep, max_prep))

                    items.append({
                        "item": row["item"].strip(),
                        "category": row.get("category", "").strip(),
                        "min_prep": min_prep,
                        "max_prep": max_prep
                    })

        except OSError:
            return []

        return items

    def open_item_selector(self):
        if self.item_dialog is None:
            self.item_dialog = ItemSelectionDialog(
                self,
                self.items
            )

        self.item_dialog.refresh_selected_items()
        self.item_dialog.search.clear()
        self.item_dialog.search.setFocus()
        self.item_dialog.exec()

        # Make sure the main window reflects the final selection.
        self.update_preparation_summary()
        self.update_range_warning()

    def add_selected_item(self, item):
        item_name = item["item"].strip().lower()

        # Prevent accidental duplicates.
        if any(
            selected["item"].strip().lower() == item_name
            for selected in self.selected_items
        ):
            return

        self.selected_items.append(item)
        self.update_preparation_summary()
        self.update_range_warning()

    def remove_selected_item(self, index):
        if 0 <= index < len(self.selected_items):
            self.selected_items.pop(index)
            self.update_preparation_summary()
            self.update_range_warning()

            if self.item_dialog is not None:
                self.item_dialog.refresh_selected_items()

    def clear_items(self):
        self.selected_items.clear()
        self.update_preparation_summary()
        self.update_range_warning()

        if self.item_dialog is not None:
            self.item_dialog.refresh_selected_items()

    def get_preparation_time(self):
        if not self.selected_items:
            return None

        # The longest-preparation item determines the order's preparation time.
        return min(
            100.0,
            max(item["max_prep"] for item in self.selected_items)
        )

    def update_preparation_summary(self):
        if not self.selected_items:
            self.selected_items_summary.setText(
                "No items selected — click SELECT ITEMS to add products."
            )
            return

        preparation_time = self.get_preparation_time()
        count = len(self.selected_items)
        noun = "item" if count == 1 else "items"

        self.selected_items_summary.setText(
            f"{count} {noun} selected  •  "
            f"Preparation time: {preparation_time:.0f} min"
        )

    # ========================================================
    # TRAINING RANGE WARNING
    # ========================================================

    def update_range_warning(self):

        warnings = []

        distance = self.distance_input.value()
        experience = self.experience_input.value()
        preparation_time = self.get_preparation_time()

        if distance < 0.59 or distance > 19.99:
            warnings.append(
                "Distance is outside the training range (0.59–19.99 km)"
            )

        if preparation_time is not None and (preparation_time < 5 or preparation_time > 29):
            warnings.append(
                "Item preparation time is outside the training range (5–29 min)"
            )

        if experience < 0 or experience > 9:
            warnings.append(
                "Courier experience is outside the training range (0–9 years)"
            )

        if warnings:
            self.range_warning.setText(
                "⚠  " + "  •  ".join(warnings)
                + "\nPredictions outside the training range may be less reliable."
            )
        else:
            self.range_warning.setText("")

    def handle_predict_click(self):
        self.click_sound.play()
        self.make_prediction()

    # ========================================================
    # MAKE PREDICTION
    # ========================================================

    def make_prediction(self):

        # ----------------------------------------------------
        # Show loading state
        # ----------------------------------------------------

        self.predict_button.setText(
            "⟳   ANALYZING ROUTE..."
        )

        self.predict_button.setEnabled(
            False
        )

        QApplication.processEvents()

        # ----------------------------------------------------
        # Get input values
        # ----------------------------------------------------

        distance = (
            self.distance_input.value()
        )

        preparation_time = self.get_preparation_time()

        if preparation_time is None:
            self.predict_button.setText(
                "▷   PREDICT DELIVERY TIME"
            )
            self.predict_button.setEnabled(True)
            self.range_warning.setText(
                "⚠  Add at least one item before predicting delivery time."
            )
            return

        preparation_time = min(100.0, max(0.0, preparation_time))

        experience = (
            self.experience_input.value()
        )

        weather = (
            self.weather_input.currentText()
        )

        traffic = (
            self.traffic_input.currentText()
        )

        time_of_day = (
            self.time_input.currentText()
        )

        vehicle = (
            self.vehicle_input.currentText()
        )

        # ----------------------------------------------------
        # ML prediction
        # ----------------------------------------------------

        prediction, lower, upper = (
            predict_delivery(
                distance=distance,
                weather=weather,
                traffic=traffic,
                time_of_day=time_of_day,
                vehicle=vehicle,
                preparation_time=preparation_time,
                experience=experience
            )
        )

        # ----------------------------------------------------
        # Risk calculation
        # ----------------------------------------------------

        score, risk, reasons = (
            calculate_risk(
                distance=distance,
                weather=weather,
                traffic=traffic,
                time_of_day=time_of_day,
                experience=experience
            )
        )

        # ----------------------------------------------------
        # Update UI
        # ----------------------------------------------------

        self.update_results(
            prediction=prediction,
            lower=lower,
            upper=upper,
            score=score,
            risk=risk,
            reasons=reasons
        )

        # ----------------------------------------------------
        # Restore button
        # ----------------------------------------------------

        self.predict_button.setText(
            "▷   PREDICT DELIVERY TIME"
        )

        self.predict_button.setEnabled(
            True
        )


# ============================================================
# APPLICATION STYLING
# ============================================================

app = QApplication(sys.argv)

app.setStyleSheet("""

    /* ======================================================
       GLOBAL
       ====================================================== */

    QMainWindow {
        background-color: #081326;
    }

    QWidget {
        color: #F4F8FF;
        font-family: "Segoe UI";
        font-size: 13px;
    }


    /* ======================================================
       HEADER
       ====================================================== */

    QLabel#appTitle {
        color: #FFFFFF;
        font-size: 21px;
        font-weight: bold;
    }

    QLabel#subtitle {
        color: #8FB8E8;
        font-size: 11px;
    }

    /* ======================================================
       CARDS
       ====================================================== */

    QFrame#card {
        background-color: #101D33;
        border: 1px solid #2D4770;
        border-radius: 14px;
    }


    /* ======================================================
       SECTION TITLES
       ====================================================== */

    QLabel#sectionTitle {
        color: #6FB7FF;
        font-size: 10px;
        font-weight: bold;
        letter-spacing: 2px;
        padding-bottom: 7px;
        border-bottom: 1px solid #294267;
    }

    QLabel#smallLabel {
        color: #8AA9CF;
        font-size: 12px;
        margin-top: 5px;
    }


    /* ======================================================
       FORM LABELS
       ====================================================== */

    QFormLayout QLabel {
        color: #9AC7F5;
        font-size: 12px;
    }


    /* ======================================================
       INPUTS
       ====================================================== */

    QDoubleSpinBox,
    QSpinBox,
    QComboBox {

        background-color: #14233D;

        color: #F7FBFF;

        border: 1px solid #35547F;

        border-radius: 7px;

        padding: 9px 11px;

        min-height: 19px;
    }


    QDoubleSpinBox:hover,
    QSpinBox:hover,
    QComboBox:hover {

        border: 1px solid #5B8FD0;
    }


    QDoubleSpinBox:focus,
    QSpinBox:focus,
    QComboBox:focus {

        border: 1px solid #59B5FF;

        background-color: #182B49;
    }


    QComboBox::drop-down {

        border: none;

        width: 30px;
    }


    QComboBox QAbstractItemView {

        background-color: #182B49;

        color: #F4F8FF;

        border: 1px solid #42648F;

        selection-background-color: #2678D9;
    }


    QPushButton#selectItemsButton {
        background-color: #162A49;
        color: #65C7FF;
        border: 1px solid #3C73A9;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 11px;
        font-weight: bold;
        letter-spacing: 1px;
    }

    QPushButton#selectItemsButton:hover {
        background-color: #1C3A63;
        border: 1px solid #59B5FF;
    }

    QLabel#selectedItemsSummary {
        color: #8FB8E8;
        background-color: #0E1A2E;
        border: 1px solid #29466F;
        border-radius: 7px;
        padding: 8px 9px;
        font-size: 10px;
    }

    QLabel#itemDialogSubtitle {
        color: #8AA9CF;
        font-size: 12px;
    }

    QLabel#itemDialogHeader {
        color: #6FB7FF;
        font-size: 10px;
        font-weight: bold;
        letter-spacing: 2px;
    }

    QListWidget#dialogSelectedItems {
        background-color: #0E1A2E;
        color: #EAF4FF;
        border: 1px solid #2D4770;
        border-radius: 9px;
        padding: 7px;
    }

    QLabel#dialogItemLabel {
        color: #EAF4FF;
        font-size: 12px;
    }

    QPushButton#itemRemoveButton {
        background-color: #2A2030;
        color: #FF7180;
        border: 1px solid #71333B;
        border-radius: 7px;
        font-size: 20px;
        font-weight: bold;
    }

    QPushButton#itemRemoveButton:hover {
        background-color: #4A2630;
        border: 1px solid #FF5C68;
    }

    QPushButton#dialogDoneButton {
        background: qlineargradient(
            x1: 0,
            y1: 0,
            x2: 1,
            y2: 0,
            stop: 0 #287CFF,
            stop: 1 #14D4E8
        );
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 11px;
        font-weight: bold;
        letter-spacing: 1px;
    }

    QLineEdit {
        background-color: #14233D;
        color: #F7FBFF;
        border: 1px solid #35547F;
        border-radius: 7px;
        padding: 9px 11px;
        min-height: 19px;
    }

    QLineEdit:hover,
    QLineEdit:focus {
        border: 1px solid #59B5FF;
        background-color: #182B49;
    }

    QListWidget#orderedItems {
        background-color: #0E1A2E;
        color: #EAF4FF;
        border: 1px solid #2D4770;
        border-radius: 7px;
        padding: 4px;
    }

    QListWidget#orderedItems::item {
        padding: 6px 7px;
        border-radius: 5px;
    }

    QListWidget#orderedItems::item:selected {
        background-color: #1E5AA5;
    }

    QLabel#formSectionLabel {
        color: #9AC7F5;
        font-size: 12px;
        margin-top: 2px;
    }

    QLabel#prepSummary {
        color: #58C7FF;
        background-color: #102844;
        border: 1px solid #24588A;
        border-radius: 6px;
        padding: 7px 9px;
        font-size: 10px;
    }

    QPushButton#secondaryButton {
        background-color: #14233D;
        color: #9FCBFF;
        border: 1px solid #35547F;
        border-radius: 6px;
        padding: 6px 8px;
        font-size: 9px;
        font-weight: bold;
    }

    QPushButton#secondaryButton:hover {
        background-color: #1A3152;
        border: 1px solid #59B5FF;
    }

    QCompleter QAbstractItemView {
        background-color: #14233D;
        color: #F7FBFF;
        border: 1px solid #3D6DA5;
        selection-background-color: #287CFF;
        padding: 4px;
    }

    /* ======================================================
       PREDICT BUTTON
       ====================================================== */

    QPushButton {

        background: qlineargradient(
            x1: 0,
            y1: 0,
            x2: 1,
            y2: 0,
            stop: 0 #287CFF,
            stop: 1 #14D4E8
        );

        color: white;

        border: none;

        border-radius: 8px;

        font-size: 12px;

        font-weight: bold;

        letter-spacing: 1px;
    }


    QPushButton:hover {

        background: qlineargradient(
            x1: 0,
            y1: 0,
            x2: 1,
            y2: 0,
            stop: 0 #4D9BFF,
            stop: 1 #36E3F2
        );
    }


    QPushButton:pressed {

        background-color: #2169D8;
    }


    QPushButton:disabled {

        background-color: #2D4261;

        color: #A3B7D1;
    }


    QLabel#rangeWarning {
        color: #FFD166;
        background-color: #302A18;
        border: 1px solid #7A6425;
        border-radius: 7px;
        padding: 7px 12px;
        font-size: 10px;
    }


    /* ======================================================
       PREDICTION
       ====================================================== */

    QLabel#predictionValue {

        color: #4DD7FF;

        font-size: 58px;

        font-weight: 300;
    }


    QLabel#minutesLabel {

        color: #9BBBE0;

        font-size: 14px;

        margin-top: 25px;
    }


    QLabel#rangeLabel {

        color: #7095C5;

        font-size: 9px;

        font-weight: bold;

        letter-spacing: 1px;
    }


    QLabel#rangeValue {

        color: #C4D6EE;

        font-size: 11px;
    }


    QLabel#predictionMarker {

        color: #5AC4FF;

        font-size: 10px;

        font-weight: bold;
    }


    /* ======================================================
       DIVIDER
       ====================================================== */

    QFrame#divider {

        color: #2B4264;

        background-color: #2B4264;

        max-height: 1px;
    }


    /* ======================================================
       RISK
       ====================================================== */

    QLabel#riskSlash {

        color: #536B8E;

        font-size: 18px;
    }


    QProgressBar#riskBar {

        background-color: #263E61;

        border: none;

        border-radius: 3px;
    }


    /* ======================================================
       RISK SCALE
       ====================================================== */

    QLabel#riskScale {

        color: #6585AD;

        font-size: 8px;

        font-weight: bold;
    }

""")


# ============================================================
# START APPLICATION
# ============================================================

window = RouteRisk()

window.show()

sys.exit(
    app.exec()
)