import locale
from collections import defaultdict

from GnuCashPyReports.functions import get_start_row, placeholder_range_name
from GnuCashPyReports.lib import gnucashxml
from GnuCashPyReports.lib.google_sheets import get_sheet_values

locale.setlocale(locale.LC_ALL, "nl")


def walk_book(book_file, date1, date2):
    book = gnucashxml.from_filename(book_file)
    data = {}
    for account, subaccounts, splits in book.walk():
        if account.actype in ["INCOME", "EXPENSE"]:
            account_name = account.fullname().split(":")[-1]
            the_sum = sum(
                split.value for split in account.splits if date1 <= split.transaction.date.date() <= date2)
            if account_name not in data:
                data[account_name] = defaultdict(int)
            data[account_name][account.actype] = the_sum
        elif account.actype in ["ASSET", "BANK"]:
            account_name = account.fullname().split(":")[-1]
            the_sum = sum(split.value for split in account.splits)
            if account_name not in data:
                data[account_name] = defaultdict(int)
            data[account_name][account.actype] = the_sum
    return data


class AutoRealisatieReport:
    def __init__(self, book_file, date1, date2):
        self.data = walk_book(book_file, date1, date2)

    def realisatie_report(self, accounts_long):
        accounts = [a.strip() for a in accounts_long.split("\n")]
        result = ""
        for account in accounts:
            if account in self.data:
                data = self.get_account_report(account)
                result += "{}\t {}\t{}\n".format(account, locale.format("%10.2f", -data[0]),
                                                 locale.format("%10.2f", data[1]))
            else:
                result += "{}\n".format(account)
        return result

    def get_account_report(self, account):
        if account in self.data:
            return [-float(self.data[account]["INCOME"]), float(self.data[account]["EXPENSE"])]
        else:
            return []

    def get_activa_balance(self, account):
        if account in self.data:
            return float(self.data[account]["BANK"]) + float(self.data[account]["ASSET"])

    def direct_to_sheet(self, spreadsheet_id, range_name=""):
        if not range_name:
            return

        values, service = get_sheet_values(spreadsheet_id, range_name)
        data = []

        if not values:
            print('No data found.')
        else:
            data_block = []
            block_start = 0
            k_start = get_start_row(range_name)
            wait_for_header = False
            placeholder_range = placeholder_range_name(range_name)
            for i, row in enumerate(values):
                if row:
                    if row[0].startswith("Subtotaal"):
                        data.append({
                            "range": placeholder_range.format(block_start + k_start, i + k_start - 1),
                            "majorDimension": "ROWS",
                            "values": data_block
                        })
                        data_block = []
                        wait_for_header = True
                        continue
                    if wait_for_header:
                        wait_for_header = False
                        data_block = []
                        block_start = i + 1
                        continue
                    data_block.append([row[0]] + self.get_account_report(row[0]))
                else:
                    data_block.append([])

                if row and row[0] is "Totaal":
                    break

            body = {
                'valueInputOption': 'USER_ENTERED',
                'data': data
            }
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body).execute()

    def balans_to_sheet(self, spreadsheet_id, range_name_activa="", range_name_passiva=""):
        if range_name_activa:
            self.activa_to_sheet(spreadsheet_id, range_name_activa)
        if range_name_passiva:
            self.passiva_to_sheet(spreadsheet_id, range_name_passiva)

    def activa_to_sheet(self, spreadsheet_id, range_name_activa):
        values, service = get_sheet_values(spreadsheet_id, range_name_activa)
        data = []

        if not values:
            print('No data found.')
        else:
            data_block = []
            block_start = 0
            k_start = get_start_row(range_name_activa)
            placeholder_range = placeholder_range_name(range_name_activa)
            for row in values:
                if row and row[0] in self.data:
                    try:
                        last_activia_balance = row[1]
                    except IndexError:
                        last_activia_balance = 0
                    current_activia_balance = self.get_activa_balance(row[0])
                    data_block.append([row[0]] + [last_activia_balance, current_activia_balance])
                else:
                    data_block.append([])
            data.append({
                "range": placeholder_range.format(block_start + k_start, len(values) + k_start - 1),
                "majorDimension": "ROWS",
                "values": data_block
            })

            body = {
                'valueInputOption': 'USER_ENTERED',
                'data': data
            }
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body).execute()

    def passiva_to_sheet(self, spreadsheet_id, range_name_passiva):
        values, service = get_sheet_values(spreadsheet_id, range_name_passiva)
        data = []

        if not values:
            print('No data found.')
        else:
            data_block = []
            block_start = 0
            k_start = get_start_row(range_name_passiva)
            placeholder_range = placeholder_range_name(range_name_passiva)
            for row in values:
                if row and row[0] in self.data:
                    try:
                        last_activia_balance = row[1]
                    except IndexError:
                        last_activia_balance = 0
                    current_activia_balance = -self.get_activa_balance(row[0])
                    data_block.append([row[0]] + [last_activia_balance, current_activia_balance])
                else:
                    data_block.append([])
            data.append({
                "range": placeholder_range.format(block_start + k_start, len(values) + k_start - 1),
                "majorDimension": "ROWS",
                "values": data_block
            })

            body = {
                'valueInputOption': 'USER_ENTERED',
                'data': data
            }
            print(body)
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body).execute()