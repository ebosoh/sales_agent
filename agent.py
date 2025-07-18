

import sys
import sqlite3
import os
import threading
import time
import base64
from playwright.sync_api import sync_playwright
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QMessageBox,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QInputDialog,
)
from PyQt6.QtGui import QColor, QPixmap, QIcon
from PyQt6.QtCore import QObject, pyqtSignal, QThread

from database import create_connection, create_tables
from licensing import validate_key, generate_key
from gemini_processor import initialize_gemini, analyze_message_with_gemini, classify_message_type, find_matches_in_catalog

class Worker(QObject):
    """
    A worker thread for performing background tasks.
    """
    finished = pyqtSignal()
    status_update = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, monitor_function):
        super().__init__()
        self.monitor_function = monitor_function
        self.running = True

    def run(self):
        try:
            self.monitor_function(self)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

    def stop(self):
        self.running = False

class SalesAgentDashboard(QMainWindow):
    def __init__(self, user_phone_number):
        super().__init__()
        self.user_phone_number = user_phone_number
        self.setWindowTitle(
            f"Sales Agent (User: {self.user_phone_number}) powered by TechBrain"
        )
        self.setGeometry(100, 100, 1200, 800)

        self.conn = create_connection()
        create_tables(self.conn) # Ensure tables are created on startup
        self.gemini_model = initialize_gemini() # Initialize the AI model

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # --- Monitoring State ---
        self.monitoring_thread = None
        self.monitoring_worker = None
        self.is_monitoring = False
        self.animation_state = 0

        self.create_customer_replies_tab()
        self.create_match_tab()
        self.create_popular_tab()
        self.create_groups_tab()
        self.create_mulika_mwizi_tab()
        self.create_catalog_tab() # Add new tab

        self.load_groups()
        self.load_fraudulent_numbers()
        self.load_customer_replies()
        self.load_popular_products()
        self.load_catalog() # Load data for new tab

    def create_customer_replies_tab(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Customer Replies")
        layout = QVBoxLayout(tab)

        # The input box is no longer needed.
        info_label = QLabel(f"Showing replies to posts made by: {self.user_phone_number}")
        layout.addWidget(info_label)

        self.customer_replies_table = QTableWidget()
        self.customer_replies_table.setColumnCount(10)
        self.customer_replies_table.setHorizontalHeaderLabels(
            [
                "Date and Time",
                "Phone number of replier (seller)",
                "Risk profile",
                "Product",
                "Make",
                "Type",
                "Year",
                "Picture",
                "Price (Kenya Shillings)",
                "Reply Text",
            ]
        )
        self.customer_replies_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.customer_replies_table)

        refresh_button = QPushButton("Refresh Replies")
        refresh_button.clicked.connect(self.load_customer_replies)
        layout.addWidget(refresh_button)

    def create_match_tab(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Match")
        layout = QVBoxLayout(tab)

        self.match_table = QTableWidget()
        self.match_table.setColumnCount(7) # Buyer Request + 6 catalog columns
        self.match_table.setHorizontalHeaderLabels(["Buyer Request", "Matched Product", "Make", "Type", "Year", "Price (KSh)", "Other Details"])
        self.match_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.match_table)

        find_matches_button = QPushButton("Find All Matches")
        find_matches_button.clicked.connect(self.find_and_display_matches)
        layout.addWidget(find_matches_button)

    def create_popular_tab(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Popular")
        layout = QVBoxLayout(tab)

        self.popular_products_table = QTableWidget()
        self.popular_products_table.setColumnCount(6)
        self.popular_products_table.setHorizontalHeaderLabels(
            [
                "Product",
                "Make",
                "Type",
                "Year",
                "Picture",
                "Other details",
            ]
        )
        self.popular_products_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.popular_products_table)

        refresh_button = QPushButton("Refresh Data")
        refresh_button.clicked.connect(self.load_popular_products)
        layout.addWidget(refresh_button)

    def create_groups_tab(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Groups")
        layout = QVBoxLayout(tab)

        self.group_input = QLineEdit()
        self.group_input.setPlaceholderText("Enter group name to monitor")
        layout.addWidget(self.group_input)

        self.add_group_button = QPushButton("Add Group")
        self.add_group_button.clicked.connect(self.add_group)
        layout.addWidget(self.add_group_button)

        self.monitored_groups_list = QListWidget()
        layout.addWidget(self.monitored_groups_list)

        self.remove_group_button = QPushButton("Remove Selected Group")
        self.remove_group_button.clicked.connect(self.remove_group)
        layout.addWidget(self.remove_group_button)

        self.monitoring_toggle_button = QPushButton("Start Monitoring")
        self.monitoring_toggle_button.clicked.connect(self.toggle_monitoring)
        layout.addWidget(self.monitoring_toggle_button)

        self.monitoring_status_label = QLabel("Status: Inactive")
        self.monitoring_status_label.setStyleSheet("color: grey;")
        layout.addWidget(self.monitoring_status_label)

    def create_mulika_mwizi_tab(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Mulika Mwizi")
        layout = QVBoxLayout(tab)

        self.fraud_number_input = QLineEdit()
        self.fraud_number_input.setPlaceholderText("Enter fraudulent phone number")
        layout.addWidget(self.fraud_number_input)

        self.fraud_reason_input = QTextEdit()
        self.fraud_reason_input.setPlaceholderText("Reason for reporting")
        layout.addWidget(self.fraud_reason_input)

        self.report_fraud_button = QPushButton("Report Number")
        self.report_fraud_button.clicked.connect(self.report_fraudulent_number)
        layout.addWidget(self.report_fraud_button)

        self.fraudulent_numbers_list = QListWidget()
        layout.addWidget(self.fraudulent_numbers_list)

    def create_catalog_tab(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Seller Catalog")
        layout = QVBoxLayout(tab)

        # Form for adding new products
        self.product_input = QLineEdit()
        self.product_input.setPlaceholderText("Product Name (e.g., Bumper)")
        self.make_input = QLineEdit()
        self.make_input.setPlaceholderText("Make (e.g., Toyota)")
        self.type_input = QLineEdit()
        self.type_input.setPlaceholderText("Type (e.g., Harrier)")
        self.year_input = QLineEdit()
        self.year_input.setPlaceholderText("Year")
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Price (KSh)")
        self.details_input = QLineEdit()
        self.details_input.setPlaceholderText("Other Details")
        
        add_product_button = QPushButton("Add Product to Catalog")
        add_product_button.clicked.connect(self.add_product_to_catalog)

        layout.addWidget(self.product_input)
        layout.addWidget(self.make_input)
        layout.addWidget(self.type_input)
        layout.addWidget(self.year_input)
        layout.addWidget(self.price_input)
        layout.addWidget(self.details_input)
        layout.addWidget(add_product_button)

        # Table to display catalog
        self.catalog_table = QTableWidget()
        self.catalog_table.setColumnCount(6)
        self.catalog_table.setHorizontalHeaderLabels(["Product", "Make", "Type", "Year", "Price (KSh)", "Other Details"])
        self.catalog_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.catalog_table)

    def load_catalog(self):
        print("Loading Seller Catalog...")
        try:
            self.catalog_table.setRowCount(0)
            cursor = self.conn.cursor()
            cursor.execute("SELECT product, make, type, year, price_ksh, other_details FROM seller_catalog")
            items = cursor.fetchall()

            self.catalog_table.setRowCount(len(items))
            for i, item in enumerate(items):
                self.catalog_table.setItem(i, 0, QTableWidgetItem(item[0]))
                self.catalog_table.setItem(i, 1, QTableWidgetItem(item[1]))
                self.catalog_table.setItem(i, 2, QTableWidgetItem(item[2]))
                self.catalog_table.setItem(i, 3, QTableWidgetItem(item[3]))
                self.catalog_table.setItem(i, 4, QTableWidgetItem(str(item[4])))
                self.catalog_table.setItem(i, 5, QTableWidgetItem(item[5]))
            print(f"Loaded {len(items)} items into Seller Catalog tab.")
        except Exception as e:
            print(f"Error loading seller catalog: {e}")

    def add_product_to_catalog(self):
        product = self.product_input.text()
        make = self.make_input.text()
        ptype = self.type_input.text()
        year = self.year_input.text()
        price = self.price_input.text()
        details = self.details_input.text()

        if not product or not price:
            QMessageBox.warning(self, "Input Error", "Product Name and Price are required.")
            return

        try:
            price_int = int(price)
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO seller_catalog (product, make, type, year, price_ksh, other_details)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (product, make, ptype, year, price_int, details))
            self.conn.commit()
            
            # Clear inputs and refresh table
            self.product_input.clear()
            self.make_input.clear()
            self.type_input.clear()
            self.year_input.clear()
            self.price_input.clear()
            self.details_input.clear()
            self.load_catalog()
            print(f"Added '{product}' to catalog.")

        except ValueError:
            QMessageBox.warning(self, "Input Error", "Price must be a valid number.")
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")

    def load_groups(self):
        try:
            c = self.conn.cursor()
            c.execute("SELECT name FROM groups")
            groups = c.fetchall()
            for group in groups:
                self.monitored_groups_list.addItem(group[0])
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")

    def add_group(self):
        group_name = self.group_input.text()
        if group_name:
            try:
                c = self.conn.cursor()
                c.execute("INSERT INTO groups (name) VALUES (?)", (group_name,))
                self.conn.commit()
                self.monitored_groups_list.addItem(group_name)
                self.group_input.clear()
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Duplicate Group", "This group is already being monitored.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
        else:
            QMessageBox.warning(self, "Input Error", "Please enter a group name.")

    def remove_group(self):
        selected_item = self.monitored_groups_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Selection Error", "Please select a group to remove.")
            return

        group_name = selected_item.text()
        confirm = QMessageBox.question(self, "Confirm Deletion", f"Are you sure you want to remove the group '{group_name}'?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if confirm == QMessageBox.StandardButton.Yes:
            try:
                c = self.conn.cursor()
                c.execute("DELETE FROM groups WHERE name = ?", (group_name,))
                self.conn.commit()
                self.monitored_groups_list.takeItem(self.monitored_groups_list.row(selected_item))
                QMessageBox.information(self, "Success", f"Group '{group_name}' has been removed.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"An error occurred while removing the group: {e}")

    def load_fraudulent_numbers(self):
        try:
            c = self.conn.cursor()
            c.execute("SELECT phone_number, reason FROM fraudulent_numbers")
            numbers = c.fetchall()
            for number in numbers:
                self.fraudulent_numbers_list.addItem(f"{number[0]} - {number[1]}")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")

    def report_fraudulent_number(self):
        phone_number = self.fraud_number_input.text()
        reason = self.fraud_reason_input.toPlainText()
        if phone_number and reason:
            try:
                c = self.conn.cursor()
                c.execute("INSERT INTO fraudulent_numbers (phone_number, reason) VALUES (?, ?)", (phone_number, reason))
                self.conn.commit()
                self.fraudulent_numbers_list.addItem(f"{phone_number} - {reason}")
                self.fraud_number_input.clear()
                self.fraud_reason_input.clear()
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Duplicate Number", "This number has already been reported.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
        else:
            QMessageBox.warning(self, "Input Error", "Please enter both a phone number and a reason.")

    def toggle_monitoring(self):
        if self.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()

    def start_monitoring(self):
        if self.monitored_groups_list.count() == 0:
            QMessageBox.warning(self, "No Groups", "Please add at least one group to monitor.")
            return

        self.is_monitoring = True
        self.monitoring_toggle_button.setText("Stop Monitoring")
        self.monitoring_status_label.setText("Status: Starting...")
        self.monitoring_status_label.setStyleSheet("color: orange;")

        self.monitoring_thread = QThread()
        self.monitoring_worker = Worker(self.monitor_groups)
        self.monitoring_worker.moveToThread(self.monitoring_thread)

        self.monitoring_thread.started.connect(self.monitoring_worker.run)
        self.monitoring_worker.finished.connect(self.on_monitoring_finished)
        self.monitoring_worker.status_update.connect(self.update_monitoring_status)
        self.monitoring_worker.error.connect(self.on_monitoring_error)

        self.monitoring_thread.start()

    def stop_monitoring(self):
        if self.monitoring_worker:
            self.monitoring_worker.stop()
        self.monitoring_toggle_button.setEnabled(False)
        self.monitoring_status_label.setText("Status: Stopping...")

    def on_monitoring_finished(self):
        self.is_monitoring = False
        self.monitoring_thread.quit()
        self.monitoring_thread.wait()
        self.monitoring_thread = None
        self.monitoring_worker = None
        
        self.monitoring_toggle_button.setText("Start Monitoring")
        self.monitoring_toggle_button.setEnabled(True)
        self.monitoring_status_label.setText("Status: Inactive")
        self.monitoring_status_label.setStyleSheet("color: grey;")

    def on_monitoring_error(self, error_message):
        QMessageBox.critical(self, "Monitoring Error", f"An error occurred in the monitoring thread:\n{error_message}")
        self.stop_monitoring()

    def update_monitoring_status(self, status):
        dots = "." * (self.animation_state + 1)
        self.animation_state = (self.animation_state + 1) % 3
        self.monitoring_status_label.setText(f"Status: {status}{dots}")
        self.monitoring_status_label.setStyleSheet("color: green;")

    def monitor_groups(self, worker):
        conn = create_connection()
        if not conn:
            worker.error.emit("Could not create a database connection in the monitoring thread.")
            return

        with sync_playwright() as p:
            try:
                browser = p.chromium.connect_over_cdp("http://localhost:9223")
                context = browser.contexts[0]
                page = context.pages[0]
                worker.status_update.emit("Connected to browser")

                while worker.running:
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM groups")
                    groups = [row[0] for row in cursor.fetchall()]
                    
                    if not groups:
                        worker.status_update.emit("No groups to monitor. Waiting...")
                        time.sleep(30)
                        continue

                    for group_name in groups:
                        if not worker.running:
                            break
                        
                        try:
                            # Navigate to the group
                            worker.status_update.emit(f"Navigating to '{group_name}'")
                            
                            # 1. Wait for the main chat list to be ready
                            chat_list_selector = 'div[data-testid="chat-list"]'
                            page.wait_for_selector(chat_list_selector, timeout=30000)

                            # 2. Use a more robust selector for the search box and fill it
                            search_box_selector = 'div[data-testid="chat-list-search"]'
                            page.wait_for_selector(search_box_selector, timeout=30000)
                            page.locator(search_box_selector).fill(group_name)
                            time.sleep(2) # Wait for search results to populate

                            # 3. Click the correct chat from the results
                            chat_selector = f'span[title="{group_name}"]'
                            page.wait_for_selector(chat_selector, timeout=10000)
                            page.locator(chat_selector).first.click()
                            
                            worker.status_update.emit(f"Scraping '{group_name}'")
                            time.sleep(5) # Wait for messages to load
                            self.scrape_and_save_messages(page, conn)

                        except Exception as nav_exc:
                            print(f"Could not navigate to or scrape group {group_name}: {nav_exc}")
                            worker.status_update.emit(f"Failed to load '{group_name}'")
                        
                        if not worker.running:
                            break
                        time.sleep(10) # Wait between groups

                    if worker.running:
                        worker.status_update.emit("Cycle complete. Waiting...")
                        time.sleep(60) # Wait a minute before the next full cycle

            except Exception as e:
                print(f"An error occurred during monitoring: {e}")
                worker.error.emit(str(e))
            finally:
                conn.close()
                print("Database connection for monitoring thread closed.")

    def scrape_and_save_messages(self, page, db_connection):
        print("Scraping active chat...")
        try:
            chat_panel_selector = '#app > div > div.x78zum5.xdt5ytf.x5yr21d > div > div.x9f619.x1n2onr6.xyw6214.x5yr21d.x6ikm8r.x10wlt62.x17dzmu4.x1i1dayz.x2ipvbc.x1w8yi2h.xyyilfv.x1iyjqo2.xpilrb4.x1t7ytsu.x1m2ixmg'
            page.wait_for_selector(chat_panel_selector, timeout=5000)

            message_selector = '#main > div.x1n2onr6.x1vjfegm.x1cqoux5.x14yy4lh > div > div.x10l6tqk.x13vifvy.x1o0tod.xyw6214.x9f619.x78zum5.xdt5ytf.xh8yej3.x5yr21d.x6ikm8r.x1rife3k.xjbqb8w.x1ewm37j > div.x3psx0u.xwib8y2.x1c1uobl.xrmvbpv.xh8yej3.xquzyny.xvc5jky.x11t971q > div'
            page.wait_for_selector(message_selector, timeout=5000)
            
            messages = page.query_selector_all(message_selector)
            
            if not messages:
                return

            # Get the active group name from the header
            group_header_selector = 'header [role="button"] span[dir="auto"]'
            group_name = page.locator(group_header_selector).inner_text()
            print(f"Scraping messages from group: {group_name}")

            cursor = db_connection.cursor()
            for msg_element in messages:
                text_element = msg_element.query_selector('span.selectable-text')
                meta_element = msg_element.query_selector('div[data-pre-plain-text]')
                img_element = msg_element.query_selector('img')
                
                # New logic to detect replies
                replied_to_element = msg_element.query_selector('[aria-label="Quoted message"]')
                is_reply = 1 if replied_to_element else 0
                replied_to_text = None
                replied_to_sender = None

                if is_reply:
                    try:
                        # The sender is the first span, the text is the second
                        reply_spans = replied_to_element.query_selector_all('span')
                        if len(reply_spans) > 1:
                            replied_to_sender = reply_spans[0].inner_text()
                            replied_to_text = reply_spans[1].inner_text()
                    except Exception as e:
                        print(f"Could not parse a reply element: {e}")

                picture_data = None
                if img_element:
                    try:
                        src = img_element.get_attribute('src')
                        if src and src.startswith('blob:'):
                            script = """
                                async (src) => {
                                    const response = await fetch(src);
                                    const blob = await response.blob();
                                    const reader = new FileReader();
                                    return new Promise(resolve => {
                                        reader.onload = () => resolve(reader.result);
                                        reader.readAsDataURL(blob);
                                    });
                                }
                            """
                            data_url = page.evaluate(script, src)
                            picture_data = base64.b64decode(data_url.split(',')[1])
                    except Exception as e:
                        print(f"Could not extract image data: {e}")

                if text_element and meta_element:
                    message_text = text_element.inner_text().strip()
                    meta_text = meta_element.get_attribute('data-pre-plain-text').strip()
                    
                    timestamp = meta_text.split(']')[0][1:]
                    sender = meta_text.split(']')[1].split(':')[0].strip()

                    cursor.execute("""
                        INSERT OR IGNORE INTO messages (group_name, sender, message_text, timestamp, picture_blob, is_reply, replied_to_text, replied_to_sender)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (group_name, sender, message_text, timestamp, picture_data, is_reply, replied_to_text, replied_to_sender))
            
            db_connection.commit()
            print(f"Finished scraping. {len(messages)} messages processed.")

        except Exception as e:
            print(f"Could not scrape messages: {e}")

    def load_customer_replies(self):
        buyer_identifier = self.user_phone_number
        print(f"Refreshing replies for user: '{buyer_identifier}'...")
        if not self.gemini_model:
            QMessageBox.critical(self, "AI Error", "Gemini model not initialized.")
            return

        try:
            self.customer_replies_table.setRowCount(0)
            cursor = self.conn.cursor()
            
            # The query now uses the stored number, with LIKE to be flexible
            cursor.execute("""
                SELECT timestamp, sender, message_text 
                FROM messages 
                WHERE is_reply = 1 AND replied_to_sender LIKE ?
                ORDER BY timestamp DESC
            """, (f'%{buyer_identifier}%',))
            messages = cursor.fetchall()

            self.customer_replies_table.setRowCount(len(messages))
            for i, msg in enumerate(messages):
                timestamp, sender, text = msg
                
                processed_data = analyze_message_with_gemini(self.gemini_model, text)
                
                self.customer_replies_table.setItem(i, 0, QTableWidgetItem(timestamp))
                self.customer_replies_table.setItem(i, 1, QTableWidgetItem(sender))
                
                risk_item = QTableWidgetItem("Unknown")
                risk_item.setBackground(QColor("yellow"))
                self.customer_replies_table.setItem(i, 2, risk_item)

                if processed_data:
                    self.customer_replies_table.setItem(i, 3, QTableWidgetItem(str(processed_data.get('product', 'N/A'))))
                    self.customer_replies_table.setItem(i, 4, QTableWidgetItem(str(processed_data.get('make', 'N/A'))))
                    self.customer_replies_table.setItem(i, 5, QTableWidgetItem(str(processed_data.get('type', 'N/A'))))
                    self.customer_replies_table.setItem(i, 6, QTableWidgetItem(str(processed_data.get('year', 'N/A'))))
                    
                    picture_blob = self.get_picture_for_message(timestamp, sender, text)
                    if picture_blob:
                        pixmap = QPixmap()
                        pixmap.loadFromData(picture_blob)
                        icon = QIcon(pixmap)
                        self.customer_replies_table.setItem(i, 7, QTableWidgetItem(icon, ""))

                    self.customer_replies_table.setItem(i, 8, QTableWidgetItem(str(processed_data.get('price_ksh', 0))))
                    self.customer_replies_table.setItem(i, 9, QTableWidgetItem(text)) # Show the actual reply text
                else:
                    self.customer_replies_table.setItem(i, 9, QTableWidgetItem(f"[AI FAILED] {text}"))

            print(f"Loaded {len(messages)} replies to '{buyer_identifier}'.")
        except Exception as e:
            print(f"Error loading customer replies: {e}")

    def get_picture_for_message(self, timestamp, sender, text):
        """Helper function to retrieve a picture blob for a specific message."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT picture_blob FROM messages 
                WHERE timestamp=? AND sender=? AND message_text=?
            """, (timestamp, sender, text))
            result = cursor.fetchone()
            return result[0] if result and result[0] else None
        except Exception as e:
            print(f"Error fetching picture from DB: {e}")
            return None

    def load_popular_products(self):
        print("Refreshing Popular Products tab with AI Analysis...")
        if not self.gemini_model:
            QMessageBox.critical(self, "AI Error", "Gemini model not initialized. Check your API key.")
            return
            
        try:
            self.popular_products_table.setRowCount(0)
            cursor = self.conn.cursor()
            cursor.execute("SELECT timestamp, sender, message_text FROM messages ORDER BY timestamp DESC LIMIT 50")
            messages = cursor.fetchall()

            self.popular_products_table.setRowCount(len(messages))
            for i, msg in enumerate(messages):
                timestamp, sender, text = msg
                
                processed_data = analyze_message_with_gemini(self.gemini_model, text)

                if processed_data:
                    self.popular_products_table.setItem(i, 0, QTableWidgetItem(str(processed_data.get('product', 'N/A'))))
                    self.popular_products_table.setItem(i, 1, QTableWidgetItem(str(processed_data.get('make', 'N/A'))))
                    self.popular_products_table.setItem(i, 2, QTableWidgetItem(str(processed_data.get('type', 'N/A'))))
                    self.popular_products_table.setItem(i, 3, QTableWidgetItem(str(processed_data.get('year', 'N/A'))))
                    
                    picture_blob = self.get_picture_for_message(timestamp, sender, text)
                    if picture_blob:
                        pixmap = QPixmap()
                        pixmap.loadFromData(picture_blob)
                        icon = QIcon(pixmap)
                        self.popular_products_table.setItem(i, 4, QTableWidgetItem(icon, ""))

                    self.popular_products_table.setItem(i, 5, QTableWidgetItem(str(processed_data.get('other_details', 'N/A'))))
                else:
                    # Optional: You might want to fill the row with placeholder text if AI fails
                    self.popular_products_table.setItem(i, 0, QTableWidgetItem("[AI FAILED]"))
                    self.popular_products_table.setItem(i, 1, QTableWidgetItem("N/A"))
                    self.popular_products_table.setItem(i, 2, QTableWidgetItem("N/A"))
                    self.popular_products_table.setItem(i, 3, QTableWidgetItem("N/A"))
                    self.popular_products_table.setItem(i, 4, QTableWidgetItem("N/A"))
                    self.popular_products_table.setItem(i, 5, QTableWidgetItem(text))


            print(f"Loaded and processed {len(messages)} messages into Popular Products tab.")
        except Exception as e:
            print(f"Error loading popular products: {e}")

    def find_and_display_matches(self):
        print("Finding and displaying matches...")
        if not self.gemini_model:
            QMessageBox.critical(self, "AI Error", "Gemini model not initialized.")
            return

        try:
            self.match_table.setRowCount(0)
            cursor = self.conn.cursor()

            # 1. Get all catalog items
            cursor.execute("SELECT id, product, make, type, year, price_ksh, other_details FROM seller_catalog")
            catalog_items_raw = cursor.fetchall()
            catalog_items = [dict(zip([c[0] for c in cursor.description], row)) for row in catalog_items_raw]

            if not catalog_items:
                QMessageBox.information(self, "No Catalog", "The seller catalog is empty. Please add items to find matches.")
                return

            # 2. Get all messages and classify them
            cursor.execute("SELECT message_text FROM messages")
            all_messages = cursor.fetchall()
            
            all_matches = []
            for msg_tuple in all_messages:
                message_text = msg_tuple[0]
                if classify_message_type(self.gemini_model, message_text) == "BUYING_REQUEST":
                    # 3. For each buying request, find matches
                    matches = find_matches_in_catalog(self.gemini_model, message_text, catalog_items)
                    if matches:
                        for match in matches:
                            # Add the original request to the match data for display
                            match['buyer_request'] = message_text
                            all_matches.append(match)
            
            # 4. Display the results
            self.match_table.setRowCount(len(all_matches))
            for i, match in enumerate(all_matches):
                self.match_table.setItem(i, 0, QTableWidgetItem(match['buyer_request']))
                self.match_table.setItem(i, 1, QTableWidgetItem(match.get('product')))
                self.match_table.setItem(i, 2, QTableWidgetItem(match.get('make')))
                self.match_table.setItem(i, 3, QTableWidgetItem(match.get('type')))
                self.match_table.setItem(i, 4, QTableWidgetItem(str(match.get('year'))))
                self.match_table.setItem(i, 5, QTableWidgetItem(str(match.get('price_ksh'))))
                self.match_table.setItem(i, 6, QTableWidgetItem(match.get('other_details')))

            print(f"Displayed {len(all_matches)} matches.")
            QMessageBox.information(self, "Matching Complete", f"Found and displayed {len(all_matches)} matches.")

        except Exception as e:
            print(f"Error during matching process: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred during the matching process: {e}")


    def closeEvent(self, event):
        if self.is_monitoring:
            self.stop_monitoring()
            # Give the thread a moment to stop
            if self.monitoring_thread and self.monitoring_thread.isRunning():
                self.monitoring_thread.wait(1000) # Wait up to 1 second
        if self.conn:
            self.conn.close()
        event.accept()

def check_license():
    license_file = "license.key"
    if os.path.exists(license_file):
        with open(license_file, "r") as f:
            try:
                username, key, phone_number = f.read().splitlines()
                if validate_key(username, key):
                    return True, phone_number # Return phone number on success
                else:
                    os.remove(license_file)
                    return False, None
            except ValueError: # Handles case where file is malformed
                os.remove(license_file)
                return False, None
    return False, None

def get_license():
    username, ok = QInputDialog.getText(None, "License", "Enter your username:")
    if not ok or not username: return False, None

    key, ok = QInputDialog.getText(None, "License", "Enter your 10-digit license key:")
    if not ok or not key: return False, None

    phone_number, ok = QInputDialog.getText(None, "Setup", "Enter your full WhatsApp Phone Number (e.g., +254712345678):")
    if not ok or not phone_number: return False, None

    username = username.strip()
    key = key.strip()
    phone_number = phone_number.strip()

    if validate_key(username, key):
        with open("license.key", "w") as f:
            f.write(f"{username}\n{key}\n{phone_number}")
        return True, phone_number
    else:
        QMessageBox.critical(None, "License Error", "Invalid license key.")
        return False, None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    is_licensed, phone_number = check_license()
    if not is_licensed:
        is_licensed, phone_number = get_license()

    if is_licensed:
        dashboard = SalesAgentDashboard(phone_number) # Pass number to dashboard
        dashboard.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)
