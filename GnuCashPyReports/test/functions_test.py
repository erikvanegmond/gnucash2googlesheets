import re

from GnuCashPyReports.functions import placeholder_range_name

print(placeholder_range_name("Realisatie!K2:N"))
print(placeholder_range_name("Realisatie!K22:N"))
print(placeholder_range_name("Realisatie!K2:N4"))
print(placeholder_range_name("Realisatie!K2:N42"))
print(placeholder_range_name("Realisatie!AZ2:N"))
print(placeholder_range_name("Realisatie!AZ2:BN22"))
print(placeholder_range_name("K2:N"))
print(placeholder_range_name("K22:N"))
print(placeholder_range_name("K2:N4"))
print(placeholder_range_name("K2:N42"))
print(placeholder_range_name("AZ2:N"))
print(placeholder_range_name("AZ2:BN22"))
