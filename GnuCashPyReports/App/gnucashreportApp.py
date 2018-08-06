import datetime
import logging
import win32api
from os.path import join, isdir

import sys
from googleapiclient.errors import HttpError
from kivy.app import App
from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.utils import platform
from oauth2client.clientsecrets import InvalidClientSecretsError

from GnuCashPyReports.functions import *
from GnuCashPyReports.reports.realisatie_report import *

MAX_TIME = 1 / 60

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('gnureportapp')
logger.setLevel(logging.DEBUG)


def get_drives():
    drives = win32api.GetLogicalDriveStrings()
    drives = drives.split('\000')[:-1]
    return drives

class MessagePopup(Popup):
    pass

class WarningPopup(FloatLayout):
    cancel = ObjectProperty(None)

    def __init__(self, message=None, **kwargs):
        super(WarningPopup, self).__init__(**kwargs)
        self.ids.warning_popup_text.text = message

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)

    def __init__(self, path=None, **kwargs):
        super(LoadDialog, self).__init__(**kwargs)
        self.drives_list.adapter.bind(on_selection_change=self.drive_selection_changed)
        if path and isdir(path):
            self.filechooser.path = path
        else:
            home = expanduser("~")
            drives = self.get_win_drives()
            if drives:
                self.filechooser.path = home

    def show_item(self, directory, filename):
        result = (self.is_dir(directory, filename) and not self.is_hidden_folder(directory, filename)) or (
            os.path.isfile(filename) and filename.split(".")[-1] == "gnucash")
        return result

    @staticmethod
    def is_dir(directory, filename):
        return isdir(join(directory, filename))

    @staticmethod
    def is_hidden_folder(directory, filename):
        first_of_last = join(directory, filename).split(os.sep)[-1][0]
        if first_of_last is ".":
            return True
        return False

    def get_quick_links(self):
        links = []
        home = expanduser("~")
        links.append(home)
        links += self.get_win_drives()
        return links

    @staticmethod
    def get_win_drives():
        if platform == 'win':
            drives = win32api.GetLogicalDriveStrings()
            drives = drives.split('\000')[:-1]
            return drives
        else:
            return []

    def drive_selection_changed(self, *args):
        selected_item = args[0].selection[0].text
        self.filechooser.path = selected_item

    def go_to_directory(self, path):
        if isdir(path):
            self.filechooser.path = path


class MainScreen(Screen):
    file = ObjectProperty(None)
    text_input = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.process_running = False

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_set_gnucash_file_path(self):
        path = None
        if self.ids.gnucash_file_path.text:
            if isdir(self.ids.gnucash_file_path.text):
                path = self.ids.gnucash_file_path.text
            else:
                path = os.path.dirname(self.ids.gnucash_file_path.text)
                print(path)

        content = LoadDialog(path=path, load=self.set_destination_path, cancel=self.dismiss_popup)
        self._popup = Popup(title="Select GnuCash File", content=content)
        self._popup.open()

    def set_destination_path(self, path, filename):
        self.ids.gnucash_file_path.text = filename[0]
        self.dismiss_popup()

    def make_report(self):
        accounts = self.ids.gnucash_accounts.text
        try:
            date1 = datetime.datetime.strptime(self.ids.start_date.text, "%Y-%m-%d").date()
        except:
            date1 = datetime.date(2017, 9, 1)
        try:
            date2 = datetime.datetime.strptime(self.ids.end_date.text, "%Y-%m-%d").date()
        except:
            date2 = datetime.date(2018, 9, 1)

        self.persist.set_property("gnucashpath", self.ids.gnucash_file_path.text)
        self.persist.set_property("start_date", self.ids.start_date.text)
        self.persist.set_property("end_date", self.ids.end_date.text)

        auto = AutoRealisatieReport(self.ids.gnucash_file_path.text, date1, date2)

        if not self.ids.accordion_manual.collapse:
            self.persist.set_property("gnucash_accounts", self.ids.gnucash_accounts.text)

            try:
                auto.realisatie_report(accounts)
                report = auto.realisatie_report(accounts)
                self.ids.generated_report.text = report
            except InvalidClientSecretsError as e:
                print(e)
                content = WarningPopup(message=str(e), cancel=self.dismiss_popup)
                self._popup = MessagePopup(title="Error", content=content)
                self._popup.open()
            except Exception as e:
                print("exception ",e)
                content = WarningPopup(message=json.loads(e.content)['error']['message'], cancel=self.dismiss_popup)
                self._popup = MessagePopup(title="Error", content=content)
                self._popup.open()
        elif not self.ids.accordion_auto.collapse:
            self.persist.set_property("spreadsheet_id", self.ids.spreadsheet_id.text)
            self.persist.set_property("realisatie_range_name", self.ids.realisatie_range_name.text)
            self.persist.set_property("balans_range_name_activa", self.ids.balans_range_name_activa.text)
            self.persist.set_property("balans_range_name_passiva", self.ids.balans_range_name_passiva.text)
            try:
                auto.direct_to_sheet(spreadsheet_id=self.ids.spreadsheet_id.text,
                                     range_name=self.ids.realisatie_range_name.text)

                auto.balans_to_sheet(spreadsheet_id=self.ids.spreadsheet_id.text,
                                     range_name_activa=self.ids.balans_range_name_activa.text,
                                     range_name_passiva=self.ids.balans_range_name_passiva.text)
            except InvalidClientSecretsError as e:
                print("InvalidClientSecretsError: ", e)
                content = WarningPopup(message=str(e), cancel=self.dismiss_popup)
                self._popup = MessagePopup(title="Error", content=content)
                self._popup.open()
            except HttpError as e:
                content = WarningPopup(message=json.loads(e.content)['error']['message'], cancel=self.dismiss_popup)
                self._popup = MessagePopup(title="Error", content=content)
                self._popup.open()


class GnucashReportApp(App):
    current_action = ""
    rv_data = []
    printed = False

    def build(self):
        return Manager()

    def on_start(self, **kwargs):
        self.persist = PersistProperties()
        self.root.main_screen.persist = self.persist
        self.root.main_screen.ids.gnucash_file_path.text = self.persist.gnucashpath
        self.root.main_screen.ids.spreadsheet_id.text = self.persist.spreadsheet_id
        self.root.main_screen.ids.realisatie_range_name.text = self.persist.realisatie_range_name
        self.root.main_screen.ids.balans_range_name_activa.text = self.persist.balans_range_name_activa
        self.root.main_screen.ids.balans_range_name_passiva.text = self.persist.balans_range_name_passiva
        self.root.main_screen.ids.start_date.text = self.persist.start_date
        self.root.main_screen.ids.end_date.text = self.persist.end_date
        self.root.main_screen.ids.gnucash_accounts.text = self.persist.gnucash_accounts


class Manager(ScreenManager):
    main_screen = ObjectProperty(None)


if __name__ == '__main__':
    GnucashReportApp().run()
