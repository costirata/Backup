__author__ = 'Constantin'
import unittest
import Backup
import re
import os


class TestBackup(unittest.TestCase):
    def test_get_working_backup_dir(self):
        backup_dir = os.getcwd()
        extra_info = 'extra_data'
        correct_output_pattern = backup_dir+os.path.sep+r"[0-9]*_"+extra_info
        correct_output_pattern = correct_output_pattern.replace('\\', '\\\\')
        result = Backup.get_working_backup_dir(backup_dir, custom_name=extra_info)
        re.match(correct_output_pattern, result)
        success = re.match(correct_output_pattern, result) is not None
        self.assertTrue(success, msg='Ceva sa imbulinat '+result+' regular expr='+correct_output_pattern)

# if __name__ == '__main__':
#     unittest.main()